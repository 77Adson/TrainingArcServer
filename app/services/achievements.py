from app.repositories import achievement_repo

def evaluate_user_achievements(user_doc, new_level, new_stats):
    """
    Dynamically checks the database for achievements the user qualifies for.
    """
    unlocked_ids = user_doc.get("achievements", [])
    new_unlocks = []

    def grant(ach_id):
        if ach_id not in unlocked_ids and ach_id not in new_unlocks:
            new_unlocks.append(ach_id)

    # 1. Base Core checks
    grant("first_blood")
    if new_level >= 5: grant("level_5")
    if new_level >= 10: grant("level_10")

    # 2. Dynamic LoL Rank Stat Checks
    # Fetch all achievements that have a "stat_requirement" field
    stat_achievements = achievement_repo.get_achievements_with_stat_requirements()
    
    for ach in stat_achievements:
        req = ach["stat_requirement"]
        stat_name = req["stat"]
        required_value = req["value"]
        
        # If the user's current stat meets or exceeds the requirement, grant it!
        if new_stats.get(stat_name, 0) >= required_value:
            grant(ach["_id"])

    return new_unlocks

def get_display_names(achievement_ids):
    """Fetches the readable names for the Android summary screen."""
    if not achievement_ids:
        return []
        
    # Query the database for all achievements matching the unlocked IDs
    docs = achievement_repo.get_achievements_by_ids(achievement_ids)
    return [doc["name"] for doc in docs]