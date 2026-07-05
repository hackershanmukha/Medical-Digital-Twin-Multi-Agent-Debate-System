from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App Info
    app_name: str = "Medical Digital Twin & Debate API"
    debug: bool = False
    environment: str = "development"

    # Database Settings
    # default to SQLite, can override in env
    database_url: str = "sqlite+aiosqlite:///./data/medical_ai.db"
    database_echo: bool = False

    # Security & JWT
    secret_key: str = "change-me-in-production-use-strong-random-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    # Google Generative AI
    google_api_key: str = ""
    google_model: str = "gemini-2.5-pro"

    # Vector Database (ChromaDB)
    chroma_db_dir: str = "./data/chroma_db"
    chroma_host: Optional[str] = None
    chroma_port: Optional[int] = None

    # CORS Allowed Origins
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
