"""
schemas/profile.py — Pydantic Schemas for Candidate Profile
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ExperienceItem(BaseModel):
    """Structured work experience item."""
    company: str = Field(..., json_schema_extra={"example": "TechCorp"})
    title: str = Field(..., json_schema_extra={"example": "Junior Software Engineer"})
    location: Optional[str] = Field(None, json_schema_extra={"example": "Bangalore, India"})
    start_date: Optional[str] = Field(None, json_schema_extra={"example": "2023-01"})
    end_date: Optional[str] = Field(None, json_schema_extra={"example": "Present"})
    description: Optional[str] = Field(None, json_schema_extra={"example": "Developed backend microservices using FastAPI and PostgreSQL."})


class EducationItem(BaseModel):
    """Structured education item."""
    institution: str = Field(..., json_schema_extra={"example": "National Institute of Technology"})
    degree: str = Field(..., json_schema_extra={"example": "Bachelor of Technology"})
    field_of_study: Optional[str] = Field(None, json_schema_extra={"example": "Computer Science"})
    graduation_year: Optional[int] = Field(None, json_schema_extra={"example": 2024})


class CandidateProfileUpdate(BaseModel):
    """Payload for updating candidate profile information."""
    full_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[ExperienceItem]] = None
    education: Optional[List[EducationItem]] = None
    preferred_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    employment_types: Optional[List[str]] = None
    career_interests: Optional[List[str]] = None


class CandidateProfileResponse(BaseModel):
    """Full candidate profile representation."""
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    experience: List[dict] = []
    education: List[dict] = []
    preferred_roles: List[str] = []
    preferred_locations: List[str] = []
    employment_types: List[str] = []
    career_interests: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
