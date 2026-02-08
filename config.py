import os
from datetime import timedelta

class Config:
    """Base configuration."""
    # Ustaw te zmienne w swoim środowisku EC2!
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://FlaskUser:pakerapp1@172.31.41.176:27017/training_arc_db") # Private IP address of MongoDB server
    # MONGO_URI = os.environ.get("MONGO_URI", "mongodb://FlaskUser:pakerapp1@16.171.146.230:27017/training_arc_db") # Public IP address of MongoDB server
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "twoj-super-sekretny-klucz-jwt")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    # Ustaw na False w produkcji!
    DEBUG = True