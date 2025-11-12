# Fichier: app/core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Convert PostgreSQL URL to asyncpg format for SQLAlchemy async
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Enable SQL query logging only if DEBUG_SQL is set to "true"
# This prevents exposing sensitive data in production logs
echo_sql = settings.DEBUG_SQL.lower() == "true"
engine = create_async_engine(database_url, echo=echo_sql)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session