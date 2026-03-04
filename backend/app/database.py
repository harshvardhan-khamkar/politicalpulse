from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Keep database failures fast and explicit in local development.
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 10,
}

if settings.DATABASE_URL.startswith("postgresql"):
    # psycopg connect timeout in seconds
    engine_kwargs["connect_args"] = {"connect_timeout": 5}

# Create database engine
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Session local class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI routes to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()