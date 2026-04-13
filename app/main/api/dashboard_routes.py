from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.repositories import user_repo
from app.services.dashboard_service import build_weekly_schedule, calculate_streak_and_progress, get_recent_achievements
import datetime

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/user/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_jwt_identity()
        user = user_repo.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        schedule, target_days = build_weekly_schedule(user_id)
        stats = calculate_streak_and_progress(user_id, target_days, schedule)
        recent_achievements = get_recent_achievements(user)

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