"""
Healthcare Multi-Agent System Configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Healthcare Multi-Agent Assistant"
    DEBUG: bool = True
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    USERS_DIR: Path = DATA_DIR / "users"
    SHARED_DIR: Path = DATA_DIR / "shared"
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/healthcare.db"
    SESSIONS_DB: str = "data/sessions.db"
    
    # Auth
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Google Gemini
    GOOGLE_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.7
    
    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Document Processing
    OCR_DPI: int = 300
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    
    # Memory
    SUMMARIZATION_TRIGGER_TOKENS: int = 8000
    SUMMARIZATION_KEEP_MESSAGES: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create directories on import
settings = get_settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.USERS_DIR.mkdir(parents=True, exist_ok=True)
settings.SHARED_DIR.mkdir(parents=True, exist_ok=True)
