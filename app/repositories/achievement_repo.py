# achievement_repo.py
from app import mongo

def get_all_achievements():
    return list(mongo.db.achievements.find())

def get_achievements_by_ids(ach_ids):
    return list(mongo.db.achievements.find({"_id": {"$in": ach_ids}}))
    
def get_stat_achievements():
    return list(mongo.db.achievements.find({"stat_requirement": {"$exists": True}}))