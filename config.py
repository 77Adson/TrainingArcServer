import os

class Config:
    """Base configuration."""
    # Ustaw te zmienne w swoim środowisku EC2!
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://myFlaskAppUser:anotherStrongPassword@172.31.41.176:27017/training_arc_db")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "twoj-super-sekretny-klucz-jwt")
    # Ustaw na False w produkcji!
    DEBUG = True