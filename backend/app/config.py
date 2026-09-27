"""Application configuration.

All secrets and API credentials are read from environment variables (or a local
``.env`` file). Nothing sensitive is ever hard-coded or sent to the frontend.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"


class Settings(BaseSettings):
    """Runtime settings for the SocialScope AI backend."""

    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- Application -----------------------------------------------------
    app_name: str = "SocialScope AI"
    app_tagline: str = "From Social Data to Smart Insights."
    environment: str = "development"
    debug: bool = False

    # ---- API credentials (never exposed to the browser) -----------------
    youtube_api_key: str | None = Field(default=None, alias="YOUTUBE_API_KEY")
    facebook_access_token: str | None = Field(default=None, alias="FACEBOOK_ACCESS_TOKEN")
    instagram_access_token: str | None = Field(default=None, alias="INSTAGRAM_ACCESS_TOKEN")
    instagram_account_id: str | None = Field(default=None, alias="INSTAGRAM_ACCOUNT_ID")
    facebook_page_id: str | None = Field(default=None, alias="FACEBOOK_PAGE_ID")
    meta_api_version: str = Field(default="v21.0", alias="META_API_VERSION")

    # ---- Database --------------------------------------------------------
    database_url: str = Field(
        default=f"sqlite:///{(DATA_DIR / 'socialscope.db').as_posix()}",
        alias="DATABASE_URL",
    )
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")

    # ---- HTTP / security -------------------------------------------------
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    rate_limit_requests: int = Field(default=30, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")
    request_timeout_seconds: float = Field(default=20.0, alias="REQUEST_TIMEOUT_SECONDS")
    max_comment_pages: int = Field(default=5, alias="MAX_COMMENT_PAGES")
    comments_per_page: int = Field(default=100, alias="COMMENTS_PER_PAGE")

    # ---- Analysis configuration -----------------------------------------
    sentiment_backend: str = Field(default="auto", alias="SENTIMENT_BACKEND")
    enable_demo_mode: bool = Field(default=True, alias="ENABLE_DEMO_MODE")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, (list, tuple)):
            return ",".join(str(item) for item in value)
        return value

    @field_validator(
        "youtube_api_key",
        "facebook_access_token",
        "instagram_access_token",
        "instagram_account_id",
        "facebook_page_id",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def _blank_database_url(cls, value: object) -> object:
        """Normalize the connection URL.

        * An empty value means "use the local SQLite default".
        * Hosts such as Render, Neon, Supabase and Railway hand out
          ``postgresql://`` URLs, whose SQLAlchemy default driver is psycopg2.
          psycopg2 is not a dependency of this project, so a URL is rewritten to
          the psycopg3 driver that *is* installed. Without this, pasting a
          provider URL verbatim fails with
          ``ModuleNotFoundError: No module named 'psycopg2'``.
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return f"sqlite:///{(DATA_DIR / 'socialscope.db').as_posix()}"

        url = str(value).strip()
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def data_dir(self) -> Path:
        return DATA_DIR

    def platform_credentials(self) -> dict[str, bool]:
        """Report which platforms have usable credentials (booleans only)."""
        return {
            "youtube": bool(self.youtube_api_key),
            "facebook": bool(self.facebook_access_token or self.instagram_access_token),
            "instagram": bool(self.instagram_access_token or self.facebook_access_token),
        }

    def ensure_directories(self) -> None:
        for name in ("raw", "cleaned", "exports", "demo"):
            (DATA_DIR / name).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings


settings = get_settings()
