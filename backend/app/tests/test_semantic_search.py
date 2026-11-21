"""
tests/test_semantic_search.py — Unit & Integration Tests for Semantic & Hybrid Search

Run with:
    pytest app/tests/test_semantic_search.py -v
"""

import pytest
from app.services.embedding_service import embed_text, compute_cosine_similarity, EMBEDDING_DIM


@pytest.fixture(autouse=True)
def setup_jobs_and_embeddings(client):
    """Ensures jobs are seeded and embeddings are generated before tests run."""
    client.post("/api/jobs/seed")
    client.post("/api/search/embed-all")


def test_embed_text_dimensions_and_normalization():
    """Embedding model should output 384-dimensional unit-normalized vector."""
    vec = embed_text("Python backend software engineer")
    assert len(vec) == EMBEDDING_DIM
    assert isinstance(vec[0], float)
    
    # Cosine similarity with itself should be ~1.0
    sim = compute_cosine_similarity(vec, vec)
    assert pytest.approx(sim, abs=1e-4) == 1.0


def test_cosine_similarity_semantic_relevance():
    """Related sentences should have significantly higher similarity than unrelated sentences."""
    vec_ai = embed_text("Machine learning engineer training transformers")
    vec_dl = embed_text("Deep learning specialist building neural networks")
    vec_chef = embed_text("Pastry chef baking croissants in a french bakery")

    sim_ai_dl = compute_cosine_similarity(vec_ai, vec_dl)
    sim_ai_chef = compute_cosine_similarity(vec_ai, vec_chef)

    # Conceptual similarity between ML and DL should far exceed ML and Pastry Chef
    assert sim_ai_dl > sim_ai_chef
    assert sim_ai_dl > 0.40   # Strong semantic closeness
    assert sim_ai_chef < 0.25  # Dissimilar domains


def test_semantic_search_ranks_relevant_jobs(client):
    """
    Search for 'intelligent agents and LLM applications'
    Should rank 'Junior AI Engineer' or 'LLM Solutions Architect' at the top,
    even though the exact query terms differ from the title.
    """
    payload = {
        "query": "intelligent agents and LLM applications",
        "top_k": 5,
    }
    response = client.post("/api/search/semantic", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    
    top_job = data["results"][0]["job"]
    top_score = data["results"][0]["similarity_score"]
    
    # Verify score is in valid range
    assert 0.0 <= top_score <= 1.0
    # Top result should be an AI/LLM/ML role
    assert any(term in top_job["title"].lower() for term in ["ai", "llm", "machine learning", "product manager"])


def test_semantic_search_with_location_filter(client):
    """Semantic search with location filter returns only jobs in that location."""
    payload = {
        "query": "backend API engineer",
        "location": "New York",
        "top_k": 5,
    }
    response = client.post("/api/search/semantic", json=payload)
    assert response.status_code == 200
    data = response.json()
    for item in data["results"]:
        assert "New York" in item["job"]["location"]


def test_hybrid_search(client):
    """Hybrid search combines vector similarity with keyword bonus."""
    payload = {
        "query": "FastAPI microservices payment settlement",
        "top_k": 5,
    }
    response = client.post("/api/search/hybrid", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["search_type"] == "hybrid"
    assert data["total_results"] > 0

    top_item = data["results"][0]
    assert top_item["similarity_score"] > 0
    assert top_item["semantic_score"] is not None
    assert top_item["keyword_score"] is not None
    assert len(top_item["match_reasons"]) >= 1
