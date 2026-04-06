def get_technique_multiplier(raw_sets):
    """Converts 1-5 star ratings into a 0.5x to 1.5x multiplier."""
    ratings = [s.get("technique_rating", 3) for s in raw_sets if s.get("technique_rating")]
    avg_technique = sum(ratings) / len(ratings) if ratings else 3.0
    return 0.5 + ((avg_technique - 1) * 0.25)

def get_primary_metric(log, log_type):
    """Determines the main metric for momentum based on exercise type."""
    if log_type == "compound":
        return log.get("aggr_best_e1RM", 0)
    elif log_type in ["isolation", "bodyweight"]:
        return log.get("aggr_total_volume", 0)
    elif log_type == "running":
        return log.get("aggr_total_distance_km", 0)
    return 0

def calculate_exercise_xp_gains(log, log_type, past_logs, technique_multiplier):
    """
    Calculates XP for all 4 RPG tracks.
    Returns a dictionary of XP gained for each stat.
    """
    gains = {
        "mastery": 0,
        "strength": 0,
        "stamina": 0,
        "momentum": 0
    }
    
    # 1. Mastery: Base XP for showing up and practicing technique
    raw_sets = log.get("raw_sets", [])
    gains["mastery"] = int((25 + (len(raw_sets) * 5)) * technique_multiplier)

    # 2. Strength: Driven by e1RM (Heavy lifting)
    e1rm = log.get("aggr_best_e1RM", 0)
    if log_type in ["compound", "isolation", "bodyweight"]:
        gains["strength"] = int(e1rm * technique_multiplier)

    # 3. Stamina: Driven by Volume or Distance
    if log_type in ["compound", "isolation", "bodyweight"]:
        volume = log.get("aggr_total_volume", 0)
        gains["stamina"] = int((volume / 10) * technique_multiplier)
    elif log_type == "running":
        distance = log.get("aggr_total_distance_km", 0)
        gains["stamina"] = int((distance * 50) * technique_multiplier)

    # 4. Momentum: The Delta Scale (Relative Progression)
    current_metric = get_primary_metric(log, log_type)
    if not past_logs:
        gains["momentum"] = int(50 * technique_multiplier) # Discovery Bonus
    else:
        baseline = max([get_primary_metric(l, log_type) for l in past_logs] + [0])
        if baseline > 0 and current_metric > baseline:
            delta = (current_metric - baseline) / baseline
            capped_delta = min(delta * 10, 2.0)
            gains["momentum"] = int((50 * capped_delta) * technique_multiplier)

    return gains

def evaluate_level_progression(current_level, current_xp, xp_gained, xp_per_level_multiplier):
    """
    Calculates if a stat leveled up. 
    Level 1 requires 100 XP. Level 2 requires 200 XP. Level 3 requires 300 XP.
    """
    new_xp = current_xp + xp_gained
    leveled_up = False
    
    xp_required = current_level * xp_per_level_multiplier
    while new_xp >= xp_required:
        current_level += 1
        new_xp -= xp_required  # Carry over leftover XP
        leveled_up = True
        xp_required = current_level * xp_per_level_multiplier
        
    return current_level, new_xp, leveled_up