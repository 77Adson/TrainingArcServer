def get_technique_multiplier(raw_sets):
    """Converts 1-5 star ratings into a 0.5x to 1.5x multiplier."""
    ratings = [s.get("technique_rating", 3) for s in raw_sets if s.get("technique_rating")]
    avg_technique = sum(ratings) / len(ratings) if ratings else 3.0
    return 0.5 + ((avg_technique - 1) * 0.25)

def calculate_momentum_score(current_log, log_type, past_logs, curr_tech_mult):
    """
    Calculates a weighted composite score comparing the current session
    to the average of the past sessions.
    """
    if not past_logs:
        return 0.5  # Default positive momentum for the first time

    def safe_delta(curr, base, invert=False):
        if base <= 0: return 0
        # If invert is True, lower is better (e.g., rest time, running pace)
        delta = (base - curr) / base if invert else (curr - base) / base
        # Cap individual deltas at +/- 1.0 (100% change) to prevent crazy math spikes
        return max(-1.0, min(1.0, delta))

    if log_type in ["compound", "isolation", "bodyweight"]:
        # 1. Current Values
        curr_e1rm = current_log.get("aggr_best_e1RM", 0)
        curr_vol = current_log.get("aggr_total_volume", 0)
        curr_rest = current_log.get("aggr_average_rest_sec", 0)
        
        # 2. Baseline Values (Averages from recent history)
        base_e1rm = sum(l.get("aggr_best_e1RM", 0) for l in past_logs) / len(past_logs)
        base_vol = sum(l.get("aggr_total_volume", 0) for l in past_logs) / len(past_logs)
        base_rest = sum(l.get("aggr_average_rest_sec", 0) for l in past_logs) / len(past_logs)
        base_tech = sum(get_technique_multiplier(l.get("raw_sets", [])) for l in past_logs) / len(past_logs)

        # 3. Calculate % change for each metric
        d_e1rm = safe_delta(curr_e1rm, base_e1rm)
        d_vol = safe_delta(curr_vol, base_vol)
        d_tech = safe_delta(curr_tech_mult, base_tech)
        d_rest = safe_delta(curr_rest, base_rest, invert=True)

        # 4. Weighted Composite Score
        composite_delta = (d_e1rm * 0.40) + (d_vol * 0.30) + (d_tech * 0.20) + (d_rest * 0.10)
        return composite_delta

    elif log_type == "running":
        # For running, momentum is a mix of distance (60%) and pace (40%)
        curr_dist = current_log.get("aggr_total_distance_km", 0)
        curr_time = current_log.get("aggr_total_time_sec", 0)
        curr_pace = curr_time / curr_dist if curr_dist > 0 else 0

        base_dist = sum(l.get("aggr_total_distance_km", 0) for l in past_logs) / len(past_logs)
        base_time = sum(l.get("aggr_total_time_sec", 0) for l in past_logs) / len(past_logs)
        base_pace = base_time / base_dist if base_dist > 0 else 0

        d_dist = safe_delta(curr_dist, base_dist)
        d_pace = safe_delta(curr_pace, base_pace, invert=True) # Lower pace is faster/better

        return (d_dist * 0.60) + (d_pace * 0.40)
        
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

    # 4. Momentum: The Composite Delta Scale
    if not past_logs:
        gains["momentum"] = int(100 * technique_multiplier) # Discovery Bonus
    else:
        composite_delta = calculate_momentum_score(log, log_type, past_logs, technique_multiplier)
        
        if composite_delta > 0:
            # Positive momentum scales up your XP!
            # e.g., 10% overall improvement -> 0.10 * 10 = 1.0 multiplier -> 50 XP
            capped_delta = min(composite_delta * 10, 2.0)
            gains["momentum"] = int((100 * capped_delta) * technique_multiplier)
        else:
            # Negative momentum: You had a bad day, but you still get a tiny trickle of XP for the effort.
            gains["momentum"] = int(25 * technique_multiplier)

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