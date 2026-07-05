"""
Central configuration using Pydantic Settings.
All settings loaded from environment variables with sensible defaults.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Medical AI System"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    models_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "models")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "logs")

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/medical_ai.db"
    database_echo: bool = False

    # Google ADK / Gemini
    google_api_key: str = ""
    google_model: str = "gemini-1.5-pro"
    google_model_temperature: float = 0.3
    google_model_top_p: float = 0.9
    google_model_max_tokens: int = 8192

    # ADK Settings
    adk_session_db_url: str = "sqlite+aiosqlite:///./data/adk_sessions.db"

    # RAG / Vector Store
    rag_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rag_faiss_index_path: str = "./data/faiss_index"
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.7

    # Medical Corpus
    medical_corpus_path: str = "./data/medical_corpus"

    # MCP Servers
    mcp_drug_server_url: str = "http://localhost:8001"
    mcp_patient_server_url: str = "http://localhost:8002"
    mcp_guideline_server_url: str = "http://localhost:8003"

    # OpenFDA API (for drug data)
    openfda_api_key: str = ""
    openfda_base_url: str = "https://api.fda.gov"

    # Security
    secret_key: str = "change-me-in-production-use-strong-random-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12

    # PHI Masking
    phi_masking_enabled: bool = True
    phi_presidio_language: str = "en"

    # Audit Logging
    audit_log_enabled: bool = True
    audit_log_path: str = "./logs/audit.log"
    audit_log_max_size_mb: int = 100
    audit_log_backup_count: int = 5

    # Prompt Injection Detection
    prompt_guard_enabled: bool = True
    prompt_guard_threshold: float = 0.8

    # Streamlit
    streamlit_host: str = "0.0.0.0"
    streamlit_port: int = 8501
    streamlit_theme_base: str = "light"
    streamlit_server_headless: bool = True

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    api_cors_origins: List[str] = Field(default_factory=lambda: ["*"])

    # ML Models
    ml_model_path: str = "./models"
    ml_heart_disease_model: str = "heart_disease_xgb.pkl"
    ml_diabetes_model: str = "diabetes_xgb.pkl"
    ml_risk_model: str = "risk_xgb.pkl"

    # Simulation
    simulation_months: List[int] = Field(default_factory=lambda: [3, 6, 12])
    simulation_monte_carlo_runs: int = 100

    # Debate System
    debate_max_rounds: int = 3
    debate_confidence_threshold: float = 0.7
    debate_min_consensus: float = 0.6

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "./logs/app.log"

    # External APIs
    pubmed_api_key: str = ""
    clinical_trials_api_key: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export commonly used settings
settings = get_settings()