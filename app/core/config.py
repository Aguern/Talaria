# Fichier: app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Clé pour le chiffrement des configurations
    FERNET_KEY: str

    # Variables pour Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # LLM Configuration
    OPENAI_MODEL: str = "gpt-5-mini-2025-08-07"
    OPENAI_TEMPERATURE: float = 0.0

    class Config:
        env_file = ".env"

settings = Settings()