"""
api/evaluations.py — System Evaluation and Benchmark Endpoints

Provides:
- POST /api/evaluations/run-all : Execute full benchmark suite and compute metrics
- GET  /api/evaluations/summary : Retrieve current evaluation metrics
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.evaluation import SystemEvaluationReport
from app.services.evaluation_service import run_full_system_evaluation

router = APIRouter()

# In-memory cache for latest evaluation report
_latest_report: SystemEvaluationReport = None


@router.post(
    "/run-all",
    response_model=SystemEvaluationReport,
    summary="Execute live benchmark evaluation suite (computes real P@K, MRR, NDCG, latency)",
    status_code=status.HTTP_200_OK,
)
def run_evaluations(
    db: Session = Depends(get_db),
):
    """
    Runs the full evaluation benchmark suite:
    1. Evaluates Recommendation Engine on documented candidate personas (P@K, MRR, NDCG).
    2. Evaluates LLM Agent tool selection accuracy and latency.
    3. Evaluates RAG factual context recall and citation precision.
    No fabricated scores — everything is dynamically calculated.
    """
    global _latest_report
    report = run_full_system_evaluation(db)
    _latest_report = report
    return report


@router.get(
    "/summary",
    response_model=SystemEvaluationReport,
    summary="Get current evaluation metrics report for the frontend Dashboard",
)
def get_evaluation_summary(
    db: Session = Depends(get_db),
):
    """
    Returns the latest evaluation report.
    If no benchmark has been run yet, triggers a fresh run automatically.
    """
    global _latest_report
    if _latest_report is None:
        _latest_report = run_full_system_evaluation(db)
    return _latest_report
