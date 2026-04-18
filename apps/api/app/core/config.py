from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


CURRENT_FILE = Path(__file__).resolve()
API_ROOT = next((parent for parent in CURRENT_FILE.parents if (parent / "pyproject.toml").exists()), CURRENT_FILE.parent)
REPO_ROOT = API_ROOT.parent.parent if len(API_ROOT.parents) >= 2 else API_ROOT
ENV_FILE = REPO_ROOT / ".env" if (REPO_ROOT / ".env").exists() else API_ROOT / ".env"


class Settings(BaseSettings):
    app_name: str = "Utah Research Matcher API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/utah_research_matcher"
    cors_allowed_origins_raw: str = Field(default="*", alias="CORS_ALLOWED_ORIGINS")
    openai_api_key: str | None = None
    openai_generation_model: str = "gpt-5-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openalex_api_key: str | None = None
    openalex_base_url: str = "https://api.openalex.org"
    openalex_contact_email: str | None = None
    profiles_base_url: str = "https://profiles.faculty.utah.edu"
    profiles_seed_urls_raw: str = Field(
        default="https://profiles.faculty.utah.edu",
        alias="PROFILES_SEED_URLS",
    )
    minimum_publication_count: int = 3
    recent_paper_window_years: int = 3
    enable_query_persistence: bool = False

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://") and "+psycopg" not in value:
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @property
    def profiles_seed_urls(self) -> list[str]:
        return [
            value.strip()
            for value in self.profiles_seed_urls_raw.split(",")
            if value.strip()
        ]

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [
            value.strip()
            for value in self.cors_allowed_origins_raw.split(",")
            if value.strip()
        ]


settings = Settings()
