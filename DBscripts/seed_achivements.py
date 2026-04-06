from pymongo import MongoClient

# Connect to the local MongoDB exposed by your Docker container
client = MongoClient("mongodb://localhost:27017/")
db = client["trainingarc"]

def seed_achievements():
    print("Clearing old achievements...")
    db.achievements.drop()

    achievements = []

    # ==========================================
    # 1. BEGINNER & CORE MILESTONES
    # ==========================================
    core_achievements = [
        {"_id": "first_blood", "name": "First Blood", "description": "Completed your first workout. The journey begins."},
        {"_id": "level_5", "name": "Getting Serious", "description": "Reached Level 5."},
        {"_id": "level_10", "name": "Dedicated Athlete", "description": "Reached Level 10."},
        {"_id": "first_mastery", "name": "Student of the Game", "description": "Reached Level 2 Mastery on any exercise."},
        {"_id": "form_police", "name": "Form Police", "description": "Logged a set with a 5-star technique rating."},
    ]
    achievements.extend(core_achievements)

    # ==========================================
    # 2. THE LEAGUE OF LEGENDS RANKED SYSTEM
    # ==========================================
    # Defines the tier and the required stat level to reach it
    lol_ranks = [
        ("Iron", 15),
        ("Bronze", 30),
        ("Silver", 50),
        ("Gold", 75),
        ("Platinum", 100),
        ("Emerald", 150),
        ("Diamond", 200),
        ("Master", 300),
        ("Grandmaster", 400),
        ("Challenger", 500)
    ]

    stats = ["Strength", "Stamina", "Dexterity", "Endurance", "Consistency"]

    for stat in stats:
        for rank, threshold in lol_ranks:
            ach_id = f"{stat.lower()}_{rank.lower()}"
            ach_name = f"{rank} {stat}"
            ach_desc = f"Reached {threshold} {stat}. You are ranked {rank}."
            
            achievements.append({
                "_id": ach_id,
                "name": ach_name,
                "description": ach_desc,
                "stat_requirement": { "stat": stat.lower(), "value": threshold } # Useful for backend evaluation later
            })

    # ==========================================
    # 3. "OTHER STUFF" (FUN / GRIND MILESTONES)
    # ==========================================
    fun_achievements = [
        {"_id": "century_club", "name": "Century Club", "description": "Completed 100 total workouts."},
        {"_id": "night_owl", "name": "Night Owl", "description": "Finished a workout between Midnight and 4 AM."},
        {"_id": "early_bird", "name": "Early Bird", "description": "Finished a workout between 4 AM and 7 AM."},
        {"_id": "marathon_session", "name": "Marathon", "description": "Completed a single workout lasting over 2 hours."},
        {"_id": "hypertrophy_god", "name": "The Pump", "description": "Accumulated 10,000kg of total volume in a single session."},
        {"_id": "momentum_shift", "name": "Unstoppable Force", "description": "Gained Momentum XP by beating your 5-session baseline."}
    ]
    achievements.extend(fun_achievements)

    # Insert into database
    print(f"Inserting {len(achievements)} achievements into the database...")
    db.achievements.insert_many(achievements)
    print("Done! Your database is now populated.")

if __name__ == "__main__":
    seed_achievements()