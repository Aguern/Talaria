# Fichier: app/core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Database engine and session (only created if DATABASE_URL is set)
engine = None
SessionLocal = None
Base = declarative_base()

# Only initialize database if DATABASE_URL is provided
# DéMé Traiteur doesn't need PostgreSQL - it uses Notion for data storage
if settings.DATABASE_URL:
    # Convert PostgreSQL URL to asyncpg format for SQLAlchemy async
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Enable SQL query logging only if DEBUG_SQL is set to "true"
    # This prevents exposing sensitive data in production logs
    echo_sql = settings.DEBUG_SQL.lower() == "true"
    engine = create_async_engine(database_url, echo=echo_sql)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def get_db():
    """Get database session. Raises error if database is not configured."""
    if SessionLocal is None:
        raise RuntimeError("Database not configured. Set DATABASE_URL environment variable.")
    async with SessionLocal() as session:
        yield session

def is_database_configured() -> bool:
    """Check if database is configured and available."""
    return engine is not None
