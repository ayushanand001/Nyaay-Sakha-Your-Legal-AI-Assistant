import os
from pathlib import Path

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "NyayaSetu Backend API"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    
    # Supabase / PostgreSQL Database
    DATABASE_URL: str = os.getenv("SUPABASE_DB", "")
    
    # Security & Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "nyayasetu-insecure-dev-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Mail Config
    MAIL_USERNAME: str = os.getenv("EMAIL_USER", "")
    MAIL_PASSWORD: str = os.getenv("EMAIL_PASS", "")
    MAIL_FROM: str = os.getenv("EMAIL_USER", "")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "465"))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    
    # File Storage
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB

    # Model Artifacts Directory
    SERVICES_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/services"

    class Config:
        case_sensitive = True

settings = Settings()
