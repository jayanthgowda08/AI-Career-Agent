"""
tests/test_jobs.py — Unit and Integration Tests for Job Listings Pipeline

Run with:
    pytest app/tests/test_jobs.py -v
"""

import uuid
import pytest


@pytest.fixture(autouse=True)
def seed_test_jobs(client):
    """Ensures sample jobs are seeded before running job tests."""
    res = client.post("/api/jobs/seed")
    assert res.status_code == 200


def test_seed_jobs_is_idempotent(client):
    """Running seed multiple times should update existing records without creating duplicates."""
    res1 = client.post("/api/jobs/seed")
    assert res1.status_code == 200
    
    # Second seed run should report 0 created
    res2 = client.post("/api/jobs/seed")
    assert res2.status_code == 200
    data = res2.json()
    assert data["created_count"] == 0
    assert data["updated_count"] >= 15


def test_list_jobs_pagination(client):
    """Test standard job listing pagination."""
    response = client.get("/api/jobs?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert data["total"] >= 15
    assert len(data["jobs"]) == 5


def test_filter_jobs_by_location(client):
    """Filtering by 'Remote' returns only remote jobs."""
    response = client.get("/api/jobs?location=Remote")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for job in data["jobs"]:
        assert "Remote" in job["location"]


def test_filter_jobs_by_experience_level(client):
    """Filtering by 'Entry-level' returns entry-level jobs."""
    response = client.get("/api/jobs?experience_level=Entry-level")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for job in data["jobs"]:
        assert job["experience_level"] == "Entry-level"


def test_filter_jobs_by_keyword(client):
    """Keyword search matches title or description."""
    response = client.get("/api/jobs?keyword=FastAPI")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    found = any("FastAPI" in job["description"] or "FastAPI" in job["title"] for job in data["jobs"])
    assert found


def test_get_job_by_id(client):
    """Retrieving a job by its exact UUID."""
    list_res = client.get("/api/jobs?page=1&page_size=1")
    first_job = list_res.json()["jobs"][0]
    job_id = first_job["id"]

    detail_res = client.get(f"/api/jobs/{job_id}")
    assert detail_res.status_code == 200
    job = detail_res.json()
    assert job["id"] == job_id
    assert job["title"] == first_job["title"]
    assert len(job["required_skills"]) > 0


def test_get_nonexistent_job_returns_404(client):
    """Requesting an invalid job UUID returns 404."""
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/api/jobs/{random_uuid}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
