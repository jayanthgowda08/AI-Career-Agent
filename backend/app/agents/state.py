"""
agents/state.py — LangGraph Career Agent State Definition
"""

from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class CareerAgentState(TypedDict):
    """
    Mutable state passed across nodes in the LangGraph career agent graph.
    """
    user_id: str                      # Current candidate UUID as string
    messages: List[Dict[str, Any]]    # Full conversation history formatted for LLM
    current_message: str              # User's newest message
    tools_called: List[Dict[str, Any]]# Log of executed tools with arguments and results
    final_response: str               # Grounded answer to return to user
    referenced_job_ids: List[str]     # UUIDs of jobs retrieved during execution
    iterations: int                   # Safety loop counter
    status: str                       # 'running', 'finished', 'error', 'max_iterations'
    pending_tool: Optional[Dict[str, Any]] # Tool waiting to be executed
