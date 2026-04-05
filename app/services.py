import datetime

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
    if log_type in ["freeweight", "bodyweight"]:
        aggregates["aggr_average_rest_sec"] = calculate_average_rest(raw_sets)

    # Route to the appropriate logic
    if log_type == "freeweight":
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