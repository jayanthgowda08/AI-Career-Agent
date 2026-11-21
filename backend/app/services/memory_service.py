"""
services/memory_service.py — Conversational Memory & Preference Persistence

Manages:
1. Short-term session message logging in PostgreSQL.
2. User-isolated conversation history retrieval.
3. Automatic extraction and persistence of candidate preferences into CandidateProfile.
"""

import re
import uuid
from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy.orm import Session

from app.models.memory import ConversationMessage
from app.models.profile import CandidateProfile


def save_conversation_turn(
    db: Session,
    user_id: uuid.UUID,
    session_id: str,
    user_message: str,
    assistant_response: str,
) -> None:
    """
    Saves both the user's message and the assistant's response to the database.
    """
    turn_user = ConversationMessage(
        user_id=user_id,
        session_id=session_id,
        role="user",
        content=user_message,
    )
    turn_assistant = ConversationMessage(
        user_id=user_id,
        session_id=session_id,
        role="assistant",
        content=assistant_response,
    )
    db.add(turn_user)
    db.add(turn_assistant)
    db.commit()
    logger.debug(f"Saved conversation turn for user {user_id} in session '{session_id}'.")


def get_session_history(
    db: Session,
    user_id: uuid.UUID,
    session_id: str,
    limit: int = 20,
) -> List[Dict[str, str]]:
    """
    Retrieves the last N messages for a given user and session.
    Guarantees user isolation: only messages belonging to user_id are returned.
    """
    messages = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.user_id == user_id,
            ConversationMessage.session_id == session_id,
        )
        .order_by(ConversationMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in messages]


def clear_session_history(
    db: Session,
    user_id: uuid.UUID,
    session_id: str,
) -> int:
    """Deletes all messages for a specific session."""
    deleted = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.user_id == user_id,
            ConversationMessage.session_id == session_id,
        )
        .delete()
    )
    db.commit()
    return deleted


def extract_and_update_persistent_preferences(
    db: Session,
    user_id: uuid.UUID,
    user_message: str,
) -> Optional[Dict[str, Any]]:
    """
    Heuristically extracts stated preferences from conversational turns
    and updates the candidate's persistent CandidateProfile.
    
    Examples detected:
    - 'I want remote jobs' -> adds 'Remote' to preferred_locations
    - 'I am looking for AI Engineer roles' -> adds 'AI Engineer' to preferred_roles
    """
    text = user_message.lower()
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        return None

    changes = {}

    # 1. Location preference detection
    if "remote" in text and "remote" not in [loc.lower() for loc in profile.preferred_locations]:
        profile.preferred_locations = list(set(profile.preferred_locations + ["Remote"]))
        changes["preferred_locations"] = profile.preferred_locations

    locations = ["new york", "san francisco", "seattle", "austin", "boston", "chicago", "london"]
    for city in locations:
        if city in text and city not in [loc.lower() for loc in profile.preferred_locations]:
            cap_city = city.title()
            profile.preferred_locations = list(set(profile.preferred_locations + [cap_city]))
            changes["preferred_locations"] = profile.preferred_locations

    # 2. Role preference detection
    role_patterns = [
        r"(?:looking for|interested in|want to be a|target(?:ing)?)\s+([a-zA-Z\s]+?)(?:roles?|jobs?|positions?|$)",
    ]
    for pattern in role_patterns:
        match = re.search(pattern, text)
        if match:
            extracted_role = match.group(1).strip().title()
            if len(extracted_role) > 3 and extracted_role not in profile.preferred_roles:
                profile.preferred_roles = list(set(profile.preferred_roles + [extracted_role]))
                changes["preferred_roles"] = profile.preferred_roles

    if changes:
        db.commit()
        logger.info(f"💾 Automatically persisted user preferences for {user_id}: {changes}")
        return changes

    return None
