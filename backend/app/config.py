"""
Application configuration - centralized config management
"""
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str
    
    # JWT Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 7
    
    # Risk Band Thresholds
    risk_band_high_threshold: float = 0.7
    risk_band_medium_threshold: float = 0.4
    
    # Storage
    storage_path: str = "./uploads"
    
    # Inspector Availability
    inspector_availability_threshold_minutes: int = 15
    
    # ML Model
    model_path: str = "./ml-artifact/model.pkl"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
