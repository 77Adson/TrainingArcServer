import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from app.repositories import workout_repo, social_repo

# Correct service imports to avoid NameErrors
from app.services.social_service import clone_workout_blueprint
from app.services.rpg_engine import calculate_rpg_gains
from app.services.workout_processor import extract_workout_blueprint

workout_bp = Blueprint('workout_bp', __name__)

@workout_bp.route("/user/workouts", methods=["GET"])
@jwt_required()
def get_user_workouts():
    """
    Optimized List View: Returns lightweight cards for the 'Workouts' tab.
    Calculates exercise counts server-side to save frontend processing.
    """
    user_id = get_jwt_identity()
    workouts = workout_repo.get_workouts_by_user(
        user_id, 
        projection={"name": 1, "days_of_week": 1, "exercise_groups": 1, "average_time_sec": 1}
    )
    
    output = []
    for w in workouts:
        total_exercises = sum([len(g.get("exercise_ids", [])) for g in w.get("exercise_groups", [])])
        
        output.append({
            "_id": str(w["_id"]),
            "name": w.get("name", "Unnamed Plan"),
            "days_of_week": w.get("days_of_week", {}),
            "total_exercises": total_exercises,
            "average_time_sec": w.get("average_time_sec", 0)
        })
    return jsonify(output), 200

@workout_bp.route("/user/workouts/<workout_id>", methods=["GET"])
@jwt_required()
def get_my_workout_detail(workout_id):
    """
    Full Owner View: Returns the complete blueprint including private notes
    and scheduling data for editing or starting a session.
    """
    user_id = get_jwt_identity()
    w = workout_repo.get_workout_by_id(workout_id, user_id)
    
    if not w:
        return jsonify({"message": "Workout not found"}), 404

    # 1. Use the shared helper for the core blueprint structure
    blueprint = extract_workout_blueprint(w)
    
    # 2. Add owner-only metadata for Management Mode
    blueprint["description"] = w.get("description", "")
    blueprint["days_of_week"] = w.get("days_of_week", {})
    blueprint["sessions_completed"] = w.get("sessions_completed", 0)
    
    return jsonify(blueprint), 200

@workout_bp.route("/friends/workouts/<workout_id>", methods=["GET"])
@jwt_required()
def get_friend_workout_blueprint(workout_id):
    """
    Sanitized Friend View: Only returns the blueprint if a friendship exists.
    Strips out personal notes and schedules.
    """
    my_id = get_jwt_identity()
    w = workout_repo.get_workout_by_id(workout_id)
    
    if not w:
        return jsonify({"message": "Workout not found"}), 404

    owner_id = w["userId"]

    # Verify bidirectional friendship before showing any data
    friendship = social_repo.get_friendship(my_id, str(owner_id))

    if not friendship:
        return jsonify({"message": "You are not rivals with this user"}), 403

    # Return ONLY the sanitized blueprint via the helper
    return jsonify(extract_workout_blueprint(w)), 200

@workout_bp.route("/user/workouts/<workout_id>/clone", methods=["POST"])
@jwt_required()
def clone_workout(workout_id):
    """
    Deep Clone Engine: Recursively copies a friend's blueprint into the
    user's library, resetting RPG stats to Level 1.
    """
    requester_id = get_jwt_identity()
    new_id = clone_workout_blueprint(workout_id, requester_id)
    
    if not new_id:
        return jsonify({"message": "Failed to clone workout"}), 404
        
    return jsonify({
        "message": "Workout and exercises cloned successfully",
        "new_workout_id": new_id
    }), 201

@workout_bp.route("/user/workouts/<workout_id>/finish", methods=["POST"])
@jwt_required()
def finish_workout(workout_id):
    """
    RPG Engine Trigger: Processes session completion and calculates XP gains
    using the dedicated RPG engine service.
    """
    user_id = get_jwt_identity()
    data = request.json
    duration_sec = data.get("duration_sec", 0)
    session_id = data.get("session_id")

    workout = workout_repo.get_workout_by_id(workout_id, user_id)
    if not workout:
        return jsonify({"message": "Workout not found"}), 404

    # Update moving average and completion count
    sessions_count = workout.get("sessions_completed", 0)
    new_count = sessions_count + 1
    current_avg = workout.get("average_time_sec", 0)
    
    new_avg = duration_sec if current_avg == 0 else int(((current_avg * sessions_count) + duration_sec) / new_count)

    workout_repo.update_workout_fields(workout_id, user_id, {
        "average_time_sec": new_avg, 
        "sessions_completed": new_count
    })

    # Process XP, Level Ups, and Achievements
    rpg_results = calculate_rpg_gains(user_id, session_id, duration_sec)
    return jsonify(rpg_results), 200

@workout_bp.route("/user/workouts", methods=["POST"])
@jwt_required()
def create_workout_plan():
    """Initializes a new empty workout blueprint."""
    user_id = get_jwt_identity()
    data = request.json
    if "name" not in data:
        return jsonify({"message": "Workout plan name is required"}), 400
    
    new_workout = {
        "userId": ObjectId(user_id),
        "name": data["name"],
        "description": "",
        "days_of_week": {day: False for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
        "average_time_sec": 0,
        "sessions_completed": 0,
        "exercise_groups": [],
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    workout_id_str = workout_repo.create_workout(new_workout)
    return jsonify({"message": "Workout plan created", "workout_id": str(workout_id_str.inserted_id)}), 201

@workout_bp.route("/user/workouts/<workout_id>", methods=["PATCH"])
@jwt_required()
def update_workout_plan(workout_id):
    """Updates blueprint configuration fields."""
    user_id = get_jwt_identity()
    data = request.json
    update_data = {k: v for k, v in data.items() if k in ["name", "description", "days_of_week", "exercise_groups"]}
    
    if not update_data:
        return jsonify({"message": "No valid fields provided"}), 400

    workout_repo.update_workout_fields(workout_id, user_id, update_data)
    
    return jsonify({"message": "Workout updated"}), 200

@workout_bp.route("/user/workouts/<workout_id>", methods=["DELETE"])
@jwt_required()
def delete_workout_plan(workout_id):
    user_id = get_jwt_identity()
    result = workout_repo.delete_workout(workout_id, user_id)
    
    if result.deleted_count == 0:
        return jsonify({"message": "Workout not found or unauthorized"}), 404
        
    return jsonify({"message": "Workout deleted successfully"}), 200