from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from app import mongo

exercise_bp = Blueprint('exercise_bp', __name__)

@exercise_bp.route("/user/exercises", methods=["GET"])
@jwt_required()
def get_exercises():
    """Pobiera wszystkie ćwiczenia dla zalogowanego użytkownika."""
    user_id = get_jwt_identity()
    exercises = list(mongo.db.exercises.find({"userId": ObjectId(user_id)}))

    # Konwertuje ObjectId na stringi dla każdego ćwiczenia
    for ex in exercises:
        ex["_id"] = str(ex["_id"])
        ex["userId"] = str(ex["userId"])

    return jsonify(exercises), 200

@exercise_bp.route("/user/exercises", methods=["POST"])
@jwt_required()
def create_exercise():
    """Tworzy nowe ćwiczenie. Tylko nazwa jest wymagana."""
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
        
        # --- SPRINT 3: RPG EXERCISE STATS ---
        "mastery_level": 1,
        "exercise_stats": {
            "strength": 0.0,
            "stamina": 0.0,
            "momentum": 0.0
        }
    }
    
    mongo.db.exercises.insert_one(new_exercise)
    
    return jsonify({
        "message": "Exercise created successfully",
        "exercise_id": str(new_exercise["_id"])
    }), 201

@exercise_bp.route("/user/exercises/<exercise_id>", methods=["GET"])
@jwt_required()
def get_exercise_details(exercise_id):
    user_id = get_jwt_identity()
    
    # Fetch the exercise document
    exercise = mongo.db.exercises.find_one({
        "_id": ObjectId(exercise_id), 
        "userId": ObjectId(user_id)
    })
    
    if not exercise:
        return jsonify({"message": "Exercise not found"}), 404
        
    # Serialize ObjectId
    exercise["_id"] = str(exercise["_id"])
    exercise["userId"] = str(exercise["userId"])
    
    # Ensure all fields exist for the frontend
    defaults = {
        "main_type": "Unspecified",
        "notes": "",
        "tags": [],
        "goal": ""
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
    
    if not data:
        return jsonify({"message": "No data to update"}), 400

    # --- ADDED 'progression_mode' TO WHITELIST ---
    allowed_fields = [
        "name", "main_type", "tags", "goal", "weight", 
        "current_tempo_stats", "technique_rating", "notes", 
        "links", "image_paths", "progression_mode" 
    ]
    
    update_data = {}
    for field in allowed_fields:
        if field in data:
            update_data[field] = data[field]
            
    if not update_data:
        return jsonify({"message": "No valid fields provided"}), 400

    result = mongo.db.exercises.update_one(
        {"_id": ObjectId(exercise_id), "userId": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        return jsonify({"message": "Exercise not found or unauthorized"}), 404
        
    return jsonify({"message": "Exercise updated successfully"}), 200
