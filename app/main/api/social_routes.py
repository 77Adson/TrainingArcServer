import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from bson.objectid import ObjectId
from app import mongo

social_bp = Blueprint('social_bp', __name__)

@social_bp.route("/friends/invite", methods=["GET"])
@jwt_required()
def generate_invite():
    """Generates a signed, short-lived JWT for the QR code."""
    user_id = get_jwt_identity()
    # Invite expires in 10 minutes to prevent old QR codes from being scraped
    expires = datetime.timedelta(minutes=10)
    invite_token = create_access_token(identity=user_id, expires_delta=expires)
    return jsonify({"invite_token": invite_token}), 200

@social_bp.route("/friends/scan", methods=["POST"])
@jwt_required()
def accept_invite():
    """Consumes a scanned token and creates a bidirectional friendship."""
    my_id = get_jwt_identity()
    data = request.json
    scanned_token = data.get("invite_token")

    if not scanned_token:
        return jsonify({"message": "No token provided"}), 400

    try:
        # We use a custom verification or just decode if we trust the signature
        # For simplicity, we assume the frontend sends the token back to us
        from flask_jwt_extended import decode_token
        decoded = decode_token(scanned_token)
        friend_id = decoded["sub"]

        if friend_id == my_id:
            return jsonify({"message": "You cannot be your own rival"}), 400

        # Check if already friends
        exists = mongo.db.friendships.find_one({
            "$or": [
                {"user1": ObjectId(my_id), "user2": ObjectId(friend_id)},
                {"user1": ObjectId(friend_id), "user2": ObjectId(my_id)}
            ]
        })

        if not exists:
            mongo.db.friendships.insert_one({
                "user1": ObjectId(my_id),
                "user2": ObjectId(friend_id),
                "created_at": datetime.datetime.now(datetime.timezone.utc)
            })

        return jsonify({"message": "Friendship established!"}), 201
    except Exception as e:
        return jsonify({"message": "Invalid or expired invite"}), 400

@social_bp.route("/friends", methods=["GET"])
@jwt_required()
def get_friends():
    """Returns a list of friends with basic RPG stats."""
    my_id = get_jwt_identity()
    
    friendships = list(mongo.db.friendships.find({
        "$or": [{"user1": ObjectId(my_id)}, {"user2": ObjectId(my_id)}]
    }))

    friend_ids = []
    for f in friendships:
        friend_ids.append(f["user2"] if str(f["user1"]) == my_id else f["user1"])

    friends_data = list(mongo.db.users.find(
        {"_id": {"$in": friend_ids}},
        {"username": 1, "level": 1, "total_xp": 1, "stats": 1}
    ))

    for f in friends_data:
        f["_id"] = str(f["_id"])

    return jsonify(friends_data), 200

@social_bp.route("/friends/<friend_id>/profile", methods=["GET"])
@jwt_required()
def get_friend_profile(friend_id):
    """Returns full RPG stats and achievements for a training partner."""
    my_id = get_jwt_identity()
    
    # 1. Verify Friendship
    friendship = mongo.db.friendships.find_one({
        "$or": [
            {"user1": ObjectId(my_id), "user2": ObjectId(friend_id)},
            {"user1": ObjectId(friend_id), "user2": ObjectId(my_id)}
        ]
    })
    if not friendship:
        return jsonify({"message": "Unauthorized"}), 403

    # 2. Fetch sanitied User data
    user = mongo.db.users.find_one(
        {"_id": ObjectId(friend_id)},
        {"username": 1, "level": 1, "total_xp": 1, "stats": 1, "achievements": 1}
    )
    if not user:
        return jsonify({"message": "User not found"}), 404

    user["_id"] = str(user["_id"])
    return jsonify(user), 200

@social_bp.route("/friends/<friend_id>/workouts", methods=["GET"])
@jwt_required()
def get_friend_workouts(friend_id):
    """Returns a list of sanitized blueprints owned by the friend."""
    my_id = get_jwt_identity()
    
    # Verify Friendship
    friendship = mongo.db.friendships.find_one({
        "$or": [
            {"user1": ObjectId(my_id), "user2": ObjectId(friend_id)},
            {"user1": ObjectId(friend_id), "user2": ObjectId(my_id)}
        ]
    })
    if not friendship:
        return jsonify({"message": "Unauthorized"}), 403

    # Fetch blueprints (sanitized for list view)
    workouts = list(mongo.db.workouts.find({"userId": ObjectId(friend_id)}))
    output = []
    for w in workouts:
        output.append({
            "_id": str(w["_id"]),
            "name": w.get("name", "Unnamed Plan"),
            "average_time_sec": w.get("average_time_sec", 0) # FIXED JSON KEY
        })
    return jsonify(output), 200