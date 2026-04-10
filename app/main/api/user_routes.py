from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.repositories import user_repo, achievement_repo
import datetime

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    """Pobiera dane JEDNEGO, zalogowanego użytkownika."""
    try:
        user_id = get_jwt_identity()
        user = user_repo.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # 1. Convert ObjectId to string
        user['_id'] = str(user['_id'])
        
        # 2. Remove sensitive data
        user.pop('hashed_password', None)
        
        # 3. SAFETY FIX: Convert datetime to string manually
        if 'created_at' in user:
            user['created_at'] = user['created_at'].isoformat()
        
        return jsonify(user)
    except Exception as e:
        # This print helps you see the REAL error in your server console
        print(f"Error in get_user: {e}") 
        return jsonify({'error': str(e)}), 500

@user_bp.route("/user", methods=["PATCH"])
@jwt_required()
def update_user():
    """Ustawia preferencje użytkownika."""
    user_id = get_jwt_identity()
    data = request.json

    # Buduje słownik aktualizacji tylko z podanych pól
    update_data = {}
    if "username" in data:
        update_data["username"] = data["username"]
    if "weight" in data:
        update_data["weight"] = data["weight"]
    if "preferences" in data:
        update_data["preferences"] = data["preferences"]

    if not update_data:
        return jsonify({"message": "No data to update"}), 400

    # Aktualizuje dane w bazie danych
    user_repo.update_user_fields(user_id, update_data)
    
    return jsonify({"message": "User updated successfully"}), 200


@user_bp.route('/achievements', methods=['GET'])
@jwt_required()
def get_all_achievements():
    """Zwraca główną listę wszystkich dostępnych osiągnięć w grze z bazy danych."""
    achievements_cursor = achievement_repo.get_all_achievements()
    
    achievements_list = []
    for ach in achievements_cursor:
        achievements_list.append({
            "id": ach["_id"],
            "name": ach["name"],
            "description": ach["description"]
        })
        
    return jsonify(achievements_list), 200