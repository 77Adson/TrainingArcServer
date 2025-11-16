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
    from app.main.routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app