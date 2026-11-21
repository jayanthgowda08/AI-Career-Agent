"""
services/resume_parser.py — PDF Text Extraction Service

Extracts clean, readable text from uploaded PDF resumes.
Uses pdfplumber as the primary extractor (best for formatting/tables)
with a fallback to PyMuPDF (fitz) for edge cases or complex PDFs.
"""

import io
from loguru import logger
import pdfplumber
import fitz  # PyMuPDF


class ResumeExtractionError(Exception):
    """Custom exception raised when resume text extraction fails."""
    pass


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extracts text from PDF bytes.
    1. Attempts extraction using pdfplumber.
    2. If pdfplumber yields minimal or no text, falls back to PyMuPDF (fitz).
    3. Cleans whitespace and normalizes text.
    """
    extracted_text = ""

    # Strategy 1: pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = []
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text(layout=True) or ""
                if page_text.strip():
                    pages_text.append(page_text.strip())
            extracted_text = "\n\n".join(pages_text)
            if extracted_text.strip():
                logger.info(f"📄 Successfully extracted text with pdfplumber ({len(extracted_text)} chars).")
                return clean_text(extracted_text)
    except Exception as e:
        logger.warning(f"⚠️ pdfplumber failed ({e}), falling back to PyMuPDF...")

    # Strategy 2: PyMuPDF (fitz) fallback
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_text = []
        for page in doc:
            page_text = page.get_text("text") or ""
            if page_text.strip():
                pages_text.append(page_text.strip())
        extracted_text = "\n\n".join(pages_text)
        if extracted_text.strip():
            logger.info(f"📄 Successfully extracted text with PyMuPDF ({len(extracted_text)} chars).")
            return clean_text(extracted_text)
    except Exception as e:
        logger.error(f"❌ PyMuPDF extraction also failed: {e}")
        raise ResumeExtractionError(f"Failed to extract text from PDF: {str(e)}")

    if not extracted_text.strip():
        raise ResumeExtractionError(
            "The uploaded PDF contains no readable text. It might be a scanned image or empty. "
            "Please upload a text-based PDF."
        )

    return clean_text(extracted_text)


def clean_text(text: str) -> str:
    """Removes excessive blank lines and trailing whitespace."""
    lines = [line.strip() for line in text.splitlines()]
    # Collapse multiple consecutive empty lines into one
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned_lines.append("")
                prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False
    return "\n".join(cleaned_lines).strip()
