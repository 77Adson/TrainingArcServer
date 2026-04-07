import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from app import mongo
from app.services.dashboard_service import build_weekly_schedule, calculate_streak_and_progress, get_recent_achievements

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/user/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Aggregates all data required for the Home Screen Dashboard."""
    try:
        user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # 1. Schedule
        schedule, target_days = build_weekly_schedule(mongo, user_id)

        # 2. Stats & Streak
        stats = calculate_streak_and_progress(mongo, user_id, target_days)

        # 3. Recent Achievements
        recent_achievements = get_recent_achievements(mongo, user)

        # 4. Today's Workout
        today_name = datetime.datetime.now(datetime.timezone.utc).strftime("%A")
        today_workout = schedule.get(today_name)

        return jsonify({
            "user": {
                "username": user.get("username", "Athlete"),
                "level": user.get("level", 1),
                "total_xp": user.get("total_xp", 0)
            },
            "schedule": schedule,
            "today_workout": today_workout,
            "stats": stats,
            "recent_achievements": recent_achievements
        }), 200

    except Exception as e:
        print(f"Error in get_dashboard: {e}")
        return jsonify({'error': str(e)}), 500