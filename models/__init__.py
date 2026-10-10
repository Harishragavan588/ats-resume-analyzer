"""
models/__init__.py — SQLAlchemy declarative base and database engine setup.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import Config


class Base(DeclarativeBase):
    pass


engine = create_engine(
    Config.DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + Flask threads
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Yield a database session and close it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they do not already exist."""
    # Import models so SQLAlchemy registers them before creating tables
    from models.analysis import Analysis, AnalysisComparison  # noqa: F401

    Base.metadata.create_all(bind=engine)
