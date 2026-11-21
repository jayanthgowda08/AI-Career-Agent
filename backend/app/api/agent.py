"""
api/agent.py — AI Career Agent Chat and Saved Jobs Endpoints

Provides:
- POST   /api/agent/chat             : Conversational chat with tool calling
- GET    /api/agent/saved-jobs       : List candidate's saved/bookmarked jobs
- POST   /api/agent/saved-jobs/{id}  : Bookmark a job
- DELETE /api/agent/saved-jobs/{id}  : Remove a bookmark
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.saved_job import SavedJob
from app.schemas.job import JobResponse
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    ToolCallRecord,
    SavedJobResponse,
)
from app.services.auth_service import get_current_user
from app.agents.career_agent import run_career_agent
from app.services.memory_service import (
    save_conversation_turn,
    get_session_history,
    extract_and_update_persistent_preferences,
)

router = APIRouter()


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="Chat with the LLM-powered AI Career Agent (with autonomous tool calling & persistent memory)",
)
def agent_chat(
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits a conversational message to the LangGraph AI Career Agent:
    1. Loads previous conversation memory from PostgreSQL if not supplied.
    2. Runs LangGraph state machine with tools.
    3. Persists conversation turn in short-term PostgreSQL memory.
    4. Automatically extracts and persists candidate preferences into long-term profile.
    5. Returns grounded answer with tools executed.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # 1. Fetch previous history from memory if empty in request
    if request.conversation_history:
        history = [m.model_dump() for m in request.conversation_history]
    else:
        history = get_session_history(db, current_user.id, session_id, limit=10)

    # 2. Run LangGraph agent
    response_text, tools_used, referenced_jobs = run_career_agent(
        user_id=current_user.id,
        message=request.message,
        conversation_history=history,
        db=db,
    )

    # 3. Save conversation turn to PostgreSQL memory (safely)
    try:
        save_conversation_turn(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            user_message=request.message,
            assistant_response=response_text,
        )
    except Exception as mem_err:
        logger.warning(f"Could not persist session message turn: {mem_err}")

    # 4. Extract and update long-term persistent preferences (safely)
    try:
        extract_and_update_persistent_preferences(
            db=db,
            user_id=current_user.id,
            user_message=request.message,
        )
    except Exception as pref_err:
        logger.warning(f"Could not update persistent preferences: {pref_err}")

    formatted_tools = [
        ToolCallRecord(
            tool_name=tc.get("tool_name", "unknown"),
            arguments=tc.get("arguments", {}),
            result_summary=tc.get("result_summary"),
        )
        for tc in tools_used
    ]

    return AgentChatResponse(
        message=response_text,
        tools_used=formatted_tools,
        referenced_jobs=referenced_jobs,
        session_id=session_id,
    )


@router.get(
    "/saved-jobs",
    response_model=List[SavedJobResponse],
    summary="Get all bookmarked jobs for the authenticated user",
)
def get_saved_jobs_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all opportunities bookmarked by the user."""
    records = db.query(SavedJob).filter(SavedJob.user_id == current_user.id).order_by(SavedJob.saved_at.desc()).all()
    results = []
    for r in records:
        if r.job:
            results.append(
                SavedJobResponse(
                    id=r.id,
                    job=JobResponse.model_validate(r.job),
                    saved_at=r.saved_at.strftime("%Y-%m-%d %H:%M"),
                )
            )
    return results


@router.post(
    "/saved-jobs/{job_id}",
    summary="Bookmark a job by UUID",
    status_code=status.HTTP_201_CREATED,
)
def bookmark_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Saves a job to the candidate's account."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )

    existing = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id, SavedJob.job_id == job_id
    ).first()
    if existing:
        return {"message": "Job is already saved.", "job_id": str(job_id)}

    new_saved = SavedJob(user_id=current_user.id, job_id=job_id)
    db.add(new_saved)
    db.commit()
    return {"message": f"Saved '{job.title}' to your bookmarks.", "job_id": str(job_id)}


@router.delete(
    "/saved-jobs/{job_id}",
    summary="Remove a bookmarked job",
    status_code=status.HTTP_200_OK,
)
def remove_saved_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Removes a job from bookmarks."""
    record = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id, SavedJob.job_id == job_id
    ).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job was not in your saved list.",
        )
    db.delete(record)
    db.commit()
    return {"message": "Job removed from saved list."}
