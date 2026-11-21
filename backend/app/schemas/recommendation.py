"""
schemas/recommendation.py — Pydantic Schemas for Recommendations & Skill Gap Analysis
"""

import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.job import JobResponse


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown across all ranking dimensions (each 0.0 to 1.0)."""
    skill_score: float = Field(..., description="Proportion of job skills matched by candidate")
    semantic_score: float = Field(..., description="Vector embedding similarity between profile and job")
    role_score: float = Field(..., description="Relevance of job title to candidate's preferred roles")
    location_score: float = Field(..., description="Location compatibility (including Remote)")
    experience_score: float = Field(..., description="Experience level and years compatibility")


class JobRecommendationResponse(BaseModel):
    """A personalized job recommendation item with explainable scores and skills."""
    job: JobResponse
    match_score: int = Field(..., ge=0, le=100, description="Overall match percentage (0 - 100%)")
    matching_skills: List[str] = Field(default_factory=list, description="Skills candidate has that the job requires")
    missing_skills: List[str] = Field(default_factory=list, description="Skills the job requires that candidate lacks")
    match_reasons: List[str] = Field(default_factory=list, description="Human-readable reasons for recommendation")
    score_breakdown: ScoreBreakdown


class RecommendationListResponse(BaseModel):
    """Paginated list of personalized recommendations."""
    candidate_id: uuid.UUID
    total_recommendations: int
    recommendations: List[JobRecommendationResponse]


class SkillGapAnalysisResponse(BaseModel):
    """In-depth skill gap analysis between a candidate and a specific job."""
    job_id: uuid.UUID
    job_title: str
    company: str
    match_score: int
    matching_skills: List[str]
    missing_required_skills: List[str]
    missing_preferred_skills: List[str]
    recommendations_for_improvement: List[str]
