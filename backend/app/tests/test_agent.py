"""
tests/test_agent.py — Unit and Integration Tests for AI Career Agent & Tools

Run with:
    pytest app/tests/test_agent.py -v
"""

import json
import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.agents.tools import (
    search_jobs,
    get_job_details,
    compare_jobs,
    analyse_skill_gap,
    recommend_jobs,
    save_job,
    get_saved_jobs,
    update_candidate_preferences,
)
from app.agents.graph import create_career_agent_graph, should_continue


@pytest.fixture
def test_user(client):
    """Creates a user and profile for agent testing."""
    email = f"agent_user_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "StrongPassword123!"
    reg = client.post("/api/auth/register", json={"email": email, "password": pwd})
    token = reg.json()["access_token"]
    user_id = reg.json()["user_id"]
    headers = {"Authorization": f"Bearer {token}"}

    client.put(
        "/api/profiles/me",
        json={
            "full_name": "Test Candidate",
            "skills": ["Python", "FastAPI", "Docker"],
            "preferred_roles": ["Backend Developer"],
            "preferred_locations": ["Remote"],
        },
        headers=headers,
    )
    return {"user_id": user_id, "headers": headers}


@pytest.fixture(autouse=True)
def seed_jobs_and_embeddings(client):
    """Seed sample jobs."""
    client.post("/api/jobs/seed")
    client.post("/api/search/embed-all")


# ============================================================
# Tool Unit Tests (Testing all 8 tools individually)
# ============================================================
def test_tool_search_jobs():
    """search_jobs tool returns JSON with matched jobs."""
    res_str = search_jobs(query="Python backend", location="New York")
    data = json.loads(res_str)
    assert "jobs_found" in data
    assert data["jobs_found"] >= 1
    assert "title" in data["results"][0]


def test_tool_get_job_details(client):
    """get_job_details tool returns comprehensive job data."""
    job_id = client.get("/api/jobs?page=1&page_size=1").json()["jobs"][0]["id"]
    res_str = get_job_details(job_id=str(job_id))
    data = json.loads(res_str)
    assert data["id"] == str(job_id)
    assert "required_skills" in data
    assert "description" in data


def test_tool_compare_jobs(client):
    """compare_jobs compares two opportunities side by side."""
    jobs = client.get("/api/jobs?page=1&page_size=2").json()["jobs"]
    j1_id = jobs[0]["id"]
    j2_id = jobs[1]["id"]

    res_str = compare_jobs(job_id_1=str(j1_id), job_id_2=str(j2_id))
    data = json.loads(res_str)
    assert "job_1" in data
    assert "job_2" in data
    assert "shared_skills" in data


def test_tool_analyse_skill_gap(client, test_user):
    """analyse_skill_gap compares candidate skills against job requirements."""
    job_id = client.get("/api/jobs?page=1&page_size=1").json()["jobs"][0]["id"]
    res_str = analyse_skill_gap(job_id=str(job_id), candidate_id=str(test_user["user_id"]))
    data = json.loads(res_str)
    assert "job_title" in data
    assert "match_score" in data
    assert "matching_skills" in data
    assert "missing_required_skills" in data


def test_tool_recommend_jobs(test_user):
    """recommend_jobs returns personalized job list."""
    res_str = recommend_jobs(candidate_id=str(test_user["user_id"]), top_k=3)
    data = json.loads(res_str)
    assert "recommendations_count" in data
    assert len(data["jobs"]) <= 3


def test_tool_save_and_get_saved_jobs(client, test_user):
    """save_job bookmarks a job and get_saved_jobs retrieves it."""
    job_id = client.get("/api/jobs?page=1&page_size=1").json()["jobs"][0]["id"]
    user_id = str(test_user["user_id"])

    # 1. Save job
    save_res = json.loads(save_job(user_id=user_id, job_id=str(job_id)))
    assert save_res["status"] == "success"

    # 2. Get saved jobs
    get_res = json.loads(get_saved_jobs(user_id=user_id))
    assert get_res["saved_count"] >= 1
    assert any(j["job_id"] == str(job_id) for j in get_res["saved_jobs"])


def test_tool_update_candidate_preferences(test_user):
    """update_candidate_preferences modifies candidate search preferences."""
    res_str = update_candidate_preferences(
        user_id=str(test_user["user_id"]),
        preferred_roles=["Lead Architect", "Staff Engineer"],
        preferred_locations=["Tokyo", "London"],
    )
    data = json.loads(res_str)
    assert data["status"] == "success"


# ============================================================
# Saved Jobs API Endpoints Tests
# ============================================================
def test_saved_jobs_api_crud(client, test_user):
    """Test bookmarking and removing jobs via the REST API endpoints."""
    headers = test_user["headers"]
    job_id = client.get("/api/jobs?page=1&page_size=1").json()["jobs"][0]["id"]

    # 1. Bookmark job
    post_res = client.post(f"/api/agent/saved-jobs/{job_id}", headers=headers)
    assert post_res.status_code == 201

    # 2. List saved jobs
    list_res = client.get("/api/agent/saved-jobs", headers=headers)
    assert list_res.status_code == 200
    saved = list_res.json()
    assert len(saved) >= 1
    assert any(str(item["job"]["id"]) == str(job_id) for item in saved)

    # 3. Delete saved job
    del_res = client.delete(f"/api/agent/saved-jobs/{job_id}", headers=headers)
    assert del_res.status_code == 200


# ============================================================
# LangGraph Graph Routing Tests
# ============================================================
def test_should_continue_logic():
    """Verify conditional edge routing decisions in the LangGraph graph."""
    # When status is finished -> terminate
    assert should_continue({"status": "finished", "iterations": 1}) == "end"

    # When status is tool_call -> continue to tools_node
    assert should_continue({"status": "tool_call", "iterations": 1}) == "tools_node"

    # When iterations reach limit -> force termination
    assert should_continue({"status": "tool_call", "iterations": 8}) == "end"


def test_agent_chat_endpoint_mocked(client, test_user):
    """
    Integration test for /api/agent/chat:
    Mocks agent execution output to verify API contract and response schema.
    """
    mock_response = (
        "Based on your profile, here are 3 excellent job opportunities matching your Python skills:\n"
        "1. Junior AI Engineer at DeepMind Innovations (90% match)\n"
        "2. Backend Python Developer at FinFlow Payments (85% match)"
    )
    mock_tools = [
        {"tool_name": "recommend_jobs", "arguments": {"top_k": 3}, "result_summary": "Found 3 jobs"}
    ]

    with patch("app.api.agent.run_career_agent", return_value=(mock_response, mock_tools, [])):
        response = client.post(
            "/api/agent/chat",
            json={"message": "Can you recommend jobs for me?"},
            headers=test_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert "Based on your profile" in data["message"]
        assert len(data["tools_used"]) == 1
        assert data["tools_used"][0]["tool_name"] == "recommend_jobs"
        assert "session_id" in data
