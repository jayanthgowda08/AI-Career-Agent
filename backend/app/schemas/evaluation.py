"""
schemas/evaluation.py — Pydantic Schemas for System Evaluation Metrics & Reports
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RecommendationMetrics(BaseModel):
    """Information Retrieval (IR) metrics for job recommendations."""
    precision_at_1: float = Field(..., description="Precision@1 (0.0 to 1.0)")
    precision_at_3: float = Field(..., description="Precision@3 (0.0 to 1.0)")
    precision_at_5: float = Field(..., description="Precision@5 (0.0 to 1.0)")
    recall_at_3: float = Field(..., description="Recall@3 (0.0 to 1.0)")
    recall_at_5: float = Field(..., description="Recall@5 (0.0 to 1.0)")
    mrr: float = Field(..., description="Mean Reciprocal Rank (0.0 to 1.0)")
    ndcg_at_3: float = Field(..., description="Normalized Discounted Cumulative Gain@3 (0.0 to 1.0)")
    ndcg_at_5: float = Field(..., description="Normalized Discounted Cumulative Gain@5 (0.0 to 1.0)")
    sample_size: int = Field(..., description="Number of evaluated candidate personas")


class LLMAgentMetrics(BaseModel):
    """Quality and performance metrics for the LangGraph LLM Agent."""
    tool_selection_accuracy: float = Field(..., description="Accuracy of routing prompts to correct tools (0.0 to 1.0)")
    tool_execution_success_rate: float = Field(..., description="Percentage of tool executions completing without error")
    structured_output_validity: float = Field(..., description="Percentage of LLM outputs passing Pydantic validation")
    avg_response_latency_ms: float = Field(..., description="Average end-to-end response latency in milliseconds")
    total_agent_turns_evaluated: int


class RAGGroundednessMetrics(BaseModel):
    """Factual groundedness and citation quality metrics for RAG."""
    context_recall: float = Field(..., description="Proportion of expected ground-truth keywords retrieved in context")
    citation_precision: float = Field(..., description="Percentage of citations pointing to genuinely relevant sources")
    hallucination_rate: float = Field(..., description="Percentage of generated statements unsupported by context")
    test_cases_evaluated: int


class SystemEvaluationReport(BaseModel):
    """Comprehensive system-wide evaluation benchmark report."""
    timestamp: str
    status: str
    recommendation_evaluation: RecommendationMetrics
    agent_evaluation: LLMAgentMetrics
    rag_evaluation: RAGGroundednessMetrics
    overall_health_score: float = Field(..., description="Composite system health score (0 to 100)")
    notes: List[str] = Field(default_factory=list)
