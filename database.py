"""
Database session dependency and startup migrations for FastAPI.
"""

import sqlite3
from typing import Generator

from sqlalchemy.orm import Session

from models import ENGINE, SessionLocal, DB_PATH


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations() -> None:
    """Idempotent schema migrations applied at app startup."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for table in ("works", "artifacts"):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = {row[1] for row in cursor.fetchall()}
        if "deleted_at" not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN deleted_at DATETIME")

    # Add cover_image_path to artifacts if missing
    cursor.execute("PRAGMA table_info(artifacts)")
    artifact_cols = {row[1] for row in cursor.fetchall()}
    if "cover_image_path" not in artifact_cols:
        cursor.execute("ALTER TABLE artifacts ADD COLUMN cover_image_path TEXT")

    conn.commit()
    conn.close()
