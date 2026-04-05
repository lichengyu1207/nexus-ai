import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Fangtan AI Platform"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Intelligent real estate analysis platform"
    
    # API settings
    API_V1_STR: str = "/api"
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str
    
    # Redis settings
    REDIS_URL: str
    
    # Celery settings
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Security settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # AI Agent settings
    OPENAI_API_KEY: Optional[str] = None
    LANGCHAIN_TRACING_V2: bool = False
    LANGSMITH_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()