from bson.objectid import ObjectId
from app import mongo

def get_workouts_by_user(user_id_str, projection=None):
    return list(mongo.db.workouts.find({"userId": ObjectId(user_id_str)}, projection))

def get_workout_by_id(workout_id_str, user_id_str=None):
    query = {"_id": ObjectId(workout_id_str)}
    if user_id_str:
        query["userId"] = ObjectId(user_id_str)
    return mongo.db.workouts.find_one(query)

def create_workout(workout_doc):
    return mongo.db.workouts.insert_one(workout_doc)

def update_workout_fields(workout_id_str, user_id_str, update_data):
    return mongo.db.workouts.update_one(
        {"_id": ObjectId(workout_id_str), "userId": ObjectId(user_id_str)},
        {"$set": update_data}
    )

def update_workout_advanced(workout_id_str, update_doc):
    return mongo.db.workouts.update_one({"_id": ObjectId(workout_id_str)}, update_doc)

def delete_workout(workout_id_str, user_id_str):
    return mongo.db.workouts.delete_one({
        "_id": ObjectId(workout_id_str), 
        "userId": ObjectId(user_id_str)
    })