"""
api/search.py — Semantic and Hybrid Search Endpoints

Provides:
- POST /api/search/semantic : Semantic vector search over job listings
- POST /api/search/hybrid   : Hybrid search combining vector + keyword matching
- POST /api/search/embed-all: Trigger vector generation for unindexed jobs
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.search import SemanticSearchRequest, SearchResultsResponse
from app.services.semantic_search import (
    search_jobs_semantic,
    search_jobs_hybrid,
    ensure_all_jobs_embedded,
)

router = APIRouter()


@router.post(
    "/semantic",
    response_model=SearchResultsResponse,
    summary="Semantic vector search using pgvector cosine similarity",
)
def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Converts query text into a dense 384-dimensional vector and runs
    cosine similarity search (<=> operator) against stored job embeddings.
    Accepts natural language queries even with differing terminology.
    """
    results = search_jobs_semantic(db, request)
    return SearchResultsResponse(
        query=request.query,
        search_type="semantic",
        total_results=len(results),
        results=results,
    )


@router.post(
    "/hybrid",
    response_model=SearchResultsResponse,
    summary="Hybrid search combining semantic similarity and keyword relevance",
)
def hybrid_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Blended Hybrid Search:
    - 60% weight: Dense vector semantic similarity via pgvector
    - 40% weight: Lexical keyword match ratio across title and description
    Combines the strengths of deep semantic understanding and exact keyword precision.
    """
    results = search_jobs_hybrid(db, request)
    return SearchResultsResponse(
        query=request.query,
        search_type="hybrid",
        total_results=len(results),
        results=results,
    )


@router.post(
    "/embed-all",
    summary="Generate vector embeddings for all unindexed jobs",
    status_code=status.HTTP_200_OK,
)
def embed_all_jobs(
    db: Session = Depends(get_db),
):
    """
    Maintenance endpoint that computes and stores vector embeddings
    for any job in the database that is missing an embedding.
    """
    embedded_count, total = ensure_all_jobs_embedded(db)
    return {
        "message": "Job embedding backfill completed.",
        "embedded_count": embedded_count,
        "total_jobs": total,
    }
