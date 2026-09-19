"""
SQLAlchemy engine/session setup.

Uses SQLite by default so the project runs with zero external setup, but the
connection string is read from an environment variable so swapping in
Postgres (e.g. for a real cloud deployment) is a one-line change:

    export DATABASE_URL="postgresql://user:pass@host:5432/thunder_scout"
"""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "data" / "thunder_scout.db"

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
