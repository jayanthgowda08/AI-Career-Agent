"""
api/jobs.py — Job Listings API Endpoints

Provides:
- GET  /api/jobs          : Paginated job listings with keyword and category filters
- GET  /api/jobs/{job_id} : Single job details
- POST /api/jobs/seed     : Seed database with sample jobs
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.job import JobResponse, JobListResponse, JobFilterParams
from app.services.job_service import get_jobs, get_job_by_id, seed_jobs_from_file

router = APIRouter()


@router.get(
    "",
    response_model=JobListResponse,
    summary="List job opportunities with filtering and pagination",
)
def list_jobs(
    keyword: Optional[str] = Query(None, description="Search term for title, company, or description"),
    location: Optional[str] = Query(None, description="Filter by location (e.g. 'Remote', 'San Francisco')"),
    employment_type: Optional[str] = Query(None, description="Filter by 'Full-time', 'Internship', etc."),
    experience_level: Optional[str] = Query(None, description="Filter by 'Entry-level', 'Mid-level', 'Senior'"),
    min_years: Optional[int] = Query(None, description="Maximum required years of experience"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Retrieves paginated job listings.
    Supports structured SQL filtering on location, experience, and employment type,
    as well as text search across titles and descriptions.
    """
    filters = JobFilterParams(
        keyword=keyword,
        location=location,
        employment_type=employment_type,
        experience_level=experience_level,
        min_years=min_years,
        page=page,
        page_size=page_size,
    )
    jobs, total = get_jobs(db, filters)
    return JobListResponse(
        total=total,
        page=page,
        page_size=page_size,
        jobs=jobs,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get single job details by UUID",
)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieves full details of a specific job listing."""
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )
    return job


@router.post(
    "/seed",
    summary="Seed sample jobs from data/sample_jobs.json (Idempotent)",
)
def seed_jobs(
    db: Session = Depends(get_db),
):
    """
    Loads data/sample_jobs.json into PostgreSQL.
    Safely updates existing jobs or creates new ones.
    """
    created, updated = seed_jobs_from_file(db)
    return {
        "message": "Sample jobs seeded successfully.",
        "created_count": created,
        "updated_count": updated,
    }
