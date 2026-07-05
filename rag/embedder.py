"""
RAG Embedder Module.

Handles loading of sentence-transformer models and generating embeddings
for document chunks and queries.
"""
from __future__ import annotations

import logging
from typing import Optional

from sentence_transformers import SentenceTransformer

from config.settings import settings

logger = logging.getLogger(__name__)

_EMBEDDER: Optional[SentenceTransformer] = None


def get_embedder_model() -> SentenceTransformer:
    """Get or load the singleton SentenceTransformer instance."""
    global _EMBEDDER
    if _EMBEDDER is None:
        model_name = settings.rag_embedding_model or "sentence-transformers/all-MiniLM-L6-v2"
        logger.info(f"[Embedder] Loading sentence-transformer model: {model_name}...")
        try:
            # sentence-transformers defaults model download to cache directory
            _EMBEDDER = SentenceTransformer(model_name)
            logger.info("[Embedder] Model loaded successfully.")
        except Exception as e:
            logger.error(f"[Embedder] Failed to load model {model_name}: {e}")
            raise
    return _EMBEDDER


def get_embedding(text: str) -> list[float]:
    """
    Generate a dense vector embedding for a single text string.

    Args:
        text: Input string.

    Returns:
        List of floats representing the embedding vector.
    """
    model = get_embedder_model()
    embeddings = model.encode([text], convert_to_numpy=True)
    return embeddings[0].tolist()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate dense vector embeddings for a list of text strings.

    Args:
        texts: List of input strings.

    Returns:
        List of lists of floats.
    """
    if not texts:
        return []
    model = get_embedder_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()
