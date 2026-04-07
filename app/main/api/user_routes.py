from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from app import mongo
import datetime

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    """Pobiera dane JEDNEGO, zalogowanego użytkownika."""
    try:
        user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # 1. Convert ObjectId to string
        user['_id'] = str(user['_id'])
        
        # 2. Remove sensitive data
        user.pop('hashed_password', None)
        
        # 3. SAFETY FIX: Convert datetime to string manually
        if 'created_at' in user:
            user['created_at'] = user['created_at'].isoformat()
        
        return jsonify(user)
    except Exception as e:
        # This print helps you see the REAL error in your server console
        print(f"Error in get_user: {e}") 
        return jsonify({'error': str(e)}), 500

@user_bp.route("/user", methods=["PATCH"])
@jwt_required()
def update_user():
    """Ustawia preferencje użytkownika."""
    user_id = get_jwt_identity()
    data = request.json

    # Buduje słownik aktualizacji tylko z podanych pól
    update_data = {}
    if "username" in data:
        update_data["username"] = data["username"]
    if "weight" in data:
        update_data["weight"] = data["weight"]
    if "preferences" in data:
        update_data["preferences"] = data["preferences"]

    if not update_data:
        return jsonify({"message": "No data to update"}), 400

    # Aktualizuje dane w bazie danych
    mongo.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    
    return jsonify({"message": "User updated successfully"}), 200


@user_bp.route('/achievements', methods=['GET'])
@jwt_required()
def get_all_achievements():
    """Zwraca główną listę wszystkich dostępnych osiągnięć w grze z bazy danych."""
    achievements_cursor = mongo.db.achievements.find()
    
    achievements_list = []
    for ach in achievements_cursor:
        achievements_list.append({
            "id": ach["_id"],
            "name": ach["name"],
            "description": ach["description"]
        })
        
    return jsonify(achievements_list), 200

@user_bp.route('/user/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Aggregates all data required for the Home Screen Dashboard."""
    try:
        user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # 1. Fetch User's Workouts to build the Schedule
        workouts = list(mongo.db.workouts.find({"userId": ObjectId(user_id)}))
        
        # Build 7-day schedule mapping
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        schedule = {day: None for day in days_of_week}
        
        for w in workouts:
            days = w.get("days_of_week", {})
            for day, is_active in days.items():
                if is_active and not schedule[day]:
                    # Map the first active workout found for that day
                    total_exercises = sum([len(g.get("exercise_ids", [])) for g in w.get("exercise_groups", [])])
                    schedule[day] = {
                        "_id": str(w["_id"]),
                        "name": w.get("name", "Unnamed Workout"),
                        "description": w.get("description", ""),
                        "average_time_sec": w.get("average_time_sec", 0),
                        "total_exercises": total_exercises
                    }

        unique_scheduled_days = sum(1 for day, w in schedule.items() if w is not None)

        # 2. Calculate Streak and "This Week" Progress
        today = datetime.datetime.now(datetime.timezone.utc).date()
        start_of_week = today - datetime.timedelta(days=today.weekday()) # Monday

        # Fetch dates of all logged workouts for this user
        logs = list(mongo.db.exercise_logs.find({"userId": ObjectId(user_id)}, {"date": 1}))
        workout_dates = sorted(list(set([log["date"].date() for log in logs if "date" in log])), reverse=True)

        streak = 0
        check_date = today
        
        # If they worked out today or yesterday, the streak is alive
        if workout_dates and (workout_dates[0] == today or workout_dates[0] == today - datetime.timedelta(days=1)):
            idx = 0
            # If the first log is yesterday, start checking from yesterday
            if workout_dates[0] == today - datetime.timedelta(days=1):
                check_date = today - datetime.timedelta(days=1)
                
            while idx < len(workout_dates) and workout_dates[idx] == check_date:
                streak += 1
                check_date -= datetime.timedelta(days=1)
                idx += 1

        workouts_this_week = sum(1 for d in workout_dates if d >= start_of_week)

        # 3. Recent Achievements (Last 3)
        recent_ach_ids = user.get("achievements", [])[-3:]
        recent_achievements = []
        if recent_ach_ids:
            ach_docs = list(mongo.db.achievements.find({"_id": {"$in": recent_ach_ids}}))
            ach_map = {doc["_id"]: doc for doc in ach_docs}
            
            # Reverse to show newest first
            for ach_id in reversed(recent_ach_ids):
                if ach_id in ach_map:
                    recent_achievements.append({
                        "id": ach_map[ach_id]["_id"],
                        "name": ach_map[ach_id]["name"],
                        "description": ach_map[ach_id]["description"]
                    })

        # 4. Today's Workout
        today_name = today.strftime("%A")
        today_workout = schedule.get(today_name)

        return jsonify({
            "user": {
                "username": user.get("username", "Athlete"),
                "level": user.get("level", 1),
                "total_xp": user.get("total_xp", 0)
            },
            "schedule": schedule,
            "today_workout": today_workout,
            "stats": {
                "streak": streak,
                "this_week_completed": workouts_this_week,
                "this_week_target": unique_scheduled_days if unique_scheduled_days > 0 else 1
            },
            "recent_achievements": recent_achievements
        }), 200

    except Exception as e:
        print(f"Error in get_dashboard: {e}")
        return jsonify({'error': str(e)}), 500