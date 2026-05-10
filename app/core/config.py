from functools import lru_cache
from uuid import UUID

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration.

    Values are loaded from environment variables and optionally a `.env` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    project_name: str = "Smart Citizen Complaint Management System"
    api_v1_str: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/smart_citizen"
    backend_cors_origins: list[str] = [
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ]
    backend_cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    # Supabase integration
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    # Set to "authenticated" if you want strict audience checks.
    supabase_jwt_audience: str | None = None
    supabase_mock_verify: bool = True
    dev_skip_auth: bool = False

    # --- AI / ML ---
    # Auto-assign category_id on report creation (when enabled).
    ai_enabled: bool = True
    ai_preload_on_startup: bool = False
    # 0 disables the threshold (always accept the top label).
    ai_min_confidence: float = 0.0
    ai_default_category_name: str = "Other"
    ai_cache_ttl_seconds: int = 300

    # HuggingFace zero-shot classification defaults
    ai_hf_model: str = "facebook/bart-large-mnli"
    ai_hf_revision: str | None = None
    ai_hf_device: int = -1

    # OpenAI fallback (only used when HuggingFace fails / returns None)
    ai_openai_fallback_enabled: bool = False
    ai_openai_model: str = "gpt-4o-mini"
    ai_openai_timeout_seconds: float = 15.0
    openai_api_key: str | None = None

    # --- Email / SMTP ---
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None  # defaults to smtp_user if not set

    # Optional: persist an AI-generated confirmation message as a Comment.
    # Must reference an existing user UUID in the `users` table.
    ai_confirmation_comment_user_id: UUID | None = None

    # --- HuggingFace Inference API for Macedonian confirmation ---
    # Free tier: https://huggingface.co/inference-api
    # Add HF_API_TOKEN to your environment for higher rate limits (free account).
    ai_hf_inference_model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    ai_hf_inference_timeout_seconds: float = 30.0
    hf_api_token: str | None = None  # optional — raises free rate limit

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        # Allow BACKEND_CORS_ORIGINS to be set as a comma-separated string
        # in deployment env vars, not just a JSON array.
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                return value  # let pydantic parse JSON
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: object) -> object:
        # Supabase / Heroku paste a bare `postgres://` or `postgresql://` URI;
        # SQLAlchemy needs an explicit driver. We bundle psycopg (v3), so pin it.
        # Whitespace and surrounding quotes are common paste artefacts in CI secrets.
        if not isinstance(value, str):
            return value
        url = value.strip().strip('"').strip("'")
        if not url:
            return url
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (import-safe)."""
    return Settings()

