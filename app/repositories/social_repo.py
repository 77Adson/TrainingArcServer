from bson.objectid import ObjectId
from app import mongo

def get_friendship(user_id_1_str, user_id_2_str):
    return mongo.db.friendships.find_one({
        "$or": [
            {"user1": ObjectId(user_id_1_str), "user2": ObjectId(user_id_2_str)},
            {"user1": ObjectId(user_id_2_str), "user2": ObjectId(user_id_1_str)}
        ]
    })

def get_all_friendships(user_id_str):
    return list(mongo.db.friendships.find({
        "$or": [{"user1": ObjectId(user_id_str)}, {"user2": ObjectId(user_id_str)}]
    }))

def create_friendship(friendship_doc):
    return mongo.db.friendships.insert_one(friendship_doc)