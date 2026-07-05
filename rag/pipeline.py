"""
RAG Pipeline Module.

Orchestrates guideline document parsing, chunking, indexing, and context retrieval.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from config.settings import settings
from rag.retriever import ClinicalRetriever

logger = logging.getLogger(__name__)


class ClinicalRAGPipeline:
    """Orchestrates indexing of the medical corpus and context retrieval."""

    def __init__(self, corpus_path: Optional[str] = None, index_path: Optional[str] = None):
        self.corpus_path = Path(corpus_path or settings.medical_corpus_path)
        self.retriever = ClinicalRetriever(index_path)

    def initialize(self, force_rebuild: bool = False) -> None:
        """
        Scan the medical corpus directory, split documents, and build the FAISS index.
        Skip if the index already exists and force_rebuild is False.
        """
        if not force_rebuild and self.retriever.index is not None:
            logger.info("[RAG Pipeline] FAISS index loaded from disk. Skipping initialization.")
            return

        logger.info("[RAG Pipeline] Initialising medical corpus index...")
        self.corpus_path.mkdir(parents=True, exist_ok=True)

        txt_files = list(self.corpus_path.glob("*.txt"))
        if not txt_files:
            logger.warning(
                f"[RAG Pipeline] No guideline text documents found in {self.corpus_path}. "
                "Guideline retrieval will be empty until documents are added."
            )
            return

        all_chunks = []
        for file_path in txt_files:
            try:
                logger.info(f"[RAG Pipeline] Processing document: {file_path.name}...")
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                chunks = self._chunk_text(
                    content, 
                    chunk_size=settings.rag_chunk_size, 
                    overlap=settings.rag_chunk_overlap
                )
                logger.info(f"  → Generated {len(chunks)} chunks.")
                
                # Append to current run index
                self.retriever.append_to_index(chunks, file_path.name)
            except Exception as e:
                logger.error(f"[RAG Pipeline] Failed to index {file_path.name}: {e}")

        logger.info("[RAG Pipeline] Pipeline initialised and index saved.")

    def retrieve(self, query: str, top_k: Optional[int] = None) -> Optional[str]:
        """
        Retrieve matching clinical guideline passages and format them as a single context block.

        Args:
            query: Clinical search query.
            top_k: Optional top results limit.

        Returns:
            Formatted guideline string, or None if no relevant matches are found.
        """
        k = top_k or settings.rag_top_k
        matches = self.retriever.search(query, top_k=k)
        
        if not matches:
            return None

        # Filter by similarity threshold
        threshold = settings.rag_similarity_threshold
        filtered_matches = [
            m for m in matches 
            if m.get("similarity_score", 0.0) >= threshold
        ]

        if not filtered_matches:
            # Fallback to top 1 if we have matches but below threshold, for robustness
            filtered_matches = [matches[0]]

        logger.info(
            f"[RAG Pipeline] Retrieved {len(filtered_matches)} guideline passages for query: '{query}'"
        )

        formatted_passages = []
        for m in filtered_matches:
            formatted_passages.append(
                f"--- SOURCE: {m.get('source', 'Unknown')} (similarity: {m.get('similarity_score', 0.0):.2f}) ---\n"
                f"{m.get('text', '')}"
            )

        return "\n\n".join(formatted_passages)

    def add_document(self, content: str, source_name: str) -> None:
        """
        Parse and add a new guideline text document dynamically.
        """
        chunks = self._chunk_text(
            content, 
            chunk_size=settings.rag_chunk_size, 
            overlap=settings.rag_chunk_overlap
        )
        self.retriever.append_to_index(chunks, source_name)

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
        """
        Helper to split text into overlapping character windows.
        Respects paragraph boundaries where possible.
        """
        # Split by paragraph
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        chunks = []
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            if current_len + p_len > chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                # Retain last few paragraphs for overlap
                overlap_len = 0
                overlap_chunk = []
                for prev in reversed(current_chunk):
                    if overlap_len + len(prev) < overlap:
                        overlap_chunk.insert(0, prev)
                        overlap_len += len(prev)
                    else:
                        break
                current_chunk = overlap_chunk
                current_len = sum(len(x) for x in current_chunk)
            
            current_chunk.append(p)
            current_len += p_len

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        # Fallback if paragraphs are too long
        final_chunks = []
        for c in chunks:
            if len(c) > chunk_size * 2:
                # Force chunk by character limit
                words = c.split()
                sub_chunk = []
                sub_len = 0
                for w in words:
                    sub_chunk.append(w)
                    sub_len += len(w) + 1
                    if sub_len > chunk_size:
                        final_chunks.append(" ".join(sub_chunk))
                        sub_chunk = sub_chunk[-10:] # small overlap
                        sub_len = sum(len(x) for x in sub_chunk)
                if sub_chunk:
                    final_chunks.append(" ".join(sub_chunk))
            else:
                final_chunks.append(c)

        return final_chunks
