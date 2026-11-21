"""
schemas/search.py — Pydantic Schemas for Semantic and Hybrid Search
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.job import JobResponse


class SemanticSearchRequest(BaseModel):
    """Payload for natural language semantic search."""
    query: str = Field(..., min_length=2, description="Natural language search query")
    location: Optional[str] = Field(None, description="Optional location filter")
    employment_type: Optional[str] = Field(None, description="Optional employment type filter")
    experience_level: Optional[str] = Field(None, description="Optional experience level filter")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class ScoredJobResponse(BaseModel):
    """Job result annotated with similarity and ranking score."""
    job: JobResponse
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    semantic_score: Optional[float] = None
    keyword_score: Optional[float] = None
    match_reasons: List[str] = Field(default_factory=list)


class SearchResultsResponse(BaseModel):
    """Wrapper response for search results."""
    query: str
    search_type: str  # "semantic" or "hybrid"
    total_results: int
    results: List[ScoredJobResponse]
