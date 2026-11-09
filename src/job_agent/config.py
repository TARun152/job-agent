"""Environment-backed application settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from job_agent.constants.apply import (
    DEFAULT_APPLY_SLOW_MO_MS,
    DEFAULT_MAX_DAILY_APPLIES,
    DEFAULT_MAX_DAILY_DISCOVERIES,
    DEFAULT_NOTICE_PERIOD_DAYS,
)
from job_agent.constants.logging_const import DEFAULT_LOG_LEVEL
from job_agent.constants.matching import (
    DEFAULT_KEYWORD_STUFF_CAP,
    DEFAULT_LOCATIONS,
    DEFAULT_MATCH_THRESHOLD,
    DEFAULT_ROLE_KEYWORDS,
)
from job_agent.constants.paths import (
    DEFAULT_DATABASE_URL,
    DEFAULT_RESUME_DIR,
    DEFAULT_SESSIONS_DIR,
    DEFAULT_TAILORED_DIR,
)
from job_agent.constants.statuses import QUEUE_HOST_DEFAULT, QUEUE_PORT_DEFAULT


class Settings(BaseSettings):
    """Runtime configuration loaded from env and optional ``.env`` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    job_agent_env: str = "dev"
    log_level: str = DEFAULT_LOG_LEVEL
    database_url: str = DEFAULT_DATABASE_URL
    resume_dir: str = DEFAULT_RESUME_DIR
    tailored_dir: str = DEFAULT_TAILORED_DIR
    sessions_dir: str = DEFAULT_SESSIONS_DIR

    match_score_threshold: float = DEFAULT_MATCH_THRESHOLD
    match_keyword_stuff_cap: float = DEFAULT_KEYWORD_STUFF_CAP
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"

    role_keywords: str = Field(default=",".join(DEFAULT_ROLE_KEYWORDS))
    locations: str = Field(default=",".join(DEFAULT_LOCATIONS))
    remote_ok: bool = True
    salary_floor_inr: int | None = None
    notice_period_days: int = DEFAULT_NOTICE_PERIOD_DAYS

    naukri_email: str = ""
    naukri_password: str = ""
    instahyre_email: str = ""
    instahyre_password: str = ""
    linkedin_email: str = ""
    linkedin_password: str = ""
    workday_email: str = ""
    workday_password: str = ""

    gmail_credentials_path: str = "./credentials.json"
    gmail_token_path: str = "./gmail_token.json"
    gmail_sender: str = ""

    queue_host: str = QUEUE_HOST_DEFAULT
    queue_port: int = QUEUE_PORT_DEFAULT

    apply_headless: bool = False
    apply_slow_mo_ms: int = DEFAULT_APPLY_SLOW_MO_MS
    max_daily_applies: int = DEFAULT_MAX_DAILY_APPLIES
    max_daily_discoveries: int = DEFAULT_MAX_DAILY_DISCOVERIES

    def role_keyword_list(self) -> list[str]:
        """Split configured role keywords into a clean list."""
        return [part.strip() for part in self.role_keywords.split(",") if part.strip()]

    def location_list(self) -> list[str]:
        """Split configured locations into a clean list."""
        return [part.strip() for part in self.locations.split(",") if part.strip()]

    def ensure_runtime_dirs(self) -> None:
        """Create on-disk directories used at runtime."""
        for path_str in (self.resume_dir, self.tailored_dir, self.sessions_dir, "data"):
            Path(path_str).mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide cached settings instance.

    Returns:
        Loaded ``Settings`` object.
    """
    settings = Settings()
    # Ensure data folders exist before any DB or file I/O.
    settings.ensure_runtime_dirs()
    return settings
