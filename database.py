"""
Database session dependency and startup migrations for FastAPI.
"""

import sqlite3
from typing import Generator

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from models import ENGINE, SessionLocal, DB_PATH, Artifact, Work


@event.listens_for(Session, "do_orm_execute")
def _add_soft_delete_criteria(execute_state):
    """Globally enforce soft-deletes across all queries and relationships."""
    if execute_state.is_select:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                Artifact, lambda cls: cls.deleted_at.is_(None), include_aliases=True
            ),
            with_loader_criteria(
                Work, lambda cls: cls.deleted_at.is_(None), include_aliases=True
            ),
        )


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

    # Create scrape_log table if missing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scrape_log (
            id VARCHAR(36) PRIMARY KEY,
            artifact_id VARCHAR(36) NOT NULL REFERENCES artifacts(artifact_id),
            attempted_at DATETIME NOT NULL,
            source VARCHAR(40) NOT NULL,
            query TEXT,
            status VARCHAR(20) NOT NULL,
            error_detail TEXT,
            image_url TEXT
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS ix_scrape_log_artifact
        ON scrape_log(artifact_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS ix_scrape_log_source_status
        ON scrape_log(source, status)
    """)

    conn.commit()
    conn.close()
