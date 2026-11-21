"""
schemas/job.py — Pydantic Schemas for Job Management
"""

import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobBase(BaseModel):
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location or 'Remote'")
    employment_type: str = Field(default="Full-time", description="Full-time, Part-time, Contract, Internship")
    experience_level: str = Field(default="Mid-level", description="Entry-level, Mid-level, Senior, Lead")
    min_years_experience: int = Field(default=0, ge=0)
    description: str = Field(..., description="Complete job description")
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    salary_range: Optional[str] = None
    application_url: Optional[str] = None
    external_id: Optional[str] = None
    posted_date: Optional[date] = None


class JobCreate(JobBase):
    """Schema for inserting a new job."""
    pass


class JobResponse(JobBase):
    """Schema for returned job listing."""
    id: uuid.UUID
    posted_date: date
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """Paginated list of jobs."""
    total: int
    page: int
    page_size: int
    jobs: List[JobResponse]


class JobFilterParams(BaseModel):
    """Optional search query parameters."""
    keyword: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    min_years: Optional[int] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
