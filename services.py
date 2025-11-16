def calculate_e1rm(weight, reps):
    """Oblicza szacowany 1 Rep Max (e1RM) używając formuły Epley'a."""
    if reps == 0:
        return 0
    if reps == 1:
        return weight
    return weight * (1 + (reps / 30))

def process_workout_log(log_type, raw_data, user_weight_kg):
    """
    Przetwarza surowe dane w celu obliczenia agregatów
    zgodnie ze schematem "Smart Aggregation".
    """
    aggregates = {
        "aggr_total_volume": 0,
        "aggr_best_e1RM": 0,
        "aggr_total_distance_km": 0,
        "aggr_total_time_sec": 0
    }
    
    raw_sets = raw_data.get("raw_sets", [])

    if log_type == "freeweight":
        total_volume = 0
        best_e1rm = 0
        for s in raw_sets:
            reps = s.get("reps", 0)
            weight = s.get("weight", 0)
            
            total_volume += reps * weight
            e1rm = calculate_e1rm(weight, reps)
            if e1rm > best_e1rm:
                best_e1rm = e1rm
                
        aggregates["aggr_total_volume"] = total_volume
        aggregates["aggr_best_e1RM"] = round(best_e1rm, 2)

    elif log_type == "bodyweight":
        total_volume = 0
        best_e1rm = 0
        # Używamy wagi użytkownika, jeśli waga nie jest podana w secie
        base_weight = user_weight_kg 
        
        for s in raw_sets:
            reps = s.get("reps", 0)
            # Pozwalamy na dodanie wagi (np. podciąganie z obciążeniem)
            weight = s.get("weight", 0) + base_weight 
            
            total_volume += reps * weight
            e1rm = calculate_e1rm(weight, reps)
            if e1rm > best_e1rm:
                best_e1rm = e1rm

        aggregates["aggr_total_volume"] = total_volume
        aggregates["aggr_best_e1RM"] = round(best_e1rm, 2)

    elif log_type == "running":
        # Dla 'running' raw_data to obiekt, nie tablica
        aggregates["aggr_total_distance_km"] = raw_data.get("distance_km", 0)
        aggregates["aggr_total_time_sec"] = raw_data.get("time_sec", 0)
        
    return aggregates