from bson.objectid import ObjectId
from app import mongo

def clone_workout_blueprint(source_workout_id, requester_id_str):
    """
    Recursively copies exercises and recreates the workout container.
    """
    # 1. Fetch original workout
    original = mongo.db.workouts.find_one({"_id": ObjectId(source_workout_id)})
    if not original:
        return None

    new_exercise_groups = []
    
    # 2. Iterate through groups and clone exercises
    for group in original.get("exercise_groups", []):
        new_ids = []
        for ex_id in group.get("exercise_ids", []):
            # Fetch original exercise
            old_ex = mongo.db.exercises.find_one({"_id": ObjectId(ex_id)})
            if old_ex:
                # Prepare a clean copy for the new user
                new_ex_doc = {
                    "userId": ObjectId(requester_id_str),
                    "name": old_ex["name"],
                    "main_type": old_ex.get("main_type"),
                    "goal": old_ex.get("goal"),
                    "notes": old_ex.get("notes"),
                    "tags": old_ex.get("tags", []),
                    # RESET RPG STATS
                    "mastery_level": 1,
                    "stats": {
                        "mastery": {"level": 1, "xp": 0},
                        "strength": {"level": 1, "xp": 0},
                        "stamina": {"level": 1, "xp": 0},
                        "momentum": {"level": 1, "xp": 0}
                    }
                }
                res = mongo.db.exercises.insert_one(new_ex_doc)
                new_ids.append(str(res.inserted_id))
        
        new_exercise_groups.append({
            "name": group["name"],
            "exercise_ids": new_ids
        })

    # 3. Create the new Workout Blueprint
    new_workout = {
        "userId": ObjectId(requester_id_str),
        "name": f"Copy of {original['name']}",
        "description": original.get("description", ""),
        "exercise_groups": new_exercise_groups,
        "days_of_week": {d: False for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
        "average_time_sec": 0,
        "sessions_completed": 0
    }
    
    final_res = mongo.db.workouts.insert_one(new_workout)
    return str(final_res.inserted_id)