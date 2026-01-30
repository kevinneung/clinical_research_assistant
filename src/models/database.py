"""SQLite database connection and session management."""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

Base = declarative_base()

_engine = None
_SessionLocal = None


def get_engine(db_path: str | Path | None = None):
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        if db_path is None:
            # Default to app data directory
            db_path = Path.home() / ".clinical_research_assistant" / "database.db"
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            echo=False,
        )
    return _engine


def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db(db_path: str | Path | None = None) -> None:
    """Initialize the database, creating all tables."""
    engine = get_engine(db_path)

    # Import all models to ensure they're registered with Base
    from . import project, agent_run, approval, document  # noqa: F401

    Base.metadata.create_all(bind=engine)
