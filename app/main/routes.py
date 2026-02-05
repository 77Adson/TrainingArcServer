import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from bson.json_util import dumps
from app import mongo
from app.services import process_workout_log

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def home():
    return jsonify({
        'message': 'Training Arc API',
        'endpoints': [
            '/register',
            '/login',
            '/user',
            '/user/exercises',
            '/user/workouts',
            '/log_workout',
            '/stats/<exercise_id>'
        ]
    })

@main_bp.route('/user', methods=['GET'])
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

@main_bp.route("/user", methods=["PATCH"])
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

@main_bp.route("/user/exercises", methods=["GET"])
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

@main_bp.route("/user/exercises", methods=["POST"])
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
        "image_paths": []
    }
    
    mongo.db.exercises.insert_one(new_exercise)
    
    return jsonify({
        "message": "Exercise created successfully",
        "exercise_id": str(new_exercise["_id"])
                    }), 201

@main_bp.route("/user/exercises/<exercise_id>", methods=["PATCH"])
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

@main_bp.route("/user/workouts", methods=["GET"])
@jwt_required()
def get_user_workouts():
    """Pobiera zdefiniowane plany treningowe użytkownika."""
    user_id = get_jwt_identity()
    # Fetch from the 'workouts' collection (Routines), NOT 'workoutLogs' (History)
    workouts = list(mongo.db.workouts.find({"userId": ObjectId(user_id)}))

    output = []
    for w in workouts:
        # Safely convert data for the client
        plan = {
            "_id": str(w["_id"]),
            "name": w.get("name", "Unnamed Plan"),
            # Convert list of ObjectIds to strings if they exist
            "exercise_ids": [str(eid) for eid in w.get("exercise_ids", [])]
        }
        output.append(plan)

    return jsonify(output), 200

@main_bp.route("/user/workouts", methods=["POST"])
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

@main_bp.route("/user/workouts/<workout_id>", methods=["PATCH"])
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

@main_bp.route("/log_workout", methods=["POST"])
@jwt_required()
def log_workout():
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

@main_bp.route("/stats/<exercise_id>", methods=["GET"])
@jwt_required()
def get_stats(exercise_id):
    """Pobiera dane do wykresów (tylko agregaty)."""
    user_id = get_jwt_identity()
    
    # Fetch the data as a standard list
    # Note: "_id": 0 is already in your projection, so we don't need to convert ObjectId!
    logs = list(mongo.db.workoutLogs.find(
        {
            "userId": ObjectId(user_id),
            "exercise_id": ObjectId(exercise_id)
        },
        {
            "_id": 0, 
            "data": 1, 
            "aggr_total_volume": 1, 
            "aggr_best_e1RM": 1,
            "aggr_total_distance_km": 1, 
            "aggr_total_time_sec": 1
        }
    ).sort("data", 1))
    
    # Manual serialization for DateTime objects
    for log in logs:
        if "data" in log and log["data"]:
            # Convert datetime to ISO 8601 string (e.g., "2023-10-27T10:00:00")
            log["data"] = log["data"].isoformat()

    # Pass the raw list to jsonify, which will create a proper JSON Array
    return jsonify(logs), 200