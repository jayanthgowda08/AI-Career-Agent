"""
tests/test_resumes.py — Unit & Integration Tests for Resume Ingestion Pipeline

Run with:
    pytest app/tests/test_resumes.py -v
"""

import io
import uuid
import pytest
import fitz  # PyMuPDF to create a real test PDF in memory
from unittest.mock import patch

from app.schemas.resume import (
    ParsedResumeData,
    WorkExperienceExtracted,
    EducationExtracted,
)


@pytest.fixture
def auth_headers(client):
    """Creates a user and returns valid Authorization headers."""
    email = f"resume_tester_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "SecurePassword123!"
    res = client.post("/api/auth/register", json={"email": email, "password": pwd})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_pdf_bytes():
    """Generates a valid, minimal in-memory PDF with text using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "John Doe\n"
        "Email: johndoe@example.com | Phone: +1 555-0199\n"
        "Location: Seattle, WA\n\n"
        "Professional Summary:\n"
        "Experienced Backend Software Engineer specializing in Python, FastAPI, and PostgreSQL.\n\n"
        "Technical Skills:\n"
        "Python, FastAPI, Docker, PostgreSQL, PyTorch, Git, Redis\n\n"
        "Experience:\n"
        "Senior Developer at CloudTech (2022 - Present)\n"
        "Designed and maintained scalable microservices handling 10M daily requests.\n\n"
        "Education:\n"
        "B.S. in Computer Science, University of Washington (2020)\n",
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_upload_non_pdf_rejected(client, auth_headers):
    """Uploading a non-PDF file should return 400 Bad Request."""
    fake_txt = io.BytesIO(b"This is not a PDF file.")
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.txt", fake_txt, "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Only PDF" in response.json()["detail"]


def test_upload_unauthenticated_rejected(client):
    """Uploading without a Bearer token should return 401 Unauthorized."""
    fake_pdf = io.BytesIO(b"%PDF-1.4 dummy content")
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.pdf", fake_pdf, "application/pdf")},
    )
    assert response.status_code == 401


def test_resume_upload_and_parsing_pipeline(client, auth_headers, sample_pdf_bytes):
    """
    Tests complete pipeline:
    1. Uploads in-memory valid PDF.
    2. Mocks Gemini output with a known ParsedResumeData structure.
    3. Verifies that the endpoint returns 200 and updates CandidateProfile in PostgreSQL.
    """
    mock_gemini_output = ParsedResumeData(
        full_name="John Doe",
        email="johndoe@example.com",
        phone="+1 555-0199",
        location="Seattle, WA",
        headline="Senior Backend Engineer",
        summary="Experienced Backend Software Engineer specializing in Python and FastAPI.",
        technical_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "PyTorch"],
        soft_skills=["Communication", "Problem-solving"],
        experience=[
            WorkExperienceExtracted(
                company="CloudTech",
                title="Senior Developer",
                start_date="2022",
                end_date="Present",
                description="Designed scalable microservices.",
            )
        ],
        education=[
            EducationExtracted(
                institution="University of Washington",
                degree="B.S.",
                field_of_study="Computer Science",
                graduation_year=2020,
            )
        ],
        suggested_roles=["Backend Engineer", "Python Developer", "Cloud Engineer"],
    )

    with patch(
        "app.api.resumes.extract_structured_resume_with_gemini",
        return_value=mock_gemini_output,
    ):
        file_obj = io.BytesIO(sample_pdf_bytes)
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("john_doe_resume.pdf", file_obj, "application/pdf")},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["parsed_data"]["full_name"] == "John Doe"
        assert "FastAPI" in data["parsed_data"]["technical_skills"]

        # Now verify that candidate profile was automatically updated in PostgreSQL
        profile_res = client.get("/api/profiles/me", headers=auth_headers)
        assert profile_res.status_code == 200
        profile = profile_res.json()
        assert profile["full_name"] == "John Doe"
        assert profile["headline"] == "Senior Backend Engineer"
        assert "Python" in profile["skills"]
        assert len(profile["experience"]) == 1
        assert profile["experience"][0]["company"] == "CloudTech"
        assert profile["preferred_roles"] == ["Backend Engineer", "Python Developer", "Cloud Engineer"]
