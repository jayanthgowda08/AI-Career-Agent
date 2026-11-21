"""
schemas/resume.py — Structured Resume Pydantic Schemas

Defines the target schema that Gemini must populate when analyzing a resume.
Every field has strict types and validation rules.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class WorkExperienceExtracted(BaseModel):
    """Extracted work experience entry."""
    company: str = Field(description="Company or organization name")
    title: str = Field(description="Job title / role")
    location: Optional[str] = Field(None, description="City, country or Remote")
    start_date: Optional[str] = Field(None, description="Start date (e.g. 'Jan 2022' or '2022-01')")
    end_date: Optional[str] = Field(None, description="End date (e.g. 'Present' or '2023-12')")
    description: Optional[str] = Field(None, description="Key responsibilities and achievements")


class EducationExtracted(BaseModel):
    """Extracted education entry."""
    institution: str = Field(description="University, college or school name")
    degree: str = Field(description="Degree or qualification (e.g. 'B.Tech', 'M.S.', 'High School')")
    field_of_study: Optional[str] = Field(None, description="Major / field of study (e.g. 'Computer Science')")
    graduation_year: Optional[int] = Field(None, description="Year of graduation if available")


class ProjectExtracted(BaseModel):
    """Extracted project entry."""
    name: str = Field(description="Project name or title")
    description: Optional[str] = Field(None, description="Summary of what the project does")
    technologies: List[str] = Field(default_factory=list, description="Technologies / languages / tools used")
    link: Optional[str] = Field(None, description="URL or GitHub repo link if present")


class ParsedResumeData(BaseModel):
    """
    Complete structured profile extracted from a candidate's resume by Gemini.
    """
    full_name: Optional[str] = Field(None, description="Candidate's full name")
    email: Optional[str] = Field(None, description="Candidate's email if found on resume")
    phone: Optional[str] = Field(None, description="Phone number if found on resume")
    location: Optional[str] = Field(None, description="Current city/state/country")
    headline: Optional[str] = Field(None, description="Professional headline or title (e.g. 'Full Stack Developer')")
    summary: Optional[str] = Field(None, description="Professional summary or bio")
    
    # Categorized skills
    technical_skills: List[str] = Field(
        default_factory=list,
        description="Programming languages, frameworks, databases, developer tools, cloud platforms",
    )
    soft_skills: List[str] = Field(
        default_factory=list,
        description="Communication, leadership, teamwork, problem-solving, etc.",
    )
    
    # Career details
    experience: List[WorkExperienceExtracted] = Field(default_factory=list)
    education: List[EducationExtracted] = Field(default_factory=list)
    projects: List[ProjectExtracted] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list, description="Professional certifications (e.g. 'AWS Certified Developer')")
    
    # Inferred preferences
    suggested_roles: List[str] = Field(
        default_factory=list,
        description="Suggested job titles based on the candidate's skills and experience",
    )


class ResumeUploadResponse(BaseModel):
    """API Response returned after resume parsing and profile updating."""
    message: str
    file_name: str
    parsed_data: ParsedResumeData
