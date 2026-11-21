"""
schemas/agent.py — Pydantic Schemas for AI Career Agent Interaction
"""

import uuid
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from app.schemas.job import JobResponse


class AgentChatMessage(BaseModel):
    """Single message in conversation history."""
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text")


class AgentChatRequest(BaseModel):
    """User message sent to the AI Career Agent."""
    message: str = Field(..., min_length=1, description="Candidate's natural language message or query")
    session_id: Optional[str] = Field(None, description="Optional conversation session identifier")
    conversation_history: List[AgentChatMessage] = Field(
        default_factory=list,
        description="Previous turns for short-term conversational context",
    )


class ToolCallRecord(BaseModel):
    """Record of a tool invocation during agent deliberation."""
    tool_name: str
    arguments: Dict[str, Any]
    result_summary: Optional[str] = None


class AgentChatResponse(BaseModel):
    """Agent response returned to the frontend."""
    message: str = Field(..., description="Agent's final grounded answer to the candidate")
    tools_used: List[ToolCallRecord] = Field(default_factory=list, description="Tools invoked during this turn")
    referenced_jobs: List[JobResponse] = Field(default_factory=list, description="Jobs specifically discussed or retrieved")
    session_id: str


class SavedJobResponse(BaseModel):
    """A saved job record with full job details."""
    id: uuid.UUID
    job: JobResponse
    saved_at: str
