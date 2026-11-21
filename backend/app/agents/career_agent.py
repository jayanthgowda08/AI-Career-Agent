"""
agents/career_agent.py — High-Level Agent Runner

Primary entry point called by the FastAPI API layer.
Manages session context, state initialization, and graph execution.
"""

import uuid
from typing import List, Dict, Any, Tuple
from loguru import logger
from sqlalchemy.orm import Session

from app.agents.graph import career_agent_executor
from app.agents.state import CareerAgentState
from app.schemas.job import JobResponse
from app.services.job_service import get_job_by_id


def run_career_agent(
    user_id: uuid.UUID,
    message: str,
    conversation_history: List[Dict[str, str]] = None,
    db: Session = None,
) -> Tuple[str, List[Dict[str, Any]], List[JobResponse]]:
    """
    Executes the compiled LangGraph career agent for a user message.
    Returns:
    (final_response_text, tools_used_log, referenced_jobs_list)
    """
    initial_state: CareerAgentState = {
        "user_id": str(user_id),
        "messages": conversation_history or [],
        "current_message": message,
        "tools_called": [],
        "final_response": "",
        "referenced_job_ids": [],
        "iterations": 0,
        "status": "running",
        "pending_tool": None,  # Required field — holds tool name+args between agent→tools_node
    }

    logger.info(f"🚀 Invoking Career Agent for user {user_id}: '{message[:80]}...'")
    try:
        final_state = career_agent_executor.invoke(initial_state)
        response_text = final_state.get(
            "final_response",
            "I have processed your request. Let me know if you would like me to search or compare opportunities.",
        )
        tools_used = final_state.get("tools_called", [])
    except Exception as e:
        logger.error(f"❌ Error during LangGraph agent execution: {e}")
        # Graceful fallback: return clear diagnostic message
        response_text = (
            f"I encountered an issue executing your request via Gemini: {str(e)}\n\n"
            "Tip: Please check that your GEMINI_API_KEY in backend/.env is a valid Google AI Studio key "
            "(typically starts with 'AIzaSy...')."
        )
        tools_used = []

    # Extract any job IDs referenced during tool calls
    referenced_jobs: List[JobResponse] = []
    if db:
        for tool_call in tools_used:
            args = tool_call.get("arguments", {})
            for key in ["job_id", "job_id_1", "job_id_2"]:
                if key in args and args[key]:
                    try:
                        jid = uuid.UUID(str(args[key]))
                        job = get_job_by_id(db, jid)
                        if job and not any(rj.id == job.id for rj in referenced_jobs):
                            referenced_jobs.append(JobResponse.model_validate(job))
                    except Exception:
                        pass

    return response_text, tools_used, referenced_jobs
