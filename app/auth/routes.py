import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app import mongo, bcrypt

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    """Rejestruje nowego użytkownika."""
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    if mongo.db.users.find_one({"email": email}):
        return jsonify({"message": "Email already registered"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    mongo.db.users.insert_one({
        "email": email,
        "hashed_password": hashed_password,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    })
    
    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    """Loguje użytkownika i zwraca token JWT."""
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = mongo.db.users.find_one({"email": email})

    if user and bcrypt.check_password_hash(user["hashed_password"], password):
        access_token = create_access_token(identity=str(user["_id"]))
        return jsonify(access_token=access_token), 200
    
    return jsonify({"message": "Invalid email or password"}), 401

