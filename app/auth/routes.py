import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app import bcrypt
from app.repositories import user_repo

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    """Rejestruje nowego użytkownika. i zwraca JWT token."""
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    if user_repo.get_user_by_email(email):
        return jsonify({"message": "Email already registered"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    new_user_doc = {
        "email": email,
        "hashed_password": hashed_password,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        
        # --- SPRINT 3: RPG STATE INITIALIZATION ---
        "level": 1,
        "total_xp": 0,
        "achievements": [],
        "stats": {
            "strength": 10,
            "stamina": 10,
            "dexterity": 10,
            "endurance": 10,
            "consistency": 10
        }
    }

    user_id = user_repo.create_user(new_user_doc)
    
    access_token = create_access_token(identity=str(user_id.inserted_id))
    
    return jsonify(access_token=access_token), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    """Loguje użytkownika i zwraca token JWT."""
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = user_repo.get_user_by_email(email)

    if user and bcrypt.check_password_hash(user["hashed_password"], password):
        access_token = create_access_token(identity=str(user["_id"]))
        return jsonify(access_token=access_token), 200
    
    return jsonify({"message": "Invalid email or password"}), 401
