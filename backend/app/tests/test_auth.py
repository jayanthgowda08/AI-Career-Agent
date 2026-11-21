"""
tests/test_auth.py — Unit and Integration Tests for Authentication & Profiles

Run with:
    pytest app/tests/test_auth.py -v
"""

import uuid
import pytest


@pytest.fixture
def random_user():
    """Generates unique user credentials for test isolation."""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "email": f"testuser_{unique_id}@example.com",
        "password": "StrongPassword123!",
    }


def test_user_registration(client, random_user):
    """Test standard user registration returns a token and user_id."""
    response = client.post("/api/auth/register", json=random_user)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == random_user["email"]
    assert "user_id" in data


def test_duplicate_registration_fails(client, random_user):
    """Test duplicate email registration is rejected with 400 Bad Request."""
    # First registration
    res1 = client.post("/api/auth/register", json=random_user)
    assert res1.status_code == 201

    # Duplicate registration
    res2 = client.post("/api/auth/register", json=random_user)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_short_password_rejected(client):
    """Test passwords under 8 characters are caught by Pydantic validation."""
    response = client.post(
        "/api/auth/register",
        json={"email": "shortpass@example.com", "password": "short"},
    )
    assert response.status_code == 422  # Unprocessable Entity (Pydantic validation error)


def test_user_login_success(client, random_user):
    """Test logging in with correct credentials returns a valid JWT token."""
    client.post("/api/auth/register", json=random_user)

    login_res = client.post("/api/auth/login", json=random_user)
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["email"] == random_user["email"]


def test_user_login_invalid_password(client, random_user):
    """Test logging in with wrong password returns 401 Unauthorized."""
    client.post("/api/auth/register", json=random_user)

    bad_login = client.post(
        "/api/auth/login",
        json={"email": random_user["email"], "password": "WrongPassword999!"},
    )
    assert bad_login.status_code == 401


def test_get_and_update_profile(client, random_user):
    """Test retrieving and updating profile using Bearer token."""
    reg = client.post("/api/auth/register", json=random_user)
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch default profile
    get_res = client.get("/api/profiles/me", headers=headers)
    assert get_res.status_code == 200
    profile_data = get_res.json()
    assert profile_data["skills"] == []

    # 2. Update profile with skills, experience, and preferences
    update_payload = {
        "full_name": "Alex Developer",
        "headline": "Junior AI Engineer",
        "location": "San Francisco, CA",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Machine Learning"],
        "preferred_roles": ["AI Engineer", "Backend Developer"],
        "employment_types": ["Full-time", "Remote"],
        "experience": [
            {
                "company": "Startup Inc",
                "title": "Software Intern",
                "start_date": "2023-05",
                "end_date": "2023-08",
                "description": "Built REST APIs with Python.",
            }
        ],
    }

    put_res = client.put("/api/profiles/me", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["full_name"] == "Alex Developer"
    assert "Python" in updated["skills"]
    assert len(updated["experience"]) == 1
    assert updated["experience"][0]["company"] == "Startup Inc"
