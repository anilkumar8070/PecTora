from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
import os

# Create SQLite database in the backend directory
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./Pectora.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # Needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator:
    """Dependency for FastAPI routes to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
