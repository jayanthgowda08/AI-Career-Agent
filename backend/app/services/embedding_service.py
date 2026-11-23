"""
services/embedding_service.py — Text Embedding Service

Uses Google Gemini Embedding API ('gemini-embedding-001') to convert text into
dense 384-dimensional vector embeddings for semantic search and RAG.
Runs with zero local RAM footprint (< 10MB) to stay well under Render's 512MB RAM limit.
"""

from typing import List, Union
from functools import lru_cache
import numpy as np
from loguru import logger
from app.config import settings

# Embedding model specification (384 dimensions matches pgvector Vector(384))
MODEL_NAME = "gemini-embedding-001"
EMBEDDING_DIM = 384

try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


def _get_genai_client():
    if not _GENAI_AVAILABLE or not settings.gemini_api_key:
        return None
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"api_version": "v1beta"},
    )


def embed_text(text: str) -> List[float]:
    """
    Converts a single string into a 384-dimensional float vector.
    Normalizes the vector to unit length for fast cosine similarity.
    """
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIM

    client = _get_genai_client()
    if client:
        try:
            resp = client.models.embed_content(
                model=MODEL_NAME,
                contents=text.strip(),
                config=genai_types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
            )
            vec = resp.embeddings[0].values
            return list(vec)
        except Exception as e:
            logger.warning(f"Gemini embed_content failed: {e}. Falling back to local SentenceTransformer.")

    # Lazy-load SentenceTransformer as emergency fallback
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        vector = model.encode(text.strip(), normalize_embeddings=True)
        return vector.tolist()
    except Exception as e:
        logger.error(f"Fallback embedding failed: {e}")
        return [0.0] * EMBEDDING_DIM


def embed_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Batch encodes multiple strings into 384-dimensional vectors efficiently.
    """
    cleaned = [t.strip() if t and t.strip() else "empty" for t in texts]
    if not cleaned:
        return []

    client = _get_genai_client()
    if client:
        try:
            resp = client.models.embed_content(
                model=MODEL_NAME,
                contents=cleaned,
                config=genai_types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
            )
            return [list(e.values) for e in resp.embeddings]
        except Exception as e:
            logger.warning(f"Gemini batch embed failed: {e}. Falling back to local SentenceTransformer.")

    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        vectors = model.encode(cleaned, batch_size=batch_size, normalize_embeddings=True)
        return vectors.tolist()
    except Exception as e:
        logger.error(f"Fallback batch embedding failed: {e}")
        return [[0.0] * EMBEDDING_DIM for _ in cleaned]


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Computes cosine similarity between two float vectors: (A . B) / (||A|| * ||B||).
    """
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
