"""
models/job.py — SQLAlchemy Job Model

Stores job listings with detailed descriptions, required skills,
experience requirements, compensation, and location.
"""

import uuid
from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy import String, Text, Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class Job(Base):
    """
    Job listing table.
    Stores structured job data and requirements.
    In Phase 6, we will attach vector embeddings to these listings.
    """
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    company: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    location: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    # Employment Type: "Full-time", "Part-time", "Contract", "Internship", "Remote"
    employment_type: Mapped[str] = mapped_column(String(100), index=True, default="Full-time")
    
    # Experience Level: "Entry-level", "Mid-level", "Senior", "Lead"
    experience_level: Mapped[str] = mapped_column(String(100), index=True, default="Mid-level")
    min_years_experience: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Required and preferred skills stored in JSONB arrays
    required_skills: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    preferred_skills: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    
    # Compensation and link
    salary_range: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    application_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Source / external reference (prevents duplicates during re-ingestion)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    
    posted_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
