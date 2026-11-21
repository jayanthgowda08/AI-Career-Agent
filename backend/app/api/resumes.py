"""
api/resumes.py — Resume Upload and Analysis Endpoints

Provides:
- POST /api/resumes/upload : Upload a PDF resume, parse with Gemini, and update CandidateProfile
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.profile import CandidateProfile
from app.schemas.resume import ResumeUploadResponse
from app.services.auth_service import get_current_user
from app.services.resume_parser import extract_text_from_pdf_bytes, ResumeExtractionError
from app.services.gemini_service import extract_structured_resume_with_gemini, GeminiServiceError

router = APIRouter()


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload PDF resume, extract text, analyze with Gemini, and update profile",
)
async def upload_resume(
    file: UploadFile = File(..., description="PDF resume file (max 10MB)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Complete Resume Analysis Pipeline:
    1. Validates that the uploaded file is a PDF.
    2. Validates file size does not exceed MAX_UPLOAD_SIZE_MB.
    3. Extracts clean text using pdfplumber / PyMuPDF.
    4. Calls Gemini with structured Pydantic schema.
    5. Updates candidate profile in PostgreSQL with extracted skills and history.
    6. Returns structured profile data.
    """
    # 1. Validate File Type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF resumes are accepted.",
        )

    # 2. Read bytes and check size
    file_bytes = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb} MB.",
        )

    # 3. Save copy locally in uploads/
    safe_filename = f"{current_user.id}_{uuid.uuid4().hex[:6]}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, safe_filename)
    try:
        with open(file_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        logger.warning(f"Failed to persist copy of uploaded file locally: {e}")

    # 4. Extract text from PDF
    try:
        raw_text = extract_text_from_pdf_bytes(file_bytes)
    except ResumeExtractionError as ext_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ext_err),
        )

    # 5. Analyze with Gemini Structured Output
    try:
        parsed_resume = extract_structured_resume_with_gemini(raw_text)
    except GeminiServiceError as gem_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI Extraction failed: {str(gem_err)}",
        )

    # 6. Update user's CandidateProfile in PostgreSQL
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()

    # Apply extracted data (without overwriting fields if Gemini returned None)
    if parsed_resume.full_name:
        profile.full_name = parsed_resume.full_name
    if parsed_resume.headline:
        profile.headline = parsed_resume.headline
    if parsed_resume.summary:
        profile.bio = parsed_resume.summary
    if parsed_resume.location:
        profile.location = parsed_resume.location
    if parsed_resume.phone:
        profile.phone = parsed_resume.phone

    # Combine technical & soft skills into unique list
    all_skills = list(dict.fromkeys(parsed_resume.technical_skills + parsed_resume.soft_skills))
    if all_skills:
        profile.skills = all_skills

    # Convert experience and education to dicts for JSONB
    if parsed_resume.experience:
        profile.experience = [exp.model_dump() for exp in parsed_resume.experience]
    if parsed_resume.education:
        profile.education = [edu.model_dump() for edu in parsed_resume.education]
    if parsed_resume.suggested_roles:
        profile.preferred_roles = parsed_resume.suggested_roles

    # Store raw text for future RAG / embedding retrieval
    profile.raw_resume_text = raw_text

    db.commit()
    db.refresh(profile)

    return ResumeUploadResponse(
        message="Resume successfully uploaded, parsed by Gemini, and profile updated.",
        file_name=file.filename,
        parsed_data=parsed_resume,
    )
