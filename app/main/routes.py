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
    """Pobiera dane JEDNEGO, zalogowanego użytkownika (nie wszystkich)."""
    try:
        user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        user['_id'] = str(user['_id'])
        user.pop('hashed_password', None) 
        
        return jsonify(user)
    except Exception as e:
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

@main_bp.route("/user/exercises", metheods=["POST"])
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
    
    return jsonify({"message": "Exercise created successfully"}), 201

@main_bp.route("/user/exercises/<exercise_id>", methods=["PATCH"])
@jwt_required()
def update_exercise(exercise_id):
    """Aktualizuje dane ćwiczenia."""
    user_id = get_jwt_identity()
    data = request.json

    # Buduje słownik aktualizacji tylko z podanych pól
    update_data = {}
    if "name" in data:
        update_data["name"] = data["name"]
    if "main_type" in data:
        update_data["main_type"] = data["main_type"]
    if "tags" in data:
        update_data["tags"] = data["tags"]
    if "goal" in data:
        update_data["goal"] = data["goal"]
    if "weight" in data:
        update_data["weight"] = data["weight"]
    if "current_tempo_stats" in data:
        update_data["current_tempo_stats"] = data["current_tempo_stats"]
    if "technique_rating" in data:
        update_data["technique_rating"] = data["technique_rating"]
    if "notes" in data:
        update_data["notes"] = data["notes"]
    if "links" in data:
        update_data["links"] = data["links"]
    if "image_paths" in data:
        update_data["image_paths"] = data["image_paths"]

    if not update_data:
        return jsonify({"message": "No fields to update"}), 400

    # Aktualizuje dane w bazie danych
    mongo.db.exercises.update_one(
        {"_id": ObjectId(exercise_id), "userId": ObjectId(user_id)},
        {"$set": update_data}
    )

    return jsonify({"message": "Exercise updated successfully"}), 200

@main_bp.route("/user/workouts", methods=["GET"])
@jwt_required()
def get_user_workouts():
    """Pobiera wszystkie workouty użytkownika."""
    user_id = get_jwt_identity()
    workouts = list(mongo.db.workouts.find({"userId": ObjectId(user_id)}))

    for s in workouts:
        s["_id"] = str(s["_id"])
        s["userId"] = str(s["userId"])

    return jsonify(workouts), 200

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
    
    stats = mongo.db.workoutLogs.find(
        {
            "userId": ObjectId(user_id),
            "exercise_id": ObjectId(exercise_id)
        },
        {
            "_id": 0, "data": 1, "aggr_total_volume": 1, "aggr_best_e1RM": 1,
            "aggr_total_distance_km": 1, "aggr_total_time_sec": 1
        }
    ).sort("data", 1)
    
    return jsonify(dumps(list(stats))), 200