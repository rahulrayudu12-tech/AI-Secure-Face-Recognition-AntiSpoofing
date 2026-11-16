import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
TEMPLATE_DIR = DATA_DIR / "templates"
LOGS_DIR = DATA_DIR / "logs"

for directory in [DATA_DIR, UPLOAD_DIR, TEMPLATE_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "aura-id-cybersecurity-secret-key-2026-x99")
    JWT_SECRET = os.getenv("JWT_SECRET", "aura-id-jwt-super-secret-token-sign-key")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))
    
    # Database: Supports PostgreSQL or local SQLite automatically
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{DATA_DIR / 'secure_auth.db'}"
    )
    # Fix postgres:// URL prefix for modern SQLAlchemy if deployed on Heroku/Render
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Biometric Thresholds
    IDENTITY_MATCH_THRESHOLD = float(os.getenv("IDENTITY_MATCH_THRESHOLD", 0.65))
    LIVENESS_THRESHOLD = float(os.getenv("LIVENESS_THRESHOLD", 0.70))
    MULTIFTNET_THRESHOLD = float(os.getenv("MULTIFTNET_THRESHOLD", 0.68))
    MINIFASNET_THRESHOLD = float(os.getenv("MINIFASNET_THRESHOLD", 0.65))
    LSTM_TEMPORAL_THRESHOLD = float(os.getenv("LSTM_TEMPORAL_THRESHOLD", 0.60))
    
    # Quality Filter Threshold (Laplacian blur variance)
    BLUR_MIN_VARIANCE = 50.0
    MIN_FACE_SIZE = 80 # pixels
    
    # Host & Port
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
