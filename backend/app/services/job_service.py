"""
services/job_service.py — Job Ingestion & Management Service

Handles:
- Idempotent ingestion of job listings from JSON/dict data.
- Paginated querying with structured filters.
- Detailed single-job retrieval.
"""

import json
import os
import uuid
from datetime import date
from typing import List, Optional, Tuple
from loguru import logger
from sqlalchemy import or_, select, func
from sqlalchemy.orm import Session

from app.models.job import Job
from app.schemas.job import JobCreate, JobFilterParams


def seed_jobs_from_file(db: Session, file_path: str = "data/sample_jobs.json") -> Tuple[int, int]:
    """
    Reads sample jobs from file and inserts or updates them in PostgreSQL.
    Returns (created_count, updated_count).
    """
    # Locate file relative to current directory or project root
    candidates = [
        file_path,
        os.path.join("..", file_path),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", file_path),
    ]
    target_path = None
    for path in candidates:
        if os.path.exists(path):
            target_path = path
            break

    if not target_path:
        logger.error(f"❌ Sample jobs file not found at: {file_path}")
        return 0, 0

    with open(target_path, "r", encoding="utf-8") as f:
        job_data_list = json.load(f)

    return ingest_jobs_list(db, job_data_list)


def ingest_jobs_list(db: Session, job_data_list: List[dict]) -> Tuple[int, int]:
    """
    Idempotently ingests a list of job dicts.
    Matches by external_id or (title + company) to prevent duplicates.
    """
    created_count = 0
    updated_count = 0

    for raw_job in job_data_list:
        job_create = JobCreate.model_validate(raw_job)

        # Check for existing job by external_id or title+company
        existing_job = None
        if job_create.external_id:
            existing_job = db.query(Job).filter(Job.external_id == job_create.external_id).first()
        if not existing_job:
            existing_job = (
                db.query(Job)
                .filter(Job.title == job_create.title, Job.company == job_create.company)
                .first()
            )

        if existing_job:
            # Update fields
            existing_job.location = job_create.location
            existing_job.employment_type = job_create.employment_type
            existing_job.experience_level = job_create.experience_level
            existing_job.min_years_experience = job_create.min_years_experience
            existing_job.description = job_create.description
            existing_job.required_skills = job_create.required_skills
            existing_job.preferred_skills = job_create.preferred_skills
            existing_job.salary_range = job_create.salary_range
            existing_job.application_url = job_create.application_url
            if job_create.posted_date:
                existing_job.posted_date = job_create.posted_date
            updated_count += 1
        else:
            # Insert new job
            new_job = Job(
                external_id=job_create.external_id,
                title=job_create.title,
                company=job_create.company,
                location=job_create.location,
                employment_type=job_create.employment_type,
                experience_level=job_create.experience_level,
                min_years_experience=job_create.min_years_experience,
                description=job_create.description,
                required_skills=job_create.required_skills,
                preferred_skills=job_create.preferred_skills,
                salary_range=job_create.salary_range,
                application_url=job_create.application_url,
                posted_date=job_create.posted_date or date.today(),
            )
            db.add(new_job)
            created_count += 1

    db.commit()
    logger.info(f"✅ Ingestion complete: {created_count} created, {updated_count} updated.")
    return created_count, updated_count


def get_jobs(
    db: Session,
    filters: JobFilterParams,
) -> Tuple[List[Job], int]:
    """
    Retrieves a paginated list of jobs matching optional filter parameters.
    Returns (jobs_list, total_count).
    """
    query = select(Job)

    # Keyword filter across title, company, description
    if filters.keyword:
        kw = f"%{filters.keyword}%"
        query = query.where(
            or_(
                Job.title.ilike(kw),
                Job.company.ilike(kw),
                Job.description.ilike(kw),
            )
        )

    # Location filter (e.g., 'San Francisco', 'Remote')
    if filters.location:
        query = query.where(Job.location.ilike(f"%{filters.location}%"))

    # Employment type filter
    if filters.employment_type:
        query = query.where(Job.employment_type.ilike(filters.employment_type))

    # Experience level filter
    if filters.experience_level:
        query = query.where(Job.experience_level.ilike(filters.experience_level))

    # Max years of experience filter
    if filters.min_years is not None:
        query = query.where(Job.min_years_experience <= filters.min_years)

    # Get total count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    # Apply pagination and sorting (newest first)
    offset = (filters.page - 1) * filters.page_size
    query = query.order_by(Job.posted_date.desc(), Job.created_at.desc()).offset(offset).limit(filters.page_size)

    jobs = db.scalars(query).all()
    return list(jobs), total


def get_job_by_id(db: Session, job_id: uuid.UUID) -> Optional[Job]:
    """Retrieves a single job by its UUID."""
    return db.query(Job).filter(Job.id == job_id).first()
