"""
agents/tools.py — The 8 Concrete AI Career Agent Tools

Each tool is:
1. Documented with clear docstrings explaining when to use it.
2. Accepts primitive JSON-serializable parameters (strings, ints, lists).
3. Self-manages its database session internally so Pydantic/Gemini never inspects Session.
4. Returns sanitized JSON-string results suitable for LLM reasoning.
"""

import json
import uuid
from typing import Optional, Dict, Any, List
from loguru import logger

from app.database import SessionLocal
from app.models.job import Job
from app.models.saved_job import SavedJob
from app.models.profile import CandidateProfile
from app.schemas.search import SemanticSearchRequest
from app.services.job_service import get_job_by_id
from app.services.semantic_search import search_jobs_hybrid
from app.services.recommendation_service import (
    get_personalized_recommendations,
    analyze_candidate_skill_gap,
)


# ============================================================
# Tool 1: search_jobs
# ============================================================
def search_jobs(query: str) -> str:
    """
    Search relevant job opportunities using hybrid semantic and keyword retrieval.
    Use this when the user asks to find jobs, search for roles, or explore openings.
    query: Search query string containing desired role, skills, or location (e.g. 'python developer remote')
    """
    db = SessionLocal()
    try:
        req = SemanticSearchRequest(
            query=query,
            top_k=5,
        )
        results = search_jobs_hybrid(db, req)
        output = [
            {
                "id": str(r.job.id),
                "title": r.job.title,
                "company": r.job.company,
                "location": r.job.location,
                "salary_range": r.job.salary_range,
                "required_skills": r.job.required_skills,
                "similarity_score": f"{int(r.similarity_score * 100)}%",
                "snippet": r.job.description[:250] + "...",
            }
            for r in results
        ]
        return json.dumps({"jobs_found": len(output), "results": output})
    finally:
        db.close()


# ============================================================
# Tool 2: get_job_details
# ============================================================
def get_job_details(job_id: str) -> str:
    """
    Retrieve full detailed information about a selected job by its ID.
    Use this when the candidate asks for more information about a specific opportunity.
    """
    db = SessionLocal()
    try:
        try:
            job_uuid = uuid.UUID(job_id)
        except ValueError:
            return json.dumps({"error": f"Invalid job ID format: '{job_id}'"})

        job = get_job_by_id(db, job_uuid)
        if not job:
            return json.dumps({"error": f"No job found with ID '{job_id}'"})

        return json.dumps({
            "id": str(job.id),
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "employment_type": job.employment_type,
            "experience_level": job.experience_level,
            "min_years_experience": job.min_years_experience,
            "salary_range": job.salary_range,
            "required_skills": job.required_skills,
            "preferred_skills": job.preferred_skills,
            "application_url": job.application_url,
            "description": job.description,
        })
    finally:
        db.close()


# ============================================================
# Tool 3: compare_jobs
# ============================================================
def compare_jobs(job_id_1: str, job_id_2: str) -> str:
    """
    Compare two job opportunities side by side based on skills, experience,
    location, salary, and requirements.
    """
    db = SessionLocal()
    try:
        try:
            u1 = uuid.UUID(job_id_1)
            u2 = uuid.UUID(job_id_2)
        except ValueError:
            return json.dumps({"error": "Invalid UUID format for one of the job IDs"})

        j1 = get_job_by_id(db, u1)
        j2 = get_job_by_id(db, u2)

        if not j1 or not j2:
            return json.dumps({"error": "One or both jobs could not be found"})

        shared_skills = list(set(j1.required_skills).intersection(set(j2.required_skills)))

        return json.dumps({
            "job_1": {
                "id": str(j1.id),
                "title": j1.title,
                "company": j1.company,
                "location": j1.location,
                "salary": j1.salary_range,
                "experience_required": f"{j1.min_years_experience} years ({j1.experience_level})",
                "unique_skills": [s for s in j1.required_skills if s not in j2.required_skills],
            },
            "job_2": {
                "id": str(j2.id),
                "title": j2.title,
                "company": j2.company,
                "location": j2.location,
                "salary": j2.salary_range,
                "experience_required": f"{j2.min_years_experience} years ({j2.experience_level})",
                "unique_skills": [s for s in j2.required_skills if s not in j1.required_skills],
            },
            "shared_skills": shared_skills,
        })
    finally:
        db.close()


# ============================================================
# Tool 4: analyse_skill_gap
# ============================================================
def analyse_skill_gap(job_id: str, candidate_id: str) -> str:
    """
    Analyze skill gaps between candidate and a target job.
    Identifies matching skills, missing required skills, and gives advice.
    """
    db = SessionLocal()
    try:
        try:
            j_uuid = uuid.UUID(job_id)
            c_uuid = uuid.UUID(candidate_id)
        except ValueError:
            return json.dumps({"error": "Invalid UUID format"})

        analysis = analyze_candidate_skill_gap(db, c_uuid, j_uuid)
        return json.dumps({
            "job_title": analysis.job_title,
            "company": analysis.company,
            "match_score": f"{analysis.match_score}%",
            "matching_skills": analysis.matching_skills,
            "missing_required_skills": analysis.missing_required_skills,
            "missing_preferred_skills": analysis.missing_preferred_skills,
            "recommendations": analysis.recommendations_for_improvement,
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


# ============================================================
# Tool 5: recommend_jobs
# ============================================================
def recommend_jobs(candidate_id: str) -> str:
    """
    Retrieve personalized job recommendations for the candidate based on
    their profile skills, experience, and preferences.
    """
    db = SessionLocal()
    try:
        try:
            c_uuid = uuid.UUID(candidate_id)
        except ValueError:
            return json.dumps({"error": "Invalid candidate UUID"})

        recs = get_personalized_recommendations(db, c_uuid, top_k=5)
        output = [
            {
                "id": str(r.job.id),
                "title": r.job.title,
                "company": r.job.company,
                "location": r.job.location,
                "match_score": f"{r.match_score}%",
                "matching_skills": r.matching_skills,
                "reasons": r.match_reasons,
            }
            for r in recs
        ]
        return json.dumps({"recommendations_count": len(output), "jobs": output})
    finally:
        db.close()


# ============================================================
# Tool 6: save_job
# ============================================================
def save_job(user_id: str, job_id: str) -> str:
    """
    Save or bookmark a job opportunity to the candidate's personal account.
    """
    db = SessionLocal()
    try:
        try:
            u_uuid = uuid.UUID(user_id)
            j_uuid = uuid.UUID(job_id)
        except ValueError:
            return json.dumps({"error": "Invalid UUID format"})

        job = get_job_by_id(db, j_uuid)
        if not job:
            return json.dumps({"error": f"Job with ID '{job_id}' does not exist"})

        existing = db.query(SavedJob).filter(
            SavedJob.user_id == u_uuid, SavedJob.job_id == j_uuid
        ).first()

        if existing:
            return json.dumps({"status": "already_saved", "message": f"'{job.title}' at {job.company} is already in your saved jobs."})

        new_saved = SavedJob(user_id=u_uuid, job_id=j_uuid)
        db.add(new_saved)
        db.commit()
        return json.dumps({
            "status": "success",
            "message": f"Successfully saved '{job.title}' at {job.company} to your account.",
            "job_id": str(job.id),
        })
    finally:
        db.close()


# ============================================================
# Tool 7: get_saved_jobs
# ============================================================
def get_saved_jobs(user_id: str) -> str:
    """
    Retrieve all job opportunities saved/bookmarked by the candidate.
    """
    db = SessionLocal()
    try:
        try:
            u_uuid = uuid.UUID(user_id)
        except ValueError:
            return json.dumps({"error": "Invalid user UUID"})

        records = db.query(SavedJob).filter(SavedJob.user_id == u_uuid).all()
        saved_list = []
        for r in records:
            if r.job:
                saved_list.append({
                    "job_id": str(r.job.id),
                    "title": r.job.title,
                    "company": r.job.company,
                    "location": r.job.location,
                    "salary_range": r.job.salary_range,
                    "saved_at": r.saved_at.strftime("%Y-%m-%d"),
                })
        return json.dumps({"saved_count": len(saved_list), "saved_jobs": saved_list})
    finally:
        db.close()


# ============================================================
# Tool 8: update_candidate_preferences
# ============================================================
def update_candidate_preferences(
    user_id: str,
    preferred_roles: List[str],
    preferred_locations: List[str],
) -> str:
    """
    Update candidate job search preferences (roles, locations).
    Call this when the user asks to change their target roles or search criteria.
    """
    db = SessionLocal()
    try:
        try:
            u_uuid = uuid.UUID(user_id)
        except ValueError:
            return json.dumps({"error": "Invalid user UUID"})

        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == u_uuid).first()
        if not profile:
            profile = CandidateProfile(user_id=u_uuid)
            db.add(profile)
            db.flush()

        updated = []
        if preferred_roles:
            profile.preferred_roles = preferred_roles
            updated.append(f"roles: {', '.join(preferred_roles)}")
        if preferred_locations:
            profile.preferred_locations = preferred_locations
            updated.append(f"locations: {', '.join(preferred_locations)}")

        db.commit()
        return json.dumps({
            "status": "success",
            "message": f"Updated profile preferences ({'; '.join(updated)}).",
        })
    finally:
        db.close()


# ============================================================
# Tool 9: search_career_knowledge_base (RAG Tool)
# ============================================================
def search_career_knowledge_base(query: str) -> str:
    """
    Search the curated career coaching and platform knowledge base.
    Use this when the user asks questions about:
    - How to use this platform, its features, and how recommendations work
    - Resume writing best practices and formatting (Google XYZ formula, ATS)
    - System design and behavioral interview preparation (STAR method)
    - Salary and equity negotiation frameworks
    - Career transitions (e.g. into AI/LLM engineering)
    - Backend, frontend, DevOps, and microservices architecture standards
    """
    from app.services.rag_service import retrieve_relevant_chunks
    db = SessionLocal()
    try:
        chunks = retrieve_relevant_chunks(db, query, top_k=3)
        results = [
            {
                "title": c.source_title,
                "topic": c.metadata_fields.get("topic", "General") if c.metadata_fields else "General",
                "content": c.content,
                "relevance_score": f"{int(sim * 100)}%",
            }
            for c, sim in chunks
        ]
        return json.dumps({
            "knowledge_articles_found": len(results),
            "articles": results,
        })
    except Exception as e:
        logger.error(f"Error querying career knowledge base: {e}")
        return json.dumps({"error": f"Failed to retrieve knowledge: {str(e)}"})
    finally:
        db.close()


# ============================================================
# Tool 10: live_web_search (Live Web Grounding)
# ============================================================
def live_web_search(query: str) -> str:
    """
    Search the live web using Google Search grounding for real-time information.
    Use this when the user asks about:
    - Recent tech company hiring trends, layoffs, or market demand
    - Current 2025/2026 salary bands and compensation benchmarks
    - Company-specific culture, interview stages, or tech stack updates
    - Newly released frameworks, libraries, or AI tools
    - Any general career question that requires fresh external web data
    """
    from google import genai
    from google.genai import types
    from app.config import settings

    if not settings.gemini_api_key or settings.gemini_api_key == "your-gemini-api-key-here":
        return json.dumps({"error": "Gemini API key is not configured for web search."})

    try:
        client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options={"api_version": "v1beta"}
        )
        prompt = (
            f"Provide current, factual, verified information answering this career query: '{query}'. "
            "Include specific figures, current market expectations, dates, and actionable advice."
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.2,
            )
        )
        return json.dumps({
            "query": query,
            "web_summary": response.text.strip() if response.text else "No web results found."
        })
    except Exception as e:
        logger.warning(f"Live web search failed: {e}")
        return json.dumps({"error": f"Web search failed: {str(e)}"})


# ============================================================
# Registry mapping tool names to callable Python functions
# ============================================================
TOOL_REGISTRY: Dict[str, Any] = {
    "search_jobs": search_jobs,
    "get_job_details": get_job_details,
    "compare_jobs": compare_jobs,
    "analyse_skill_gap": analyse_skill_gap,
    "recommend_jobs": recommend_jobs,
    "save_job": save_job,
    "get_saved_jobs": get_saved_jobs,
    "update_candidate_preferences": update_candidate_preferences,
    "search_career_knowledge_base": search_career_knowledge_base,
    "live_web_search": live_web_search,
}

# Python list of tool callables to provide to Gemini/LangChain
CAREER_AGENT_TOOLS = list(TOOL_REGISTRY.values())
