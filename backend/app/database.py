"""
database.py — Database Connection Setup

This module creates the SQLAlchemy engine, session factory, and base class
that all database models will inherit from.

Key concepts:
- Engine: the connection pool to PostgreSQL.
- SessionLocal: a factory that creates database sessions.
  Each API request gets its own session, uses it, and closes it.
- Base: the declarative base that all SQLAlchemy models inherit from.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import OperationalError
from loguru import logger
from app.config import settings


# ============================================================
# Engine — the connection pool to PostgreSQL
# ============================================================
# pool_pre_ping=True means SQLAlchemy will test the connection
# before using it, automatically reconnecting if it dropped.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,          # number of persistent connections in the pool
    max_overflow=20,       # extra connections allowed beyond pool_size
    echo=settings.is_development,  # log all SQL in dev mode (disable in prod)
)


# ============================================================
# SessionLocal — session factory
# ============================================================
# autocommit=False means we control when to commit transactions.
# autoflush=False means SQLAlchemy won't flush pending changes
# automatically — we control this explicitly.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# Base declarative class
class Base(DeclarativeBase):
    pass


def init_db():
    """Ensures all registered models exist as PostgreSQL tables."""
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("🗄️ Database tables verified & created.")


# ============================================================
# Dependency — provides a DB session to FastAPI route handlers
# ============================================================
def get_db():
    """
    FastAPI dependency that provides a database session.

    Usage in a route:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...

    The 'yield' pattern ensures the session is always closed after
    the request finishes, even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# Health check — verify DB is reachable
# ============================================================
def check_database_connection() -> bool:
    """
    Runs a simple SELECT 1 query to confirm the database is reachable.
    Called at application startup.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful.")
        return True
    except OperationalError as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
