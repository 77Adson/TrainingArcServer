import datetime
from app import mongo
from bson.objectid import ObjectId

def calculate_e1rm(weight, reps):
    """Oblicza szacowany 1 Rep Max (e1RM) używając formuły Epley'a."""
    if reps == 0:
        return 0
    if reps == 1:
        return weight
    return weight * (1 + (reps / 30))

def calculate_average_rest(raw_sets):
    """Oblicza średni czas odpoczynku (w sekundach) pomiędzy seriami."""
    if len(raw_sets) < 2:
        return 0
        
    total_rest_sec = 0
    rest_count = 0
    
    for i in range(1, len(raw_sets)):
        try:
            # .replace("Z", "+00:00") handles standard JS/Kotlin ISO strings in Python
            time_prev_str = raw_sets[i-1].get("completed_at", "").replace("Z", "+00:00")
            time_curr_str = raw_sets[i].get("completed_at", "").replace("Z", "+00:00")
            
            if not time_prev_str or not time_curr_str:
                continue
                
            time_prev = datetime.datetime.fromisoformat(time_prev_str)
            time_curr = datetime.datetime.fromisoformat(time_curr_str)
            
            delta = (time_curr - time_prev).total_seconds()
            
            # Prevent negative rest times if client sends weird data
            if delta > 0:
                total_rest_sec += delta
                rest_count += 1
        except ValueError:
            # Ignore malformed timestamps without crashing the whole request
            continue
            
    if rest_count == 0:
        return 0
        
    return int(total_rest_sec / rest_count)

def calculate_strength_metrics(raw_sets, body_weight_offset=0):
    """
    Oblicza objętość i najlepsze e1RM. 
    Dla freeweight: body_weight_offset = 0.
    Dla bodyweight: body_weight_offset = user_weight_kg.
    """
    total_volume = 0
    best_e1rm = 0

    for s in raw_sets:
        reps = s.get("reps", 0)
        # Total weight = any added weight (e.g. +20kg pullup) + body weight offset
        total_weight = s.get("weight", 0) + body_weight_offset
        
        total_volume += reps * total_weight
        e1rm = calculate_e1rm(total_weight, reps)
        
        if e1rm > best_e1rm:
            best_e1rm = e1rm
            
    return total_volume, round(best_e1rm, 2)

def process_workout_log(log_type, raw_data, user_weight_kg):
    """
    Przetwarza surowe dane w celu obliczenia agregatów
    zgodnie ze schematem "Smart Aggregation".
    """
    aggregates = {
        "aggr_total_volume": 0,
        "aggr_best_e1RM": 0,
        "aggr_total_distance_km": 0,
        "aggr_total_time_sec": 0,
        "aggr_average_rest_sec": 0
    }
    
    raw_sets = raw_data.get("raw_sets", [])

    # Calculate rest time for any set-based workout
    if log_type in ["compound", "isolation", "bodyweight"]:
        aggregates["aggr_average_rest_sec"] = calculate_average_rest(raw_sets)

    # Route to the appropriate logic
    if log_type in ["compound", "isolation"]:
        vol, e1rm = calculate_strength_metrics(raw_sets, body_weight_offset=0)
        aggregates["aggr_total_volume"] = vol
        aggregates["aggr_best_e1RM"] = e1rm

    elif log_type == "bodyweight":
        vol, e1rm = calculate_strength_metrics(raw_sets, body_weight_offset=user_weight_kg)
        aggregates["aggr_total_volume"] = vol
        aggregates["aggr_best_e1RM"] = e1rm

    elif log_type == "running":
        # For 'running' raw_data is an object, not an array
        aggregates["aggr_total_distance_km"] = raw_data.get("distance_km", 0)
        aggregates["aggr_total_time_sec"] = raw_data.get("time_sec", 0)
        
    return aggregates


def calculate_rpg_gains(user_id_str, session_id, duration_sec):
    """
    Evaluates a finished session, calculates XP based on technique and duration, 
    routes stat points, and processes level-ups.
    """
    user = mongo.db.users.find_one({"_id": ObjectId(user_id_str)})
    if not user: return {}

    # Fetch all logs tied to this specific workout session
    session_logs = list(mongo.db.exercise_logs.find({"session_id": session_id}))

    total_xp_gained = 0
    stats_gained = {"strength": 0, "stamina": 0, "dexterity": 0, "endurance": 0}

    # 1. Base XP: Time spent (e.g., 2 XP per minute)
    base_xp = int((duration_sec / 60) * 2)
    total_xp_gained += base_xp

    for log in session_logs:
        log_type = log.get("log_type", "compound")
        raw_sets = log.get("raw_sets", [])
        
        # 2. Technique Multiplier (Average stars for the exercise)
        technique_ratings = [s.get("technique_rating", 3) for s in raw_sets if s.get("technique_rating")]
        avg_technique = sum(technique_ratings) / len(technique_ratings) if technique_ratings else 3.0
        
        # Map 1-5 stars to a 0.5x to 1.5x multiplier
        technique_multiplier = 0.5 + ((avg_technique - 1) * 0.25)

        # 3. Exercise XP
        # Placeholder for Delta/Momentum math: currently flat 25 XP modified by technique
        exercise_xp = int(25 * technique_multiplier)
        total_xp_gained += exercise_xp

        # 4. Route to User Stats based on Exercise Type
        stat_gain = int(1 * technique_multiplier)
        if log_type == "compound":
            stats_gained["strength"] += stat_gain
        elif log_type == "isolation":
            stats_gained["stamina"] += stat_gain
        elif log_type == "bodyweight":
            stats_gained["dexterity"] += stat_gain
        elif log_type == "running":
            stats_gained["endurance"] += stat_gain

    # 5. Process Leveling Up (1000 XP per level linear curve)
    current_level = user.get("level", 1)
    current_xp = user.get("total_xp", 0) + total_xp_gained
    leveled_up = False
    
    xp_required = current_level * 1000
    while current_xp >= xp_required:
        current_level += 1
        current_xp -= xp_required
        leveled_up = True
        xp_required = current_level * 1000

    # 6. Apply to Database
    user_stats = user.get("stats", {"strength": 10, "stamina": 10, "dexterity": 10, "endurance": 10, "consistency": 10})
    for key in stats_gained:
        user_stats[key] = user_stats.get(key, 10) + stats_gained[key]

    mongo.db.users.update_one(
        {"_id": ObjectId(user_id_str)},
        {"$set": {
            "level": current_level,
            "total_xp": current_xp,
            "stats": user_stats
        }}
    )

    return {
        "xp_gained": total_xp_gained,
        "leveled_up": leveled_up,
        "new_level": current_level
    }