import datetime
from app.repositories import workout_repo, log_repo, achievement_repo

def build_weekly_schedule(user_id_str):
    workouts = workout_repo.get_workouts_by_user(user_id_str)
    
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    schedule = {day: None for day in days_of_week}
    
    for w in workouts:
        days = w.get("days_of_week", {})
        for day, is_active in days.items():
            if is_active and not schedule[day]:
                total_exercises = sum([len(g.get("exercise_ids", [])) for g in w.get("exercise_groups", [])])
                schedule[day] = {
                    "_id": str(w["_id"]),
                    "name": w.get("name", "Unnamed Workout"),
                    "description": w.get("description", ""),
                    "average_time_sec": w.get("average_time_sec", 0),
                    "total_exercises": total_exercises
                }
                
    unique_scheduled_days = sum(1 for day, w in schedule.items() if w is not None)
    return schedule, unique_scheduled_days

def calculate_streak_and_progress(user_id_str, target_days):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    start_of_week = today - datetime.timedelta(days=today.weekday())

    logs = log_repo.get_user_log_dates(user_id_str)
    workout_dates = sorted(list(set([log["date"].date() for log in logs if "date" in log])), reverse=True)

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

    workouts_this_week = sum(1 for d in workout_dates if d >= start_of_week)
    worked_out_today = bool(workout_dates and workout_dates[0] == today)

    return {
        "streak": streak,
        "this_week_completed": workouts_this_week,
        "this_week_target": target_days if target_days > 0 else 1,
        "worked_out_today": worked_out_today
    }

def get_recent_achievements(user):
    recent_ach_ids = user.get("achievements", [])[-3:]
    recent_achievements = []
    
    if recent_ach_ids:
        ach_docs = achievement_repo.get_achievements_by_ids(recent_ach_ids)
        ach_map = {doc["_id"]: doc for doc in ach_docs}
        
        for ach_id in reversed(recent_ach_ids):
            if ach_id in ach_map:
                recent_achievements.append({
                    "id": ach_map[ach_id]["_id"],
                    "name": ach_map[ach_id]["name"],
                    "description": ach_map[ach_id]["description"]
                })
                
    return recent_achievements