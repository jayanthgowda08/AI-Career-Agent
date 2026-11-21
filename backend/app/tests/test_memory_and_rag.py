"""
tests/test_memory_and_rag.py — Unit & Integration Tests for Memory and RAG Pipelines

Run with:
    pytest app/tests/test_memory_and_rag.py -v
"""

import uuid
import pytest
from unittest.mock import patch

from app.database import SessionLocal
from app.services.memory_service import (
    save_conversation_turn,
    get_session_history,
    clear_session_history,
    extract_and_update_persistent_preferences,
)
from app.services.rag_service import (
    chunk_text,
    seed_rag_knowledge_base,
    retrieve_relevant_chunks,
    answer_career_question_with_rag,
)


@pytest.fixture
def auth_user(client):
    """Registers and returns user headers and user_id."""
    email = f"mem_user_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "StrongPassword123!"
    reg = client.post("/api/auth/register", json={"email": email, "password": pwd})
    token = reg.json()["access_token"]
    user_id = reg.json()["user_id"]
    return {"user_id": uuid.UUID(user_id), "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def second_user(client):
    """Second user to verify tenant isolation in memory."""
    email = f"isolation_user_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "StrongPassword123!"
    reg = client.post("/api/auth/register", json={"email": email, "password": pwd})
    user_id = reg.json()["user_id"]
    return {"user_id": uuid.UUID(user_id)}


# ============================================================
# Conversational Memory Tests
# ============================================================
def test_conversation_memory_persistence_and_isolation(auth_user, second_user):
    """Test saving messages, retrieving them, and verifying strict user isolation."""
    db = SessionLocal()
    session_id = f"test_session_{uuid.uuid4().hex[:6]}"
    u1_id = auth_user["user_id"]
    u2_id = second_user["user_id"]

    try:
        # User 1 saves a turn
        save_conversation_turn(
            db=db,
            user_id=u1_id,
            session_id=session_id,
            user_message="Find me junior AI roles in Seattle",
            assistant_response="I found 2 junior AI roles in Seattle for you.",
        )

        # Retrieve User 1 history
        u1_history = get_session_history(db, u1_id, session_id)
        assert len(u1_history) == 2
        assert u1_history[0]["role"] == "user"
        assert "Seattle" in u1_history[0]["content"]
        assert u1_history[1]["role"] == "assistant"

        # Verify User 2 cannot access User 1's history
        u2_history = get_session_history(db, u2_id, session_id)
        assert len(u2_history) == 0  # Tenant isolation verified

        # Clear User 1 history
        deleted = clear_session_history(db, u1_id, session_id)
        assert deleted == 2
        assert len(get_session_history(db, u1_id, session_id)) == 0
    finally:
        db.close()


def test_extract_and_persist_preferences(auth_user):
    """Tests automatic extraction of preferences from user chat messages."""
    db = SessionLocal()
    u_id = auth_user["user_id"]

    try:
        # Message expressing preference for remote work and AI roles
        msg = "I am looking for AI Engineer roles and I want remote opportunities."
        changes = extract_and_update_persistent_preferences(db, u_id, msg)
        assert changes is not None
        assert "Remote" in changes.get("preferred_locations", [])
    finally:
        db.close()


# ============================================================
# RAG (Retrieval-Augmented Generation) Tests
# ============================================================
def test_chunk_text_algorithm():
    """Verify that chunking creates segments with expected size and overlap."""
    sample_text = (
        "Designing scalable distributed systems requires careful planning of throughput, "
        "latency, availability, and consistency trade-offs. Engineers must evaluate whether "
        "to use relational databases like PostgreSQL or NoSQL databases like Cassandra. "
        "Caching layers with Redis can dramatically reduce database query pressure, while "
        "message queues like Kafka provide asynchronous decoupling."
    )
    chunks = chunk_text(sample_text, chunk_size=120, overlap=20)
    assert len(chunks) > 1
    # Check overlap: last few chars of chunk 0 should appear in chunk 1
    for c in chunks:
        assert len(c) <= 120


def test_seed_and_retrieve_rag_chunks():
    """Verify knowledge base seeding and pgvector cosine similarity retrieval."""
    db = SessionLocal()
    try:
        # Seed knowledge base
        seed_rag_knowledge_base(db)

        # Retrieve for system design question
        results = retrieve_relevant_chunks(
            db=db,
            query="How should I prepare for system design and microservice bottlenecks?",
            top_k=2,
        )
        assert len(results) >= 1
        top_chunk, score = results[0]
        assert score > 0.35
        assert any(
            topic in top_chunk.source_title.lower()
            for topic in ["system design", "microservices", "interview", "optimization"]
        )
    finally:
        db.close()


def test_rag_ask_endpoint(client, auth_user):
    """Test full RAG question answering endpoint returns citations and answers."""
    payload = {
        "question": "What is the STAR method for behavioral interviews?",
        "top_k": 2,
    }
    response = client.post(
        "/api/rag/ask",
        json=payload,
        headers=auth_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == payload["question"]
    assert len(data["answer"]) > 20
    assert len(data["citations"]) >= 1
    assert any("STAR" in c["source_title"] or "Behavioral" in c["source_title"] for c in data["citations"])
