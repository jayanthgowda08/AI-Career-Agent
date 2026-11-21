"""
api/rag.py — RAG Career Guidance and Conversation Memory Endpoints

Provides:
- POST   /api/rag/ask                  : Grounded career Q&A with citations
- POST   /api/rag/seed-knowledge-base  : Seed RAG knowledge base chunks
- GET    /api/rag/history/{session_id} : Get conversation history for a session
- DELETE /api/rag/history/{session_id} : Clear conversation session
"""

from typing import List, Dict
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse
from app.services.auth_service import get_current_user
from app.services.rag_service import answer_career_question_with_rag, seed_rag_knowledge_base
from app.services.memory_service import get_session_history, clear_session_history

router = APIRouter()


@router.post(
    "/ask",
    response_model=RAGQueryResponse,
    summary="Ask a career guidance question grounded in technical career guides",
)
def ask_career_guidance(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    RAG-powered career Q&A:
    1. Converts question into a 384-dim vector.
    2. Retrieves top relevant passages from pgvector rag_chunks.
    3. Prompts Gemini with strict context grounding.
    4. Returns grounded advice with source citations.
    """
    response = answer_career_question_with_rag(
        db=db,
        question=request.question,
        top_k=request.top_k,
    )
    return response


@router.post(
    "/seed-knowledge-base",
    summary="Seed and vectorize career guidance knowledge base",
    status_code=status.HTTP_200_OK,
)
def seed_knowledge_base(
    db: Session = Depends(get_db),
):
    """Chunks and embeds data/career_guidance_docs.json into pgvector."""
    created, total = seed_rag_knowledge_base(db)
    return {
        "message": "RAG knowledge base seeded successfully.",
        "chunks_created": created,
        "total_documents": total,
    }


@router.get(
    "/history/{session_id}",
    response_model=List[Dict[str, str]],
    summary="Retrieve short-term conversational history for a session",
)
def get_history(
    session_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns previous message turns for the current user and session."""
    return get_session_history(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        limit=limit,
    )


@router.delete(
    "/history/{session_id}",
    summary="Clear conversation history for a session",
)
def delete_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clears all short-term conversation messages for a session."""
    deleted_count = clear_session_history(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
    )
    return {"message": "Session history cleared.", "deleted_turns": deleted_count}
