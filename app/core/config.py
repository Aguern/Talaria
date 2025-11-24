# Fichier: app/core/config.py

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database URL (optional - not needed for DéMé Traiteur which uses Notion)
    DATABASE_URL: Optional[str] = Field(default=None)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Clé pour le chiffrement des configurations
    FERNET_KEY: str

    # Variables pour Celery (optionnelles pour permettre le mode Direct sans Celery)
    CELERY_BROKER_URL: str = Field(default="")
    CELERY_RESULT_BACKEND: str = Field(default="")

    # LLM Configuration
    OPENAI_MODEL: str = "gpt-5-mini-2025-08-07"
    OPENAI_TEMPERATURE: float = 0.0

    # Database debugging (set to "true" to log SQL queries)
    DEBUG_SQL: str = Field(default="false")

    # CORS configuration (comma-separated list of allowed origins)
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:3001")

    class Config:
        env_file = ".env"

settings = Settings()