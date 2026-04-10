from bson.objectid import ObjectId
from app import mongo

def upsert_exercise_log(user_id_str, exercise_id_str, session_id, update_doc):
    return mongo.db.exercise_logs.update_one(
        {
            "userId": ObjectId(user_id_str),
            "exercise_id": ObjectId(exercise_id_str),
            "session_id": session_id
        },
        {"$set": update_doc},
        upsert=True
    )

def get_logs_for_exercise(user_id_str, exercise_id_str):
    return list(mongo.db.exercise_logs.find(
        {"userId": ObjectId(user_id_str), "exercise_id": ObjectId(exercise_id_str)}
    ).sort("date", 1))

def get_logs_by_session(session_id):
    return list(mongo.db.exercise_logs.find({"session_id": session_id}))

def get_user_log_dates(user_id_str):
    return list(mongo.db.exercise_logs.find({"userId": ObjectId(user_id_str)}, {"date": 1}))

def get_past_logs_for_exercise(exercise_id_str, exclude_session_id, limit=5):
    return list(mongo.db.exercise_logs.find({
        "exercise_id": ObjectId(exercise_id_str),
        "session_id": {"$ne": exclude_session_id}
    }).sort("date", -1).limit(limit))