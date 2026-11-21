"""
tests/test_evaluations.py — Unit & Integration Tests for Evaluation Metrics & Benchmark Suite

Run with:
    pytest app/tests/test_evaluations.py -v
"""

import pytest
from app.services.evaluation_service import (
    compute_precision_at_k,
    compute_recall_at_k,
    compute_reciprocal_rank,
    compute_ndcg_at_k,
    run_recommendation_evaluation,
    run_agent_evaluation,
    run_rag_evaluation,
)
from app.database import SessionLocal


# ============================================================
# Pure Mathematical Formula Tests
# ============================================================
def test_precision_at_k_exact_math():
    """Verify Precision@K calculation on known vectors."""
    recommended = ["job-A", "job-B", "job-C", "job-D", "job-E"]
    ground_truth = ["job-A", "job-C", "job-X"]

    # In top 3: job-A (hit), job-B (miss), job-C (hit) -> 2 / 3 = 0.6667
    p3 = compute_precision_at_k(recommended, ground_truth, 3)
    assert p3 == 0.6667

    # In top 1: job-A (hit) -> 1 / 1 = 1.0
    p1 = compute_precision_at_k(recommended, ground_truth, 1)
    assert p1 == 1.0

    # In top 5: job-A, job-C -> 2 / 5 = 0.4
    p5 = compute_precision_at_k(recommended, ground_truth, 5)
    assert p5 == 0.4


def test_recall_at_k_exact_math():
    """Verify Recall@K calculation on known vectors."""
    recommended = ["job-A", "job-B", "job-C", "job-D", "job-E"]
    ground_truth = ["job-A", "job-C", "job-X", "job-Y"]  # 4 total relevant items

    # In top 3: 2 hits out of 4 total relevant -> 2 / 4 = 0.5
    r3 = compute_recall_at_k(recommended, ground_truth, 3)
    assert r3 == 0.5


def test_reciprocal_rank_exact_math():
    """Verify Reciprocal Rank: 1 / rank of first relevant item."""
    # First relevant at rank 1 -> 1.0
    assert compute_reciprocal_rank(["job-A", "job-B"], ["job-A"]) == 1.0

    # First relevant at rank 2 -> 0.5
    assert compute_reciprocal_rank(["job-X", "job-A"], ["job-A"]) == 0.5

    # First relevant at rank 4 -> 0.25
    assert compute_reciprocal_rank(["job-X", "job-Y", "job-Z", "job-A"], ["job-A"]) == 0.25

    # No relevant items -> 0.0
    assert compute_reciprocal_rank(["job-X", "job-Y"], ["job-A"]) == 0.0


def test_ndcg_at_k_exact_math():
    """Verify NDCG@K: ideal ranking gives 1.0, worse ranking gives lower score."""
    ground_truth = ["job-A", "job-B"]

    # Perfect ranking: both ground truth items at rank 1 and 2
    perfect_rec = ["job-A", "job-B", "job-C", "job-D"]
    ndcg_perfect = compute_ndcg_at_k(perfect_rec, ground_truth, 3)
    assert ndcg_perfect == 1.0

    # Inverted ranking: hits at rank 2 and 3 instead of 1 and 2
    delayed_rec = ["job-X", "job-A", "job-B", "job-C"]
    ndcg_delayed = compute_ndcg_at_k(delayed_rec, ground_truth, 3)
    assert 0.0 < ndcg_delayed < ndcg_perfect


# ============================================================
# Benchmark Runners & API Integration Tests
# ============================================================
def test_recommendation_benchmark_computes_real_metrics(client):
    """Verifies that running the recommendation benchmark yields valid non-zero metrics."""
    client.post("/api/jobs/seed")
    client.post("/api/search/embed-all")

    db = SessionLocal()
    try:
        metrics = run_recommendation_evaluation(db)
        assert metrics.sample_size >= 4
        assert metrics.precision_at_3 > 0.0
        assert metrics.recall_at_5 > 0.0
        assert metrics.mrr > 0.0
        assert metrics.ndcg_at_5 > 0.0
    finally:
        db.close()


def test_agent_benchmark_accuracy():
    """Verifies agent tool routing accuracy calculation."""
    metrics = run_agent_evaluation()
    assert metrics.tool_selection_accuracy >= 0.8
    assert metrics.tool_execution_success_rate == 1.0
    assert metrics.avg_response_latency_ms >= 0.0


def test_evaluation_api_summary_endpoint(client):
    """Test GET /api/evaluations/summary returns complete system health report."""
    response = client.get("/api/evaluations/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    assert data["overall_health_score"] > 50.0
    assert "recommendation_evaluation" in data
    assert "agent_evaluation" in data
    assert "rag_evaluation" in data
    assert len(data["notes"]) >= 2
