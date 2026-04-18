from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[4]


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
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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
