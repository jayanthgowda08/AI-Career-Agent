"""
models/rag_chunk.py — SQLAlchemy RAG Document Chunk Model (pgvector)

Stores chunked text passages and their 384-dimensional dense embeddings
from career guidance documents, resume tips, and interview prep articles.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

from app.database import Base


class RAGChunk(Base):
    """
    RAG knowledge base table with 384-dim vector embeddings for semantic retrieval.
    """
    __tablename__ = "rag_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    source_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), default="guide", index=True)  # 'guide', 'job', 'resume'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 384-dimensional vector from all-MiniLM-L6-v2
    embedding = mapped_column(Vector(384), nullable=False)
    
    metadata_fields: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
