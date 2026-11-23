"""
services/recommendation_service.py — Personalized Recommendation Pipeline

Coordinates:
1. Profile embedding generation.
2. Candidate job retrieval from pgvector.
3. Multi-factor re-ranking and skill gap analysis.
"""

import uuid
from typing import List, Optional
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_embedding import JobEmbedding
from app.models.profile import CandidateProfile
from app.schemas.job import JobResponse
from app.schemas.recommendation import (
    JobRecommendationResponse,
    SkillGapAnalysisResponse,
)
from app.services.embedding_service import embed_text
from app.services.semantic_search import ensure_all_jobs_embedded
from app.services.ranking_service import (
    calculate_match_score,
    analyze_skill_overlap,
)


def build_candidate_profile_text(profile: CandidateProfile) -> str:
    """Creates a comprehensive text representation of a candidate for embedding."""
    parts = []
    if profile.headline:
        parts.append(f"Professional Headline: {profile.headline}")
    if profile.preferred_roles:
        parts.append(f"Target Roles: {', '.join(profile.preferred_roles)}")
    if profile.skills:
        parts.append(f"Skills: {', '.join(profile.skills)}")
    if profile.bio:
        parts.append(f"Summary: {profile.bio}")
    if profile.career_interests:
        parts.append(f"Career Interests: {', '.join(profile.career_interests)}")
    if profile.raw_resume_text:
        parts.append(f"Resume Excerpt:\n{profile.raw_resume_text[:1000]}")
    
    return "\n".join(parts) if parts else "Software Developer looking for opportunities."


def get_personalized_recommendations(
    db: Session,
    user_id: uuid.UUID,
    top_k: int = 10,
    min_match_score: int = 20,
) -> List[JobRecommendationResponse]:
    """
    Returns personalized, ranked job recommendations for a candidate.
    """
    # 1. Fetch Candidate Profile
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        logger.warning(f"No profile found for user {user_id}, returning general jobs.")
        # Fallback to recent jobs if profile doesn't exist
        jobs = db.query(Job).limit(top_k).all()
        return [
            JobRecommendationResponse(
                job=JobResponse.model_validate(j),
                match_score=50,
                matching_skills=[],
                missing_skills=j.required_skills,
                match_reasons=["General listing (complete your profile for personalized scores)"],
                score_breakdown={
                    "skill_score": 0.5,
                    "semantic_score": 0.5,
                    "role_score": 0.5,
                    "location_score": 0.5,
                    "experience_score": 0.5,
                },
            )
            for j in jobs
        ]

    # 2. Ensure all jobs have embeddings
    ensure_all_jobs_embedded(db)

    # 3. Create candidate vector embedding
    cand_text = build_candidate_profile_text(profile)
    cand_vector = embed_text(cand_text)

    # 4. Stage 1: Fast pgvector retrieval of candidate pool (top 30 jobs)
    candidates = []
    try:
        distance_col = JobEmbedding.embedding.cosine_distance(cand_vector).label("distance")
        stmt = (
            select(Job, distance_col)
            .join(JobEmbedding, Job.id == JobEmbedding.job_id)
            .order_by("distance")
            .limit(30)
        )
        candidates = db.execute(stmt).all()
    except Exception as vec_err:
        logger.warning(f"Vector retrieval note: {vec_err}")

    # Fallback if no vector embeddings exist: rank directly against database jobs using multi-factor logic
    if not candidates:
        all_jobs = db.query(Job).limit(top_k * 2).all()
        direct_recs: List[JobRecommendationResponse] = []
        for job in all_jobs:
            match_score, breakdown, matching, missing, reasons = calculate_match_score(
                job=job,
                profile=profile,
                semantic_similarity=0.3,
            )
            # Strictly enforce min_match_score — no artificial score inflation
            if match_score >= min_match_score:
                direct_recs.append(
                    JobRecommendationResponse(
                        job=JobResponse.model_validate(job),
                        match_score=match_score,
                        matching_skills=matching,
                        missing_skills=missing,
                        match_reasons=reasons,
                        score_breakdown=breakdown,
                    )
                )
        direct_recs.sort(key=lambda r: r.match_score, reverse=True)
        return direct_recs[:top_k]

    # 5. Stage 2: Fine-grained multi-factor ranking
    recommendations: List[JobRecommendationResponse] = []
    for job, distance in candidates:
        semantic_sim = max(0.0, min(1.0, 1.0 - float(distance)))
        
        match_score, breakdown, matching, missing, reasons = calculate_match_score(
            job=job,
            profile=profile,
            semantic_similarity=semantic_sim,
        )

        # Strictly enforce min_match_score
        if match_score >= min_match_score:
            recommendations.append(
                JobRecommendationResponse(
                    job=JobResponse.model_validate(job),
                    match_score=match_score,
                    matching_skills=matching,
                    missing_skills=missing,
                    match_reasons=reasons,
                    score_breakdown=breakdown,
                )
            )

    # 6. Sort descending by true match score
    recommendations.sort(key=lambda r: r.match_score, reverse=True)
    return recommendations[:top_k]


def analyze_candidate_skill_gap(
    db: Session,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> SkillGapAnalysisResponse:
    """
    Performs detailed skill gap analysis between a candidate and a specific job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job with ID '{job_id}' not found.")

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    skills = profile.skills if profile else []

    matching, missing_req, missing_pref, skill_score = analyze_skill_overlap(
        skills, job.required_skills, job.preferred_skills
    )

    # Actionable suggestions
    suggestions = []
    if missing_req:
        suggestions.append(f"Consider learning or adding projects in: {', '.join(missing_req[:3])}.")
    if missing_pref:
        suggestions.append(f"Optional differentiator skills: {', '.join(missing_pref[:3])}.")
    if not missing_req:
        suggestions.append("You have 100% of the core required skills! Tailor your resume to highlight them.")

    match_percentage = int(round(skill_score * 100))

    return SkillGapAnalysisResponse(
        job_id=job.id,
        job_title=job.title,
        company=job.company,
        match_score=match_percentage,
        matching_skills=matching,
        missing_required_skills=missing_req,
        missing_preferred_skills=missing_pref,
        recommendations_for_improvement=suggestions,
    )
