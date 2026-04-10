import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.repositories import log_repo, user_repo
from app.services import process_workout_log

exercise_log_bp = Blueprint('exercise_log_bp', __name__)

@exercise_log_bp.route("/log_exercise", methods=["POST"])
@jwt_required()
def log_exercise():
    user_id = get_jwt_identity()
    data = request.json

    exercise_id = data.get("exercise_id")
    session_id = data.get("session_id") # NEW
    log_type = data.get("log_type", "compound") # NEW: "compound", "isolation", "bodyweight", "cardio"
    raw_data = data.get("raw_data")
    client_date_str = data.get("date") 
    
    if not exercise_id or not raw_data or not session_id:
        return jsonify({"message": "exercise_id, session_id, and raw_data are required"}), 400

    user = user_repo.get_user_by_id(user_id)
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
    log_repo.upsert_exercise_log(user_id, exercise_id, session_id, update_doc)
    
    return jsonify({"message": "Exercise log saved successfully"}), 201

@exercise_log_bp.route("/user/exercises/<exercise_id>/stats", methods=["GET"])
@jwt_required()
def get_exercise_stats(exercise_id):
    """
    Pobiera historię logów dla danego ćwiczenia, agregując dane dziennie.
    Zwraca płaską listę punktów gotowych do narysowania na wykresie.
    """
    user_id = get_jwt_identity()
    
    # Pobierz wszystkie logi dla tego ćwiczenia posortowane chronologicznie
    logs = log_repo.get_logs_for_exercise(user_id, exercise_id)

    stats_by_date = {}

    for log in logs:
        if "date" not in log:
            continue
            
        date_str = log["date"].strftime("%Y-%m-%d")
        
        vol = log.get("aggr_total_volume", 0)
        e1rm = log.get("aggr_best_e1RM", 0)
        
        # Bezpieczne pobranie najwyższego ciężaru
        raw_sets = log.get("raw_sets", [])
        max_weight = max([s.get("weight", 0) for s in raw_sets] + [0])

        if date_str not in stats_by_date:
            stats_by_date[date_str] = {
                "volume": vol,
                "e1rm": e1rm,
                "max_weight": max_weight,
                "average_rest_sec": log.get("aggr_average_rest_sec", 0),
                "distance_km": log.get("aggr_total_distance_km", 0),
                "time_sec": log.get("aggr_total_time_sec", 0) 
            }
        else:
            stats_by_date[date_str]["volume"] += vol
            stats_by_date[date_str]["e1rm"] = max(stats_by_date[date_str]["e1rm"], e1rm)
            stats_by_date[date_str]["max_weight"] = max(stats_by_date[date_str]["max_weight"], max_weight)
            stats_by_date[date_str]["average_rest_sec"] = log.get("aggr_average_rest_sec", 0)
            stats_by_date[date_str]["distance_km"] += log.get("aggr_total_distance_km", 0)
            stats_by_date[date_str]["time_sec"] += log.get("aggr_total_time_sec", 0)

    output = []
    for date_key, values in stats_by_date.items():
        output.append({
            "date": date_key,
            "volume": values["volume"],
            "e1rm": values["e1rm"],
            "max_weight": values["max_weight"],
            "average_rest_sec": values["average_rest_sec"],
            "distance_km": values["distance_km"],
            "time_sec": values["time_sec"]
        })

    return jsonify(output), 200