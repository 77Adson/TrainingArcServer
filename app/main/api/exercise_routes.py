from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.repositories import exercise_repo
from bson.objectid import ObjectId

exercise_bp = Blueprint('exercise_bp', __name__)

@exercise_bp.route("/user/exercises", methods=["GET"])
@jwt_required()
def get_exercises():
    user_id = get_jwt_identity()
    exercises = exercise_repo.get_exercises_by_user(user_id)

    for ex in exercises:
        ex["_id"] = str(ex["_id"])
        ex["userId"] = str(ex["userId"])

    return jsonify(exercises), 200

@exercise_bp.route("/user/exercises", methods=["POST"])
@jwt_required()
def create_exercise():
    user_id = get_jwt_identity()
    data = request.json

    if "name" not in data:
        return jsonify({"message": "Exercise name is required"}), 400
    
    new_exercise = {
        "userId": ObjectId(user_id),
        "name": data["name"],
        "main_type": None,
        "tags": [],
        "goal": None,
        "weight": None,
        "current_tempo_stats": None,
        "technique_rating": None,
        "notes": None,
        "links": [],
        "image_paths": [],
        "mastery_level": 1,
        "stats": {
            "mastery": {"level": 1, "xp": 0},
            "strength": {"level": 1, "xp": 0},
            "stamina": {"level": 1, "xp": 0},
            "momentum": {"level": 1, "xp": 0}
        }
    }
    
    res = exercise_repo.create_exercise(new_exercise)
    
    return jsonify({
        "message": "Exercise created successfully",
        "exercise_id": str(res.inserted_id)
    }), 201

@exercise_bp.route("/user/exercises/<exercise_id>", methods=["GET"])
@jwt_required()
def get_exercise_details(exercise_id):
    user_id = get_jwt_identity()
    exercise = exercise_repo.get_exercise_by_id(exercise_id, user_id)
    
    if not exercise:
        return jsonify({"message": "Exercise not found"}), 404
        
    exercise["_id"] = str(exercise["_id"])
    exercise["userId"] = str(exercise["userId"])
    
    defaults = {
            "main_type": "Unspecified", 
            "notes": "", 
            "tags": [], 
            "goal": "",
            "links": [],
            "image_paths": []
        }
    for key, value in defaults.items():
        if key not in exercise or exercise[key] is None:
            exercise[key] = value

    return jsonify(exercise), 200

@exercise_bp.route("/user/exercises/<exercise_id>", methods=["PATCH"])
@jwt_required()
def update_exercise(exercise_id):
    user_id = get_jwt_identity()
    data = request.json
    
    allowed_fields = [
        "name", "main_type", "tags", "goal", "weight", 
        "current_tempo_stats", "technique_rating", "notes", 
        "links", "image_paths", "progression_mode" 
    ]
    
    update_data = {f: data[f] for f in allowed_fields if f in data}
            
    if not update_data:
        return jsonify({"message": "No valid fields provided"}), 400

    result = exercise_repo.update_exercise(exercise_id, user_id, update_data)
    
    if result.matched_count == 0:
        return jsonify({"message": "Exercise not found or unauthorized"}), 404
        
    return jsonify({"message": "Exercise updated successfully"}), 200

@exercise_bp.route("/user/exercises/<exercise_id>", methods=["DELETE"])
@jwt_required()
def delete_exercise(exercise_id):
    user_id = get_jwt_identity()
    result = exercise_repo.delete_exercise(exercise_id, user_id)
    
    if result.deleted_count == 0:
        return jsonify({"message": "Exercise not found or unauthorized"}), 404
        
    return jsonify({"message": "Exercise deleted successfully"}), 200