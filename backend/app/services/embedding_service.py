"""
services/embedding_service.py — Text Embedding Service

Uses SentenceTransformer ('all-MiniLM-L6-v2') to convert text into
dense 384-dimensional vector embeddings for semantic search and RAG.
Model is loaded once in memory and shared across requests.
"""

from typing import List, Union
from functools import lru_cache
import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

# Embedding model specification
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class EmbeddingModelManager:
    """Singleton wrapper for the local SentenceTransformer model."""
    _instance: "EmbeddingModelManager" = None
    _model: SentenceTransformer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingModelManager, cls).__new__(cls)
            logger.info(f"🧠 Loading embedding model: {MODEL_NAME}...")
            cls._model = SentenceTransformer(MODEL_NAME)
            logger.info(f"✅ Embedding model '{MODEL_NAME}' loaded successfully.")
        return cls._instance

    @property
    def model(self) -> SentenceTransformer:
        return self._model


@lru_cache()
def get_embedding_model() -> SentenceTransformer:
    """Returns the cached SentenceTransformer instance."""
    return EmbeddingModelManager().model


def embed_text(text: str) -> List[float]:
    """
    Converts a single string into a 384-dimensional float vector.
    Normalizes the vector to unit length for fast cosine similarity.
    """
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIM

    model = get_embedding_model()
    # normalize_embeddings=True ensures dot product equals cosine similarity
    vector = model.encode(text.strip(), normalize_embeddings=True)
    return vector.tolist()


def embed_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Batch encodes multiple strings into vectors efficiently.
    """
    cleaned = [t.strip() if t and t.strip() else "empty" for t in texts]
    model = get_embedding_model()
    vectors = model.encode(cleaned, batch_size=batch_size, normalize_embeddings=True)
    return vectors.tolist()


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
