import datetime
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
        # Safely convert data for the client
        output.append({
            "_id": str(w["_id"]),
            "name": w.get("name", "Unnamed Plan"),
            "description": w.get("description", ""),
            # Convert list of ObjectIds to strings if they exist
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
        "exercise_ids": [], 
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "description": ""
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
    if "exercise_ids" in data:
        try:
            update_data["exercise_ids"] = [ObjectId(eid) for eid in data["exercise_ids"]]
        except Exception:
             return jsonify({"message": "Invalid exercise ID format"}), 400

    if not update_data:
        return jsonify({"message": "No valid fields provided"}), 400

    result = mongo.db.workouts.update_one(
        {"_id": ObjectId(workout_id), "userId": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        return jsonify({"message": "Workout plan not found or unauthorized"}), 404
        
    return jsonify({"message": "Workout plan updated successfully"}), 200
