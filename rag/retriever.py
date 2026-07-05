"""
RAG Retriever Module.

Uses FAISS to index and query vector embeddings of clinical guidelines.
Saves and loads indices and maps IDs to text chunks.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import faiss
import numpy as np

from config.settings import settings
from rag.embedder import get_embeddings, get_embedding

logger = logging.getLogger(__name__)


class ClinicalRetriever:
    """Manages the FAISS index and metadata for clinical guideline search."""

    def __init__(self, index_path: Optional[str] = None):
        self.index_path = Path(index_path or settings.rag_faiss_index_path)
        self.index_file = self.index_path / "index.faiss"
        self.meta_file = self.index_path / "metadata.json"
        
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: list[dict[str, Any]] = []
        
        self.load_index()

    def load_index(self) -> bool:
        """Load the FAISS index and metadata from disk."""
        if not self.index_file.exists() or not self.meta_file.exists():
            logger.info("[Retriever] FAISS index or metadata files do not exist yet on disk.")
            return False

        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_file))
            # Load metadata mapping
            with open(self.meta_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            logger.info(f"[Retriever] Loaded index with {self.index.ntotal} vectors from {self.index_path}")
            return True
        except Exception as e:
            logger.error(f"[Retriever] Failed to load FAISS index: {e}")
            return False

    def build_index(self, chunks: list[str], source_name: str) -> None:
        """
        Embed chunks and build a new FAISS index, overwriting any existing index.

        Args:
            chunks: List of guideline text chunks.
            source_name: Name of the source file/document.
        """
        if not chunks:
            logger.warning("[Retriever] Cannot build index: no text chunks provided.")
            return

        logger.info(f"[Retriever] Embedding {len(chunks)} chunks for source: {source_name}...")
        embeddings_list = get_embeddings(chunks)
        embeddings_np = np.array(embeddings_list, dtype=np.float32)

        # Normalise vectors for cosine similarity (Inner Product on normalized vectors)
        faiss.normalize_L2(embeddings_np)
        dimension = embeddings_np.shape[1]

        # Initialize flat inner-product index
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings_np)

        # Build metadata list
        self.metadata = [
            {"id": i, "text": chunk, "source": source_name}
            for i, chunk in enumerate(chunks)
        ]

        # Save to disk
        self._save_to_disk()

    def append_to_index(self, chunks: list[str], source_name: str) -> None:
        """
        Add new document chunks to an existing FAISS index.

        Args:
            chunks: List of guideline text chunks.
            source_name: Name of the source document.
        """
        if self.index is None:
            self.build_index(chunks, source_name)
            return

        if not chunks:
            return

        logger.info(f"[Retriever] Appending {len(chunks)} chunks to existing index...")
        embeddings_list = get_embeddings(chunks)
        embeddings_np = np.array(embeddings_list, dtype=np.float32)
        faiss.normalize_L2(embeddings_np)

        start_id = len(self.metadata)
        self.index.add(embeddings_np)

        # Append to metadata
        for i, chunk in enumerate(chunks):
            self.metadata.append({
                "id": start_id + i,
                "text": chunk,
                "source": source_name
            })

        self._save_to_disk()

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """
        Query the FAISS index for matching clinical guideline chunks.

        Args:
            query: Clinical query string.
            top_k: Max results to return.

        Returns:
            List of dicts representing matched guideline passages.
        """
        if self.index is None or not self.metadata:
            logger.warning("[Retriever] Search requested, but FAISS index is empty.")
            return []

        # Embed query vector
        query_emb = np.array([get_embedding(query)], dtype=np.float32)
        faiss.normalize_L2(query_emb)

        # Search index
        scores, indices = self.index.search(query_emb, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx].copy()
            meta["similarity_score"] = float(score)
            results.append(meta)

        return results

    def _save_to_disk(self) -> None:
        """Helper to serialize FAISS index and metadata to disk."""
        try:
            self.index_path.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self.index_file))
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"[Retriever] Successfully saved index and metadata to {self.index_path}")
        except Exception as e:
            logger.error(f"[Retriever] Failed to save FAISS files to disk: {e}")
