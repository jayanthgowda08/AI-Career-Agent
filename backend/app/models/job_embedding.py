"""
models/job_embedding.py — SQLAlchemy Job Embedding Model (pgvector)

Stores dense 384-dimensional vector representations for job listings.
Linked 1-to-1 with the Job model.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.database import Base


class JobEmbedding(Base):
    """
    Vector embedding table for semantic similarity search.
    all-MiniLM-L6-v2 outputs 384-dimensional dense vectors.
    """
    __tablename__ = "job_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # 384-dimensional float vector column from pgvector
    embedding = mapped_column(Vector(384), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship to Job
    job = relationship("Job", backref="vector_embedding")
