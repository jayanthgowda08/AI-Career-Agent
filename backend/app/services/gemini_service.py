"""
services/gemini_service.py — Google Gemini AI Integration Service

Provides structured extraction, career reasoning, and LLM completions.
Uses the new google-genai SDK configured with api_version='v1beta'
and gemini-2.5-flash for fast, reliable JSON generation.
"""

import concurrent.futures
import time
from loguru import logger
from pydantic import ValidationError

from app.config import settings
from app.schemas.resume import ParsedResumeData

# Timeout (seconds) for any single Gemini API call
GEMINI_TIMEOUT_SECONDS = 30

# Max resume text chars sent to Gemini (~12k chars ≈ 3k tokens)
MAX_RESUME_CHARS = 12_000

# ---------------------------------------------------------------------------
# SDK import & initialization
# ---------------------------------------------------------------------------
try:
    from google import genai
    from google.genai import types as genai_types
    _NEW_SDK = True
    logger.info("Using google-genai SDK.")
except ImportError:
    import google.generativeai as genai_legacy
    _NEW_SDK = False
    logger.warning("Falling back to legacy google-generativeai SDK.")

# Configure SDK with v1beta endpoint (required for JSON mode on gemini-2.5-flash)
if settings.gemini_api_key and settings.gemini_api_key != "your-gemini-api-key-here":
    if _NEW_SDK:
        _client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options={"api_version": "v1beta"}
        )
    else:
        genai_legacy.configure(api_key=settings.gemini_api_key)
        _client = None
    logger.info("🤖 Google Gemini API configured successfully with v1beta.")
else:
    _client = None
    logger.warning("⚠️ GEMINI_API_KEY is not configured or using default placeholder.")


class GeminiServiceError(Exception):
    """Custom exception for Gemini AI service failures."""
    pass


# ---------------------------------------------------------------------------
# JSON schema string for prompt injection
# ---------------------------------------------------------------------------
_RESUME_SCHEMA_STR = """
{
  "full_name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "location": "string or null",
  "headline": "string or null",
  "summary": "string or null",
  "technical_skills": ["list of strings"],
  "soft_skills": ["list of strings"],
  "experience": [
    {
      "company": "string",
      "title": "string",
      "location": "string or null",
      "start_date": "string or null",
      "end_date": "string or null",
      "description": "string or null"
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "field_of_study": "string or null",
      "graduation_year": "integer or null"
    }
  ],
  "projects": [
    {
      "name": "string",
      "description": "string or null",
      "technologies": ["list of strings"],
      "link": "string or null"
    }
  ],
  "certifications": ["list of strings"],
  "suggested_roles": ["3 to 5 job title strings"]
}
"""

_SYSTEM_PROMPT = (
    "You are an expert AI Resume Analyst and Senior Technical Recruiter. "
    "Your task is to analyze the provided resume text and extract all relevant candidate "
    "information into a structured JSON object.\n\n"
    "Instructions:\n"
    "1. Extract candidate name, contact details, and location if present.\n"
    "2. Identify all technical skills (languages, frameworks, libraries, tools, clouds, databases).\n"
    "3. Identify soft skills (e.g. teamwork, communication, problem solving).\n"
    "4. Extract work experience chronologically with clear job titles, company names, and descriptions.\n"
    "5. Extract degrees, institutions, and graduation years.\n"
    "6. Extract projects with names, descriptions, and technologies used.\n"
    "7. Suggest 3 to 5 realistic job titles that match this candidate's profile.\n"
    "8. Do NOT invent or hallucinate information that is not in the resume.\n\n"
    "IMPORTANT: Return ONLY a valid JSON object — no markdown fences, no commentary.\n"
    f"The JSON MUST match this exact schema:\n{_RESUME_SCHEMA_STR}"
)


def _strip_fences(text: str) -> str:
    """Remove markdown code fences the model may add despite instructions."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(line for line in lines if not line.startswith("```")).strip()
    return text


def extract_structured_resume_with_gemini(resume_text: str) -> ParsedResumeData:
    """
    Sends raw resume text to Gemini and returns a validated ParsedResumeData object.
    Uses gemini-2.5-flash with v1beta for sub-2s responses and fast failover.
    """
    if not settings.gemini_api_key or settings.gemini_api_key == "your-gemini-api-key-here":
        raise GeminiServiceError(
            "GEMINI_API_KEY is not configured. Please set a valid Gemini API key in backend/.env"
        )

    # Truncate oversized resumes to avoid token bloat and slow responses
    if len(resume_text) > MAX_RESUME_CHARS:
        logger.warning(
            f"Resume text truncated from {len(resume_text)} to {MAX_RESUME_CHARS} chars."
        )
        resume_text = resume_text[:MAX_RESUME_CHARS]

    user_message = f"Please extract structured data from this resume text:\n\n{resume_text}"

    # Verified working models for this API key:
    # gemini-2.5-flash ✅ (stable, zero 503s), gemini-3-flash-preview ✅, gemini-3.5-flash
    models_to_try = [settings.gemini_model, "gemini-2.5-flash", "gemini-3-flash-preview", "gemini-3.5-flash"]
    # Deduplicate while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    last_error: Exception = RuntimeError("No models attempted.")

    for model_name in models_to_try:
        def _call_gemini() -> str:
            if _NEW_SDK:
                resp = _client.models.generate_content(
                    model=model_name,
                    contents=user_message,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                return resp.text
            else:
                model = genai_legacy.GenerativeModel(
                    model_name=model_name,
                    system_instruction=_SYSTEM_PROMPT,
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1,
                    },
                )
                return model.generate_content(user_message).text

        try:
            logger.info(f"Extracting resume with Gemini model: {model_name}...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_call_gemini)
                try:
                    response_text = future.result(timeout=GEMINI_TIMEOUT_SECONDS)
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Timeout ({GEMINI_TIMEOUT_SECONDS}s) with model {model_name}, trying fallback...")
                    continue

            response_text = _strip_fences(response_text)
            logger.debug(f"Gemini Raw Response: {response_text[:300]}...")

            parsed_data = ParsedResumeData.model_validate_json(response_text)
            logger.info(f"✅ Successfully parsed resume for: {parsed_data.full_name or 'Candidate'} via {model_name}")
            return parsed_data

        except ValidationError as val_err:
            logger.error(f"❌ Pydantic validation failed on {model_name} output: {val_err}")
            raise GeminiServiceError(f"Structured output schema validation failed: {str(val_err)}")
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}. Trying next fallback...")
            last_error = e
            continue

    raise GeminiServiceError(f"All Gemini models failed or timed out. Last error: {str(last_error)}")
