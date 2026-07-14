"""
EduGenie — Database Configuration
SQLite database with SQLAlchemy ORM.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./edugenie.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined by SQLAlchemy models.
    Called on FastAPI startup to ensure the schema exists."""
    from backend.models.query_history import QueryHistory  # noqa: F401
    from backend.models.quiz import Quiz  # noqa: F401
    from backend.models.user import User  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("[EduGenie] Database tables created successfully.")
