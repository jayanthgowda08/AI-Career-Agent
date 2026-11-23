"""
agents/graph.py — LangGraph State Machine & Orchestration

Orchestrates the ReAct agent loop using the NEW google-genai SDK (v3.6.1):
1. Agent Node: Sends conversation + tool definitions to Gemini.
2. Router: Determines whether Gemini called a tool or provided a final answer.
3. Tool Execution Node: Executes requested tools in Python and appends results.
4. Stopping condition: Exits when final answer is generated OR iteration count >= 8.

IMPORTANT:
- Uses the new `google.genai` SDK, NOT `google.generativeai`.
- Tools are passed as Python callables to `GenerativeModel(tools=...)`.
- Model fallback: primary → gemini-2.0-flash → gemini-1.5-flash on 429/503.
- LangGraph edges connect agent → (tools_node | END).
"""

import json
from typing import Dict, Any, List, Optional
from loguru import logger
from langgraph.graph import StateGraph, END

from app.config import settings
from app.agents.state import CareerAgentState
from app.agents.tools import TOOL_REGISTRY, CAREER_AGENT_TOOLS

# -----------------------------------------------------------------------
# SDK Initialization — new google-genai SDK only
# -----------------------------------------------------------------------
try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
    logger.info("graph.py: Using google-genai SDK.")
except ImportError:
    _GENAI_AVAILABLE = False
    logger.error("graph.py: google-genai SDK not found! Agent graph will not function.")

def _make_genai_client() -> "genai.Client":
    """Create a Gemini client with v1beta endpoint (required for tool use + JSON mode)."""
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"api_version": "v1beta"},
    )

# Maximum tool-calling steps per turn to avoid infinite loops
MAX_ITERATIONS = 8

# Model fallback chain — based on verified availability for this API key:
# ✅ gemini-3.5-flash      (v1beta + v1)
# ✅ gemini-3.5-flash-lite (v1beta + v1)
# ✅ gemini-3.1-flash-lite (v1beta only)
# ⚠️ gemini-3.8-flash     (503 overload — try last)
_AGENT_MODEL_FALLBACK = [
    settings.gemini_model,        # Primary from .env → gemini-3.5-flash
    "gemini-3.5-flash-lite",      # Lighter, same quality
    "gemini-3.1-flash-lite",      # v1beta-only emergency fallback
    "gemini-3.8-flash",           # Last resort (often 503)
]

# De-duplicate while preserving order
_seen = set()
_AGENT_MODEL_FALLBACK = [m for m in _AGENT_MODEL_FALLBACK if not (m in _seen or _seen.add(m))]


AGENT_SYSTEM_PROMPT = (
    "You are an expert AI Career Agent, Senior Technical Recruiter, and Career Coach assisting a job seeker. "
    "You have access to 10 specialized tools to query real database listings, search internal guides, "
    "perform live web lookups, compare jobs, analyze skill gaps, and manage bookmarks:\n\n"
    "DATABASE & PLATFORM TOOLS:\n"
    "- search_jobs: Search job listings with keywords and location filters.\n"
    "- get_job_details: Retrieve complete job requirements and descriptions.\n"
    "- compare_jobs: Compare two roles side-by-side.\n"
    "- analyse_skill_gap: Discover which skills the candidate has vs missing for a target job.\n"
    "- recommend_jobs: Get personalized recommendations scored for this candidate.\n"
    "- save_job: Bookmark a job for the candidate.\n"
    "- get_saved_jobs: List bookmarked jobs.\n"
    "- update_candidate_preferences: Modify target roles or locations.\n\n"
    "KNOWLEDGE & EXTERNAL RESEARCH TOOLS:\n"
    "- search_career_knowledge_base: Query our curated platform guide, technical resume optimization rules, "
    "system design interview prep, STAR behavioral questions, negotiation playbooks, and career transition pathways.\n"
    "- live_web_search: Search the live web using Google Search grounding for real-time hiring trends, "
    "2025/2026 salary bands, company news, and new technology standards.\n\n"
    "CRITICAL RULES:\n"
    "1. Always use your tools to retrieve real data. NEVER invent job titles, companies, or salary ranges.\n"
    "2. If the user asks general questions about this platform, resumes, interviews, or career advice, "
    "ALWAYS call 'search_career_knowledge_base'.\n"
    "3. If the user asks about current market trends, company culture, salary statistics, or recent tech news, "
    "call 'live_web_search'.\n"
    "4. If the user asks for recommendations, call 'recommend_jobs'.\n"
    "5. Format all answers with clear markdown headers, bold terms, and structured bullet points.\n"
    "6. Keep responses highly actionable, insightful, and encouraging."
)


def _build_thinking_config() -> Optional[Any]:
    """
    Safely creates a ThinkingConfig disabling reasoning tokens (thinking_budget=0 or minimal)
    to prevent 'Function call is missing a thought_signature in functionCall parts'.
    Inspects model fields dynamically so it never throws a Pydantic extra_forbidden ValidationError.
    """
    if not _GENAI_AVAILABLE or not hasattr(genai_types, "ThinkingConfig"):
        return None
    try:
        fields = getattr(genai_types.ThinkingConfig, "model_fields", {})
        kwargs = {}
        if "thinking_budget" in fields:
            kwargs["thinking_budget"] = 0
        elif "thinking_level" in fields:
            kwargs["thinking_level"] = "minimal"
        if "include_thoughts" in fields:
            kwargs["include_thoughts"] = False
        if kwargs:
            return genai_types.ThinkingConfig(**kwargs)
    except Exception as e:
        logger.warning(f"Could not initialize ThinkingConfig: {e}")
    return None


def _call_gemini_with_tools(model_name: str, full_prompt: str) -> Optional[Any]:
    """
    Try calling Gemini with tool definitions using the new genai SDK.
    Returns the response object or raises an exception.
    """
    client = _make_genai_client()
    tc = _build_thinking_config()
    cfg_kwargs = {"thinking_config": tc} if tc else {}

    # Build a GenerativeModel with tools
    model = client.chats.create(
        model=model_name,
        config=genai_types.GenerateContentConfig(
            system_instruction=AGENT_SYSTEM_PROMPT,
            tools=CAREER_AGENT_TOOLS,
            temperature=0.3,
            **cfg_kwargs,
        ),
    )
    response = model.send_message(full_prompt)
    return response


def agent_node(state: CareerAgentState) -> Dict[str, Any]:
    """
    Agent Node: Calls Gemini with available tools and gets next action or final response.
    Implements multi-model fallback chain (primary → gemini-3.5-flash-lite → ...).
    """
    if not _GENAI_AVAILABLE:
        return {
            "final_response": "AI service is unavailable: google-genai SDK not installed.",
            "status": "error",
            "iterations": state.get("iterations", 0) + 1,
        }

    iteration = state.get("iterations", 0) + 1
    logger.info(f"🤖 Agent Node deliberation — iteration {iteration}")

    context_prefix = f"[Candidate User ID: {state['user_id']}]\n"
    full_prompt = context_prefix + state["current_message"]

    response = None
    last_error = None
    chat_session = None
    tc = _build_thinking_config()
    cfg_kwargs = {"thinking_config": tc} if tc else {}

    for model_name in _AGENT_MODEL_FALLBACK:
        try:
            logger.info(f"Agent trying model: {model_name}")
            client = _make_genai_client()
            chat = client.chats.create(
                model=model_name,
                config=genai_types.GenerateContentConfig(
                    system_instruction=AGENT_SYSTEM_PROMPT,
                    tools=CAREER_AGENT_TOOLS,
                    temperature=0.3,
                    **cfg_kwargs,
                ),
            )
            response = chat.send_message(full_prompt)
            chat_session = chat
            logger.info(f"✅ Agent got response from model: {model_name}")
            break
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Model {model_name} failed in agent_node: {err_str[:200]}")
            last_error = e
            # Continue fallback for retriable or model-specific errors
            if any(code in err_str for code in ["429", "503", "404", "UNAVAILABLE", "quota", "thought_signature", "INVALID_ARGUMENT"]):
                continue
            else:
                break  # Non-retriable error (e.g. bad API key) — stop immediately

    if response is None:
        return {
            "final_response": f"I encountered an error connecting to the AI model: {str(last_error)}",
            "status": "error",
            "iterations": iteration,
        }

    # Extract any tools executed during the chat (e.g. via Automatic Function Calling)
    auto_tools_called = []
    if chat_session:
        try:
            for turn in chat_session.get_history():
                for part in (getattr(turn, "parts", None) or []):
                    fn_call = getattr(part, "function_call", None)
                    if fn_call and fn_call.name:
                        auto_tools_called.append({
                            "tool_name": fn_call.name,
                            "arguments": dict(fn_call.args or {}),
                            "result_summary": "Executed via Gemini agent session",
                        })
        except Exception as hist_err:
            logger.debug(f"Could not extract tool history: {hist_err}")

    # Inspect response — check for pending function call
    try:
        candidate = response.candidates[0]
        # In new SDK, parts may be FunctionCall objects
        for part in candidate.content.parts:
            fn_call = getattr(part, "function_call", None)
            if fn_call and fn_call.name:
                tool_name = fn_call.name
                tool_args = dict(fn_call.args) if fn_call.args else {}
                logger.info(f"🛠️ Gemini called tool: {tool_name} with args {tool_args}")

                # Inject user_id/candidate_id if Gemini left them blank
                if tool_name in ["recommend_jobs", "analyse_skill_gap"]:
                    if not tool_args.get("candidate_id"):
                        tool_args["candidate_id"] = state["user_id"]
                if tool_name in ["save_job", "get_saved_jobs", "update_candidate_preferences"]:
                    if not tool_args.get("user_id"):
                        tool_args["user_id"] = state["user_id"]

                return {
                    "status": "tool_call",
                    "pending_tool": {"name": tool_name, "args": tool_args},
                    "iterations": iteration,
                    "tools_called": list(state.get("tools_called", []) or []) + auto_tools_called,
                }

        # No pending function call — extract text answer
        text_answer = response.text or "I have processed your request."
        logger.info("✅ Agent generated final textual answer.")
        return {
            "final_response": text_answer,
            "status": "finished",
            "iterations": iteration,
            "tools_called": list(state.get("tools_called", []) or []) + auto_tools_called,
        }
    except Exception as e:
        logger.error(f"❌ Failed to parse Gemini response: {e}")
        # Try to get text as fallback
        try:
            text = response.text or "I processed your request but encountered a formatting issue."
            return {
                "final_response": text,
                "status": "finished",
                "iterations": iteration,
                "tools_called": list(state.get("tools_called", []) or []) + auto_tools_called,
            }
        except Exception:
            return {
                "final_response": "An unexpected error occurred while processing the AI response.",
                "status": "error",
                "iterations": iteration,
            }


def tools_node(state: CareerAgentState) -> Dict[str, Any]:
    """
    Tool Execution Node: Invokes the Python tool function and feeds result back to Gemini
    for a synthesized, conversational answer.
    """
    pending = state.get("pending_tool", {})
    tool_name = pending.get("name") if pending else None
    tool_args = pending.get("args", {}) if pending else {}

    logger.info(f"⚡ Executing tool '{tool_name}' with args: {tool_args}")
    func = TOOL_REGISTRY.get(tool_name)

    if not func:
        result_str = json.dumps({"error": f"Tool '{tool_name}' is not recognized."})
    else:
        try:
            result_str = func(**tool_args)
        except Exception as e:
            logger.error(f"❌ Error during tool execution '{tool_name}': {e}")
            result_str = json.dumps({"error": f"Tool execution failed: {str(e)}"})

    # Record tool call in state
    tools_called = list(state.get("tools_called", []) or [])
    tools_called.append({
        "tool_name": tool_name,
        "arguments": tool_args,
        "result_summary": result_str[:300],
    })

    # Synthesize a natural language answer from tool output using Gemini
    synthesis_prompt = (
        f"The candidate asked: '{state['current_message']}'\n\n"
        f"You called the tool '{tool_name}' which returned the following real data:\n"
        f"{result_str}\n\n"
        "Please synthesize this into a helpful, well-formatted, conversational response. "
        "Use markdown headers and bullet points. Include specific details (titles, companies, "
        "match scores, required skills). Do NOT invent any information not in the tool output."
    )

    final_answer = None
    for model_name in _AGENT_MODEL_FALLBACK:
        try:
            client = _make_genai_client()
            tc = _build_thinking_config()
            cfg_kwargs = {"thinking_config": tc} if tc else {}
            resp = client.models.generate_content(
                model=model_name,
                contents=synthesis_prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.3,
                    **cfg_kwargs,
                ),
            )
            final_answer = resp.text
            logger.info(f"✅ Synthesis complete via {model_name}")
            break
        except Exception as e:
            logger.warning(f"Synthesis model {model_name} failed: {e}")
            continue

    if not final_answer:
        final_answer = f"Here is what I found:\n\n{result_str}"

    return {
        "final_response": final_answer,
        "tools_called": tools_called,
        "status": "finished",
        "pending_tool": None,
    }


def should_continue(state: CareerAgentState) -> str:
    """
    Routing edge:
    - 'tool_call' + under max iterations → go to tools_node
    - Otherwise → END
    """
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        logger.warning("⚠️ Max iterations reached. Forcing termination.")
        return "end"

    if state.get("status") == "tool_call":
        return "tools_node"

    return "end"


# ============================================================
# Build and Compile the LangGraph
# ============================================================
def create_career_agent_graph():
    """Compiles the LangGraph StateGraph for the career agent."""
    graph = StateGraph(CareerAgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools_node", tools_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools_node": "tools_node",
            "end": END,
        },
    )

    # After tool execution, go to END (single-action turn model)
    graph.add_edge("tools_node", END)

    return graph.compile()


# Singleton compiled graph (created at import time)
career_agent_executor = create_career_agent_graph()
