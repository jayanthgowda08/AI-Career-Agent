"""
tests/test_recommendations.py — Unit & Integration Tests for Recommendation Engine

Run with:
    pytest app/tests/test_recommendations.py -v
"""

import uuid
import pytest


@pytest.fixture
def python_ai_candidate(client):
    """
    Registers a candidate and populates their profile with Python & AI skills,
    preferred roles, and location preferences.
    """
    email = f"ai_candidate_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "StrongPassword123!"
    reg = client.post("/api/auth/register", json={"email": email, "password": pwd})
    token = reg.json()["access_token"]
    user_id = reg.json()["user_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Populate profile
    profile_update = {
        "full_name": "Maya AI Dev",
        "headline": "Junior AI & Backend Engineer",
        "location": "San Francisco, CA",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        "preferred_roles": ["Junior AI Engineer", "Backend Developer"],
        "preferred_locations": ["San Francisco, CA", "Remote"],
        "employment_types": ["Full-time"],
    }
    client.put("/api/profiles/me", json=profile_update, headers=headers)

    return {"headers": headers, "user_id": user_id}


@pytest.fixture(autouse=True)
def setup_jobs_and_embeddings(client):
    """Ensures jobs and embeddings exist."""
    client.post("/api/jobs/seed")
    client.post("/api/search/embed-all")


def test_personalized_recommendations(client, python_ai_candidate):
    """
    Candidate with Python, FastAPI, and AI preferences should receive
    highly ranked AI / Python engineering jobs with detailed breakdowns.
    """
    headers = python_ai_candidate["headers"]
    response = client.get("/api/recommendations?top_k=5", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_recommendations"] > 0
    top_rec = data["recommendations"][0]

    # Score should be a percentage between 0 and 100
    assert 0 <= top_rec["match_score"] <= 100
    assert len(top_rec["matching_skills"]) > 0
    assert "Python" in top_rec["matching_skills"] or "FastAPI" in top_rec["matching_skills"]
    assert len(top_rec["match_reasons"]) >= 1

    # Verify score breakdown attributes exist
    breakdown = top_rec["score_breakdown"]
    assert 0.0 <= breakdown["skill_score"] <= 1.0
    assert 0.0 <= breakdown["semantic_score"] <= 1.0


def test_skill_gap_analysis(client, python_ai_candidate):
    """
    Tests skill gap endpoint: compares candidate skills against a specific job.
    """
    # 1. Fetch a job to compare with
    jobs_res = client.get("/api/jobs?keyword=DeepMind")
    jobs = jobs_res.json()["jobs"]
    assert len(jobs) > 0
    target_job = jobs[0]
    job_id = target_job["id"]

    # 2. Run skill gap analysis
    headers = python_ai_candidate["headers"]
    response = client.get(f"/api/recommendations/skill-gap/{job_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["job_id"] == job_id
    assert data["job_title"] == target_job["title"]
    assert "matching_skills" in data
    assert "missing_required_skills" in data
    assert len(data["recommendations_for_improvement"]) > 0


def test_candidate_specific_recommendation_endpoint(client, python_ai_candidate):
    """
    Agent tools use /api/recommendations/candidate/{id} to get candidate recommendations.
    """
    user_id = python_ai_candidate["user_id"]
    response = client.get(f"/api/recommendations/candidate/{user_id}?top_k=3")
    assert response.status_code == 200
    data = response.json()
    assert str(data["candidate_id"]) == str(user_id)
    assert len(data["recommendations"]) <= 3


def test_recommendations_unauthenticated_rejected(client):
    """Unauthenticated requests to /api/recommendations should return 401."""
    response = client.get("/api/recommendations")
    assert response.status_code == 401
