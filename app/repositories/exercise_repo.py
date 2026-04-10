from bson.objectid import ObjectId
from app import mongo

def get_exercises_by_user(user_id_str):
    return list(mongo.db.exercises.find({"userId": ObjectId(user_id_str)}))

def get_exercise_by_id(exercise_id_str, user_id_str=None):
    query = {"_id": ObjectId(exercise_id_str)}
    if user_id_str:
        query["userId"] = ObjectId(user_id_str)
    return mongo.db.exercises.find_one(query)

def create_exercise(exercise_doc):
    return mongo.db.exercises.insert_one(exercise_doc)

def update_exercise(exercise_id_str, user_id_str, update_data):
    return mongo.db.exercises.update_one(
        {"_id": ObjectId(exercise_id_str), "userId": ObjectId(user_id_str)},
        {"$set": update_data}
    )

def update_exercise_advanced(exercise_id_str, update_doc):
    return mongo.db.exercises.update_one({"_id": ObjectId(exercise_id_str)}, update_doc)