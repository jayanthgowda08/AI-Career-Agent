"""
api/profiles.py — Candidate Profile Endpoints

Provides:
- GET /api/profiles/me : Retrieve current candidate profile
- PUT /api/profiles/me : Update candidate profile (skills, preferences, bio, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.profile import CandidateProfile
from app.schemas.profile import (
    CandidateProfileResponse,
    CandidateProfileUpdate,
)
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get(
    "/me",
    response_model=CandidateProfileResponse,
    summary="Get current candidate profile",
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetches the candidate profile for the logged-in user.
    If none exists, initializes an empty profile automatically.
    """
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put(
    "/me",
    response_model=CandidateProfileResponse,
    summary="Update current candidate profile",
)
def update_my_profile(
    payload: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the candidate profile attributes:
    - Basic info: full_name, headline, bio, location, phone
    - Skills array
    - Nested experience and education lists
    - Preferences: preferred_roles, locations, employment_types, career_interests
    """
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()

    # Update only fields provided in the payload (partial updates allowed)
    update_data = payload.model_dump(exclude_unset=True)

    # Convert Pydantic submodels (ExperienceItem, EducationItem) to dicts for JSONB storage
    for key, value in update_data.items():
        if isinstance(value, list) and value and hasattr(value[0], "model_dump"):
            value = [item.model_dump() for item in value]
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile
