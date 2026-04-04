import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from app import mongo
from app.services import process_workout_log

exercise_log_bp = Blueprint('log_exercise_bp', __name__)

@exercise_log_bp.route("/log_exercise", methods=["POST"])
@jwt_required()
def log_exercise():
    user_id = get_jwt_identity()
    data = request.json

    exercise_id = data.get("exercise_id")
    log_type = data.get("log_type", "freeweight") 
    raw_data = data.get("raw_data")
    client_date_str = data.get("date") # GET THE DATE FROM ANDROID
    
    if not exercise_id or not raw_data:
        return jsonify({"message": "exercise_id and raw_data are required"}), 400

    # Parse the client date, fallback to server time if anything fails
    try:
        if client_date_str:
            # Replace 'Z' with '+00:00' so Python handles the UTC ISO format natively
            log_date = datetime.datetime.fromisoformat(client_date_str.replace('Z', '+00:00'))
        else:
            log_date = datetime.datetime.now(datetime.timezone.utc)
    except ValueError:
        log_date = datetime.datetime.now(datetime.timezone.utc)

    # ... aggregations ...

    new_log_document = {
        "userId": ObjectId(user_id),
        "exercise_id": ObjectId(exercise_id),
        "date": log_date, # USE THE EXACT TIMESTAMP
        "log_type": log_type,
        "is_important_flag": data.get("is_important_flag", False),
        **aggregates,
        **raw_data
    }
    
    mongo.db.exercise_logs.insert_one(new_log_document)
    
    return jsonify({"message": "Exercise log saved successfully"}), 201
    """Zapisuje nowy log treningowy (Smart Aggregation)."""
    user_id = get_jwt_identity()
    data = request.json

    exercise_id = data.get("exercise_id")
    log_type = data.get("log_type") 
    raw_data = data.get("raw_data")
    
    if not exercise_id or not log_type or not raw_data:
        return jsonify({"message": "exercise_id, log_type, and raw_data are required"}), 400

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    user_weight = user.get("weight", 0)

    aggregates = process_workout_log(log_type, raw_data, user_weight)

    new_log_document = {
        "userId": ObjectId(user_id),
        "exercise_id": ObjectId(exercise_id),
        "data": datetime.datetime.now(datetime.timezone.utc),
        "log_type": log_type,
        "is_important_flag": data.get("is_important_flag", False),
        **aggregates,
        **raw_data
    }
    
    mongo.db.workoutLogs.insert_one(new_log_document)
    
    return jsonify({"message": "Workout log saved successfully"}), 201
