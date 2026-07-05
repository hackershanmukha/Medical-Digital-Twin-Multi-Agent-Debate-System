"""
Unit tests for RAG pipeline (ClinicalRAGPipeline).
"""
import pytest

from rag.pipeline import ClinicalRAGPipeline


def test_rag_pipeline_flow(tmp_path):
    # Arrange
    corpus_dir = tmp_path / "corpus"
    index_dir = tmp_path / "faiss"
    corpus_dir.mkdir()
    index_dir.mkdir()

    # Create dummy guideline file
    guideline_content = (
        "AHA/ACC 2019 Guideline: For patients with high cardiovascular risk (10-year risk >= 20%), "
        "initiate high-intensity statin therapy (Atorvastatin 40-80 mg daily). "
        "This reduces major adverse cardiovascular events (MACE) by 25%."
    )
    guideline_file = corpus_dir / "aha_guideline_test.txt"
    with open(guideline_file, "w", encoding="utf-8") as f:
        f.write(guideline_content)

    # Act
    pipeline = ClinicalRAGPipeline(
        corpus_path=str(corpus_dir),
        index_path=str(index_dir)
    )
    pipeline.initialize(force_rebuild=True)

    # Search
    retrieved = pipeline.retrieve("cardiovascular risk statin therapy", top_k=1)

    # Assert
    assert retrieved is not None
    assert "AHA/ACC 2019 Guideline" in retrieved
    assert "Atorvastatin" in retrieved
    assert "aha_guideline_test.txt" in retrieved

    print("ClinicalRAGPipeline unit test passed!")
