"""Core configuration settings for the application."""

from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/traffic_db"
    database_url_sync: str = "postgresql://postgres:password@localhost:5432/traffic_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # YOLO Model
    yolo_model_path: str = "./models/yolov8n.pt"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Traffic Settings
    frame_processing_interval: float = 0.5  # seconds between frame processing
    signal_optimization_interval: float = 5.0  # seconds between optimization cycles
    
    # Signal Timing (seconds)
    signal_min_green: int = 10
    signal_max_green: int = 60
    signal_yellow_duration: int = 3
    signal_all_red_duration: int = 2
    
    # Thresholds
    low_density_threshold: int = 5  # vehicles
    medium_density_threshold: int = 15  # vehicles
    high_density_threshold: int = 30  # vehicles
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
