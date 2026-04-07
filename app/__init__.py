from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from config import Config

# Inicjalizacja rozszerzeń bez aplikacji
mongo = PyMongo()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app(config_class=Config):
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicjalizacja rozszerzeń z aplikacją
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Rejestracja Blueprints
    from app.auth.routes import auth_bp
    from app.main.api.user_routes import user_bp
    from app.main.api.exercise_routes import exercise_bp
    from app.main.api.workout_routes import workout_bp
    from app.main.api.exercise_log_routes import exercise_log_bp
    from app.main.api.dashboard_routes import dashboard_bp
    from app.main.api.social_routes import social_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(exercise_bp)
    app.register_blueprint(workout_bp)
    app.register_blueprint(exercise_log_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(social_bp)

    return app