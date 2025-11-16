import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from bson.json_util import dumps
from __init__ import mongo
from app.services import process_workout_log

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def home():
    return jsonify({
        'message': 'Training Arc API',
        'endpoints': [
            '/register',
            '/login',
            '/users',
            '/exercises',
            '/sessions',
            '/log_workout',
            '/stats/<exercise_id>'
        ]
    })

@main_bp.route('/users')
@jwt_required()
def get_users():
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

@main_bp.route("/exercises", methods=["GET"])
@jwt_required()
def get_exercises():
    """Pobiera wszystkie ćwiczenia dla zalogowanego użytkownika."""
    user_id = get_jwt_identity()
    exercises = mongo.db.exercises.find({"userId": ObjectId(user_id)})
    return jsonify(dumps(list(exercises))), 200

@main_bp.route("/exercises", methods=["POST"])
@jwt_required()
def add_exercise():
    """Dodaje nowe ćwiczenie dla zalogowanego użytkownika."""
    user_id = get_jwt_identity()
    data = request.json
    
    mongo.db.exercises.insert_one({
        "userId": ObjectId(user_id),
        "nazwa": data.get("nazwa"),
        "typ_glowny": data.get("typ_glowny"),
        "tagi": data.get("tagi", []),
        "cel": data.get("cel"),
        "aktualna_waga_kg": data.get("aktualna_waga_kg"),
        "aktualne_tempo_stats": data.get("aktualne_tempo_stats"),
        "technika_rating": data.get("technika_rating"),
        "notatki": data.get("notatki"),
        "linki": data.get("linki", []),
        "zdjecia_paths": data.get("zdjecia_paths", [])
    })
    
    return jsonify({"message": "Exercise added successfully"}), 201

@main_bp.route("/sessions", methods=["GET"])
@jwt_required()
def get_sessions():
    """Pobiera wszystkie sesje (szablony) dla zalogowanego użytkownika."""
    user_id = get_jwt_identity()
    sessions = mongo.db.sessions.find({"userId": ObjectId(user_id)})
    return jsonify(dumps(list(sessions))), 200

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
    user_weight_kg = user.get("aktualna_waga_kg", 0)

    aggregates = process_workout_log(log_type, raw_data, user_weight_kg)

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