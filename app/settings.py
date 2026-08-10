import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_api_key: str
    app_version: str
    environment: str
    max_question_chars: int
    rate_limit_per_minute: int
    port: int


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    try:
        return int(value)
    except ValueError:
        return default


def _secret_env(name: str) -> str:
    """Read a secret from NAME_FILE first, then NAME.

    Supports Docker/Compose secrets mounted as files, while still allowing
    local class work and PaaS deployments that inject secrets as env vars.
    """
    file_path = os.getenv(f"{name}_FILE")
    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise RuntimeError(f"{name}_FILE points to a missing file: {file_path}")
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
        raise RuntimeError(f"{name}_FILE is empty: {file_path}")

    value = os.getenv(name)
    if value and value.strip():
        return value.strip()

    raise RuntimeError(
        f"{name} is required. Set it via .env for local development, "
        "cloud env vars for PaaS, or a secret manager for production."
    )


def get_settings() -> Settings:
    return Settings(
        app_api_key=_secret_env("APP_API_KEY"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        environment=os.getenv("ENVIRONMENT", "local"),
        max_question_chars=_int_env("MAX_QUESTION_CHARS", 2000),
        rate_limit_per_minute=_int_env("RATE_LIMIT_PER_MINUTE", 20),
        port=_int_env("PORT", 8000),
    )
