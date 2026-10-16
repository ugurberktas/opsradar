"""Database engine and session management for OpsRadar backend."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os

DATABASE_URL = os.getenv("OPSRADAR_DATABASE_URL", "sqlite:///./opsradar.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Safe to call on every startup."""
    # Import models to register them on Base metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
