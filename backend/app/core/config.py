"""
Central settings -- all environment-dependent config comes from here, no
module reads os.environ directly.

DATABASE_URL/REDIS_URL fall back to local defaults when unset, so importing
this module or building Settings() never crashes even without Postgres/Redis
running -- a connection is only attempted when a real query/command runs.
"""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]

# Settings reads .env for its own fields, but never sets os.environ -- and
# some libraries (langchain-google-genai, langchain-nvidia) read their API
# keys straight from os.environ. This module is imported first by every
# entrypoint, so calling load_dotenv() here once guarantees os.environ is
# populated everywhere, not just wherever load_dotenv() happened to be called before.
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM providers (Phase 3+) ---
    google_api_key: str = ""
    nvidia_api_key: str = ""

    # --- Database ---
    # Defaults to local sqlite so the app boots without Postgres (dev/test).
    # Production sets a real DATABASE_URL via .env.
    database_url: str = f"sqlite:///{ROOT_DIR / 'data' / 'app.db'}"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Firebase Auth ---
    # Path to service-account JSON. Empty = Firebase init is skipped with a
    # clear "auth not configured" error instead of a crash.
    firebase_credentials_path: str = ""

    # --- Rate limiting ---
    rate_limit_requests_per_minute: int = 20

    # --- App ---
    environment: str = "development"
    cors_allow_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- Observability ---
    # Empty = spans are generated but not exported (no collector configured).
    otlp_endpoint: str = ""
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        """SQLAlchemy engine URL -- forces the psycopg (v3) driver instead of
        psycopg2, since psycopg2-binary's DLL gets blocked on some corporate
        Windows machines. psycopg is already a dependency (langgraph-
        checkpoint-postgres), so this needs no new install. The raw
        `database_url` (no +psycopg suffix) is left as-is for callers like
        LangGraph's ConnectionPool, which expect plain postgresql:// conninfo."""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url

    @property
    def firebase_credentials_abspath(self) -> str:
        """firebase_credentials_path is repo-root-relative in .env, but a
        relative path resolves against cwd -- wrong if uvicorn runs from
        inside backend/. Anchoring to ROOT_DIR makes this work regardless
        of where the command is run from."""
        p = Path(self.firebase_credentials_path)
        if not p.is_absolute():
            p = ROOT_DIR / p
        return str(p)


@lru_cache
def get_settings() -> Settings:
    return Settings()
