from functools import lru_cache
from uuid import UUID

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

    # --- CORS ---
    # Strict whitelist — no wildcards allowed in production.
    # Set BACKEND_CORS_ORIGINS in .env as a comma-separated list.
    # Example: "http://localhost:5173,https://yourapp.com"
    backend_cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    # Regex fallback for localhost dev ports — disabled in production via env override.
    backend_cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    # --- Rate limiting (slowapi) ---
    # Default limit applied to all /api/v1/* endpoints.
    rate_limit_default: str = "100/minute"
    # Stricter limit for POST /reports (prevent spam submissions).
    rate_limit_reports_post: str = "10/minute"

    # --- Supabase integration ---
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_jwt_audience: str | None = None
    supabase_mock_verify: bool = True
    dev_skip_auth: bool = False

    # --- AI / ML ---
    ai_enabled: bool = True
    ai_preload_on_startup: bool = False
    ai_min_confidence: float = 0.0
    ai_default_category_name: str = "Other"
    ai_cache_ttl_seconds: int = 300

    # HuggingFace zero-shot classification
    ai_hf_model: str = "facebook/bart-large-mnli"
    ai_hf_revision: str | None = None
    ai_hf_device: int = -1

    # OpenAI fallback
    ai_openai_fallback_enabled: bool = False
    ai_openai_model: str = "gpt-4o-mini"
    ai_openai_timeout_seconds: float = 15.0
    openai_api_key: str | None = None

    # Optional: persist AI confirmation as a Comment
    ai_confirmation_comment_user_id: UUID | None = None

    # HuggingFace Inference API for Macedonian confirmation
    ai_hf_inference_model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    ai_hf_inference_timeout_seconds: float = 30.0
    hf_api_token: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (import-safe)."""
    return Settings()