from app.repositories import user_repo, log_repo, exercise_repo
from . import rpg_math
from . import achievements
import datetime

def calculate_rpg_gains(user_id_str, session_id, duration_sec):
    user = user_repo.get_user_by_id(user_id_str)
    if not user: return {}

    session_logs = log_repo.get_logs_by_session(session_id)
    
    user_xp_gained = 50 + int((duration_sec / 60) * 2)
    exercise_level_ups = []
    user_stat_gains = {"strength": 0, "stamina": 0, "dexterity": 0, "endurance": 0, "consistency": 0}

    for log in session_logs:
        exercise_id_str = str(log.get("exercise_id"))
        log_type = log.get("log_type", "compound")
        
        past_logs = log_repo.get_past_logs_for_exercise(exercise_id_str, session_id)
        
        tech_mult = rpg_math.get_technique_multiplier(log.get("raw_sets", []))
        xp_gains = rpg_math.calculate_exercise_xp_gains(log, log_type, past_logs, tech_mult)
        
        exercise = exercise_repo.get_exercise_by_id(exercise_id_str)
        if exercise:
            default_stats = {
                "mastery": {"level": 1, "xp": 0},
                "strength": {"level": 1, "xp": 0},
                "stamina": {"level": 1, "xp": 0},
                "momentum": {"level": 1, "xp": 0}
            }
            current_stats = exercise.get("stats", default_stats)
            
            for stat_name in ["mastery", "strength", "stamina", "momentum"]:
                stat_data = current_stats.get(stat_name, {"level": 1, "xp": 0})
                curr_lvl = stat_data["level"]
                curr_xp = stat_data["xp"]
                
                new_lvl, new_xp, leveled_up = rpg_math.evaluate_level_progression(
                    curr_lvl, curr_xp, xp_gains[stat_name], xp_per_level_multiplier=100
                )
                
                current_stats[stat_name] = {"level": new_lvl, "xp": new_xp}
                
                if leveled_up:
                    exercise_level_ups.append({
                        "name": exercise.get("name", "Unknown"),
                        "stat": stat_name,
                        "new_level": new_lvl
                    })
            
            exercise_repo.update_exercise_advanced(exercise_id_str, {"$set": {"stats": current_stats}})
            
        if log_type == "compound": user_stat_gains["strength"] += 1
        elif log_type == "isolation": user_stat_gains["stamina"] += 1
        elif log_type == "bodyweight": user_stat_gains["dexterity"] += 1
        elif log_type == "running": user_stat_gains["endurance"] += 1

    current_highest_streak = user.get("highest_streak", 0)
    consistency_gained, new_highest_streak = _evaluate_user_streak(user_id_str, current_highest_streak)
    user_stat_gains["consistency"] += consistency_gained

    new_u_lvl, new_u_xp, u_leveled_up = rpg_math.evaluate_level_progression(
        user.get("level", 1), user.get("total_xp", 0), user_xp_gained, xp_per_level_multiplier=1000
    )

    current_user_stats = user.get("stats", {"strength": 10, "stamina": 10, "dexterity": 10, "endurance": 10, "consistency": 10})
    for k, v in user_stat_gains.items():
        current_user_stats[k] = current_user_stats.get(k, 10) + v

    new_achievement_ids = achievements.evaluate_user_achievements(user, new_u_lvl, current_user_stats)
    readable_achievements = achievements.get_display_names(new_achievement_ids)

    user_repo.update_user_advanced(user_id_str, {
        "$set": {
            "level": new_u_lvl, 
            "total_xp": new_u_xp,
            "stats": current_user_stats,
            "highest_streak": new_highest_streak
        },
        "$push": {"achievements": {"$each": new_achievement_ids}}
    })

    return {
        "user_xp_gained": user_xp_gained,
        "user_leveled_up": u_leveled_up,
        "user_new_level": new_u_lvl,
        "exercise_level_ups": exercise_level_ups,
        "achievements_unlocked": readable_achievements,
        "user_stat_gains": user_stat_gains
    }

def _evaluate_user_streak(user_id_str, current_highest_streak):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    all_logs = log_repo.get_user_log_dates(user_id_str)
    workout_dates = sorted(list(set([log["date"].date() for log in all_logs if "date" in log])), reverse=True)

    streak = 0
    check_date = today
    
    if workout_dates and (workout_dates[0] == today or workout_dates[0] == today - datetime.timedelta(days=1)):
        idx = 0
        if workout_dates[0] == today - datetime.timedelta(days=1):
            check_date = today - datetime.timedelta(days=1)
            
        while idx < len(workout_dates) and workout_dates[idx] == check_date:
            streak += 1
            check_date -= datetime.timedelta(days=1)
            idx += 1

    consistency_gained = 1 + (streak // 3)
    new_highest_streak = max(current_highest_streak, streak)
    
    return consistency_gained, new_highest_streak