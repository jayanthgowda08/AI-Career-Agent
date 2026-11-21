"""
api/recommendations.py — Personalised Recommendation Endpoints

Provides:
- GET /api/recommendations                 : Current candidate's personalized recommendations
- GET /api/recommendations/skill-gap/{id}  : Skill gap analysis for a target job
- GET /api/recommendations/candidate/{id}  : Recommendations for a specific candidate ID
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationListResponse,
    SkillGapAnalysisResponse,
)
from app.services.auth_service import get_current_user
from app.services.recommendation_service import (
    get_personalized_recommendations,
    analyze_candidate_skill_gap,
)

router = APIRouter()


@router.get(
    "",
    response_model=RecommendationListResponse,
    summary="Get personalized job recommendations for currently authenticated user",
)
def get_recommendations(
    top_k: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    min_score: int = Query(20, ge=0, le=100, description="Minimum match percentage"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ranks jobs specifically for the authenticated user using:
    - Skill overlap (Jaccard match ratio)
    - Semantic profile embedding similarity (pgvector)
    - Preferred job role relevance
    - Location preference and Remote compatibility
    - Experience compatibility
    """
    results = get_personalized_recommendations(
        db=db,
        user_id=current_user.id,
        top_k=top_k,
        min_match_score=min_score,
    )
    return RecommendationListResponse(
        candidate_id=current_user.id,
        total_recommendations=len(results),
        recommendations=results,
    )


@router.get(
    "/candidate/{candidate_id}",
    response_model=RecommendationListResponse,
    summary="Get recommendations for a specific candidate ID (used by AI Agent tools)",
)
def get_recommendations_for_candidate(
    candidate_id: uuid.UUID,
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Candidate-specific recommendation endpoint.
    Called directly by the AI Career Agent tools during conversation.
    """
    results = get_personalized_recommendations(
        db=db,
        user_id=candidate_id,
        top_k=top_k,
    )
    return RecommendationListResponse(
        candidate_id=candidate_id,
        total_recommendations=len(results),
        recommendations=results,
    )


@router.get(
    "/skill-gap/{job_id}",
    response_model=SkillGapAnalysisResponse,
    summary="Analyze skill gaps between current user and a target job",
)
def get_skill_gap(
    job_id: uuid.UUID,
    candidate_id: Optional[uuid.UUID] = Query(None, description="Optional override candidate ID for Agent tool"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compares the candidate's skills with the job requirements.
    Identifies matching skills, missing required skills, and provides
    actionable improvement suggestions.
    """
    target_user_id = candidate_id or current_user.id
    try:
        gap_analysis = analyze_candidate_skill_gap(
            db=db,
            user_id=target_user_id,
            job_id=job_id,
        )
        return gap_analysis
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )
