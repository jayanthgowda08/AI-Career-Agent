"""
models/profile.py — SQLAlchemy Candidate Profile Model

Stores rich, structured candidate profile details including skills, experience,
education, and job search preferences.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class CandidateProfile(Base):
    """
    Detailed candidate profile. Linked 1-to-1 with a User.
    Uses JSONB for flexible nested data (skills, experience, education, preferences).
    """
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Basic Info
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Structured Profile Attributes (JSONB)
    skills: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    experience: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    education: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Job Preferences
    preferred_roles: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    preferred_locations: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    employment_types: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )  # e.g., ["Full-time", "Remote", "Contract"]
    career_interests: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # Raw resume text extracted from upload (Phase 4)
    raw_resume_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    # Reverse relationship to User
    user: Mapped["User"] = relationship("User", back_populates="profile")
