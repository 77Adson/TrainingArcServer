from bson.objectid import ObjectId
from app import mongo

def get_user_by_id(user_id_str, projection=None):
    return mongo.db.users.find_one({"_id": ObjectId(user_id_str)}, projection)

def get_user_by_email(email):
    return mongo.db.users.find_one({"email": email})

def create_user(user_doc):
    return mongo.db.users.insert_one(user_doc)

def update_user_fields(user_id_str, update_data):
    return mongo.db.users.update_one({"_id": ObjectId(user_id_str)}, {"$set": update_data})

def update_user_advanced(user_id_str, update_doc):
    return mongo.db.users.update_one({"_id": ObjectId(user_id_str)}, update_doc)

def get_users_by_ids(user_id_strs, projection=None):
    ids = [ObjectId(uid) for uid in user_id_strs]
    return list(mongo.db.users.find({"_id": {"$in": ids}}, projection))