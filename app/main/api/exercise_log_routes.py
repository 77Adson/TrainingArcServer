import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from app import mongo
from app.services import process_workout_log

exercise_log_bp = Blueprint('exercise_log_bp', __name__)

@exercise_log_bp.route("/log_exercise", methods=["POST"])
@jwt_required()
def log_exercise():
    user_id = get_jwt_identity()
    data = request.json

    exercise_id = data.get("exercise_id")
    session_id = data.get("session_id") # NEW
    log_type = data.get("log_type", "freeweight") 
    raw_data = data.get("raw_data")
    client_date_str = data.get("date") 
    
    if not exercise_id or not raw_data or not session_id:
        return jsonify({"message": "exercise_id, session_id, and raw_data are required"}), 400

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    user_weight = user.get("weight", 0) if user else 0

    # Aggregates calculates based on the FULL array passed from the frontend
    aggregates = process_workout_log(log_type, raw_data, user_weight)

    try:
        if client_date_str:
            log_date = datetime.datetime.fromisoformat(client_date_str.replace('Z', '+00:00'))
        else:
            log_date = datetime.datetime.now(datetime.timezone.utc)
    except ValueError:
        log_date = datetime.datetime.now(datetime.timezone.utc)

    # The data we want to set/update
    update_doc = {
        "date": log_date, 
        "log_type": log_type,
        "is_important_flag": data.get("is_important_flag", False),
        **aggregates,
        **raw_data # Overwrites the raw_sets array with the new full array
    }
    
    # THE UPSERT MAGIC
    mongo.db.exercise_logs.update_one(
        {
            "userId": ObjectId(user_id),
            "exercise_id": ObjectId(exercise_id),
            "session_id": session_id # Group by session and exercise
        },
        {"$set": update_doc},
        upsert=True # If it doesn't exist, create it. If it does, overwrite it.
    )
    
    return jsonify({"message": "Exercise log saved successfully"}), 201