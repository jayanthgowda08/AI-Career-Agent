"""
tests/conftest.py — Pytest Configuration and Shared Fixtures

Prepares test database tables and provides a reusable TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from app.database import engine, Base
from app.models.user import User  # noqa: F401
from app.models.profile import CandidateProfile  # noqa: F401
from app.main import app as fastapi_app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Runs once before any test executes:
    Ensures all database tables exist in PostgreSQL.
    """
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    """Provides a TestClient for making HTTP requests in tests."""
    with TestClient(fastapi_app) as test_client:
        yield test_client
