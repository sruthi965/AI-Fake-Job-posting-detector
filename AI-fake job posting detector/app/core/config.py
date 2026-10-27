"""Application settings, read from environment variables and an optional .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SECRET = "dev-insecure-secret-change-me"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader. Real environment variables always win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / ".env")


def _path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else BASE_DIR / p


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str
    secret_key: str
    access_token_minutes: int
    database_url: str
    cors_origins: list[str]
    model_path: Path
    metrics_path: Path
    frontend_dir: Path
    llm_provider: str  # none | openai | azure
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    azure_endpoint: str
    azure_deployment: str
    azure_api_version: str
    llm_timeout: float

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate(self) -> None:
        if self.is_production and (self.secret_key == DEFAULT_SECRET or len(self.secret_key) < 32):
            raise RuntimeError(
                "SECRET_KEY must be a random value of at least 32 characters when APP_ENV=production."
            )


def get_settings() -> Settings:
    env = os.environ.get
    return Settings(
        app_env=env("APP_ENV", "development").lower(),
        secret_key=env("SECRET_KEY", DEFAULT_SECRET),
        access_token_minutes=int(env("ACCESS_TOKEN_MINUTES", "60")),
        database_url=env("DATABASE_URL", "sqlite:///./jobguard.db"),
        cors_origins=_split(env("CORS_ORIGINS", "")),
        model_path=_path(env("MODEL_PATH", "artifacts/model.joblib")),
        metrics_path=_path(env("METRICS_PATH", "artifacts/metrics.json")),
        frontend_dir=_path(env("FRONTEND_DIR", "frontend")),
        llm_provider=env("LLM_PROVIDER", "none").lower(),
        llm_api_key=env("LLM_API_KEY", ""),
        llm_base_url=env("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        llm_model=env("LLM_MODEL", "gpt-4o-mini"),
        azure_endpoint=env("AZURE_OPENAI_ENDPOINT", "").rstrip("/"),
        azure_deployment=env("AZURE_OPENAI_DEPLOYMENT", ""),
        azure_api_version=env("AZURE_OPENAI_API_VERSION", "2024-06-01"),
        llm_timeout=float(env("LLM_TIMEOUT_SECONDS", "30")),
    )
