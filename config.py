import os
from datetime import timedelta

class Config:
    """Base configuration."""
    
    # 1. MongoDB: Sprawdzenie, czy URI jest ustawione w środowisku
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/trainingarc") 
    
    # 2. JWT: Check.
    # Wartość domyślna jest ustawiona na "dev-secret"
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
        
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # 3. Tryb Debug: Pozwala wyłączyć debugowanie z poziomu pliku .env w produkcji
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ["true", "1", "t"]

    if JWT_SECRET_KEY == "dev-secret-key" and not DEBUG:
        raise ValueError("CRITICAL ERROR: Lack of JWT_SECRET_KEY in environment variables. Please set it before running the server in production.")