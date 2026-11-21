"""
schemas/__init__.py — Expose all Pydantic schemas
"""

from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    Token,
    TokenPayload,
    UserResponse,
)
from app.schemas.profile import (
    ExperienceItem,
    EducationItem,
    CandidateProfileUpdate,
    CandidateProfileResponse,
)

from app.schemas.job import (
    JobCreate,
    JobResponse,
    JobListResponse,
    JobFilterParams,
)

from app.schemas.search import (
    SemanticSearchRequest,
    ScoredJobResponse,
    SearchResultsResponse,
)

from app.schemas.recommendation import (
    ScoreBreakdown,
    JobRecommendationResponse,
    RecommendationListResponse,
    SkillGapAnalysisResponse,
)

from app.schemas.agent import (
    AgentChatMessage,
    AgentChatRequest,
    ToolCallRecord,
    AgentChatResponse,
    SavedJobResponse,
)

from app.schemas.rag import (
    RAGQueryRequest,
    RAGSourceCitation,
    RAGQueryResponse,
)

from app.schemas.evaluation import (
    RecommendationMetrics,
    LLMAgentMetrics,
    RAGGroundednessMetrics,
    SystemEvaluationReport,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "Token",
    "TokenPayload",
    "UserResponse",
    "ExperienceItem",
    "EducationItem",
    "CandidateProfileUpdate",
    "CandidateProfileResponse",
    "JobCreate",
    "JobResponse",
    "JobListResponse",
    "JobFilterParams",
    "SemanticSearchRequest",
    "ScoredJobResponse",
    "SearchResultsResponse",
    "ScoreBreakdown",
    "JobRecommendationResponse",
    "RecommendationListResponse",
    "SkillGapAnalysisResponse",
    "AgentChatMessage",
    "AgentChatRequest",
    "ToolCallRecord",
    "AgentChatResponse",
    "SavedJobResponse",
    "RAGQueryRequest",
    "RAGSourceCitation",
    "RAGQueryResponse",
    "RecommendationMetrics",
    "LLMAgentMetrics",
    "RAGGroundednessMetrics",
    "SystemEvaluationReport",
]
