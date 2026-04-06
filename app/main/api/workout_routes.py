import datetime
from app.services import calculate_rpg_gains
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from app import mongo

workout_bp = Blueprint('workout_bp', __name__)

@workout_bp.route("/user/workouts", methods=["GET"])
@jwt_required()
def get_user_workouts():
    """Pobiera zdefiniowane plany treningowe użytkownika."""
    user_id = get_jwt_identity()
    workouts = list(mongo.db.workouts.find({"userId": ObjectId(user_id)}))
    output = []

    for w in workouts:
        output.append({
            "_id": str(w["_id"]),
            "name": w.get("name", "Unnamed Plan"),
            "description": w.get("description", ""),
            "exercise_groups": w.get("exercise_groups", []),
            "days_of_week": w.get("days_of_week", {
                "Monday": False, "Tuesday": False, "Wednesday": False, 
                "Thursday": False, "Friday": False, "Saturday": False, "Sunday": False
            }),
            "average_time_sec": w.get("average_time_sec", 0),
            
            # Keep this temporarily just in case old app versions expect it, 
            # though the new app uses exercise_groups exclusively.
            "exercise_ids": [str(eid) for eid in w.get("exercise_ids", [])] 
        })
    return jsonify(output), 200

@workout_bp.route("/user/workouts", methods=["POST"])
@jwt_required()
def create_workout_plan():
    """Tworzy nowy plan treningowy (np. 'Push Day')."""
    user_id = get_jwt_identity()
    data = request.json

    if "name" not in data:
        return jsonify({"message": "Workout plan name is required"}), 400
    
    new_workout = {
        "userId": ObjectId(user_id),
        "name": data["name"],
        "description": "",
        "days_of_week": {"Monday": False, "Tuesday": False, "Wednesday": False, "Thursday": False,
                         "Friday": False, "Saturday": False, "Sunday": False},
        "average_duration": 0,
        "exercise_groups": [],
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    
    result = mongo.db.workouts.insert_one(new_workout)
    
    return jsonify({
        "message": "Workout plan created successfully",
        "workout_id": str(result.inserted_id)
    }), 201

@workout_bp.route("/user/workouts/<workout_id>", methods=["PATCH"])
@jwt_required()
def update_workout_plan(workout_id):
    user_id = get_jwt_identity()
    data = request.json
    
    if not data:
        return jsonify({"message": "No data to update"}), 400

    update_data = {}
    if "name" in data:
        update_data["name"] = data["name"]
    if "description" in data:
        update_data["description"] = data["description"]
    if "days_of_week" in data:
        update_data["days_of_week"] = data["days_of_week"]
    if "exercise_groups" in data:
        update_data["exercise_groups"] = data["exercise_groups"]

    if not update_data:
        return jsonify({"message": "No valid fields provided"}), 400

    result = mongo.db.workouts.update_one(
        {"_id": ObjectId(workout_id), "userId": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        return jsonify({"message": "Workout plan not found or unauthorized"}), 404
        
    return jsonify({"message": "Workout plan updated successfully"}), 200

@workout_bp.route("/user/workouts/<workout_id>/finish", methods=["POST"])
@jwt_required()
def finish_workout(workout_id):
    """Marks the session complete, updates average duration, and processes XP."""
    user_id = get_jwt_identity()
    data = request.json
    duration_sec = data.get("duration_sec", 0)
    session_id = data.get("session_id") # NEW

    workout = mongo.db.workouts.find_one({"_id": ObjectId(workout_id), "userId": ObjectId(user_id)})
    if not workout:
        return jsonify({"message": "Workout not found"}), 404

    # Calculate new moving average
    current_avg = workout.get("average_time_sec", 0)
    sessions_count = workout.get("sessions_completed", 0) # Track how many times it was done

    new_count = sessions_count + 1
    if current_avg == 0:
        new_avg = duration_sec
    else:
        new_avg = int(((current_avg * sessions_count) + duration_sec) / new_count)

    mongo.db.workouts.update_one(
        {"_id": ObjectId(workout_id)},
        {"$set": {
            "average_time_sec": new_avg, 
            "sessions_completed": new_count
        }}
    )

    # RPG Engine Processing
    rpg_results = calculate_rpg_gains(user_id, session_id, duration_sec)

    return jsonify({
        "message": "Workout finished",
        "user_xp_gained": rpg_results.get("user_xp_gained", 0),
        "user_leveled_up": rpg_results.get("user_leveled_up", False),
        "user_new_level": rpg_results.get("user_new_level", 1),
        "exercises_leveled_up": rpg_results.get("exercise_level_ups", []),
        "achievements_unlocked": rpg_results.get("achievements_unlocked", [])
    }), 200
