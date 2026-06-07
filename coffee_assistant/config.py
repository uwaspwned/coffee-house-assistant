from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = BASE_DIR / ".env"


@dataclass(frozen=True)
class Settings:
    gemini_key: str
    telegram_bot_token: str
    gemini_model: str = "gemini-3.5-flash"
    database_path: Path = BASE_DIR / "data" / "coffee_assistant.sqlite3"
    history_limit: int = 12
    max_user_message_length: int = 2000
    assistant_timeout_seconds: float = 45.0
    assistant_retry_attempts: int = 2
    assistant_retry_delay_seconds: float = 1.0
    max_output_tokens: int = 700
    temperature: float = 0.4
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, env_path: Path | None = DEFAULT_ENV_PATH) -> Settings:
        if env_path is not None:
            load_dotenv(dotenv_path=env_path)

        database_path = Path(_get_env("DATABASE_PATH", "data/coffee_assistant.sqlite3"))
        if not database_path.is_absolute():
            database_path = BASE_DIR / database_path

        settings = cls(
            gemini_key=_get_env("GEMINI_KEY", ""),
            telegram_bot_token=_get_env("TELEGRAM_BOT_TOKEN", ""),
            gemini_model=_get_env("GEMINI_MODEL", "gemini-3.5-flash"),
            database_path=database_path,
            history_limit=_get_int("HISTORY_LIMIT", 12),
            max_user_message_length=_get_int("MAX_USER_MESSAGE_LENGTH", 2000),
            assistant_timeout_seconds=_get_float("ASSISTANT_TIMEOUT_SECONDS", 45.0),
            assistant_retry_attempts=_get_int("ASSISTANT_RETRY_ATTEMPTS", 2),
            assistant_retry_delay_seconds=_get_float("ASSISTANT_RETRY_DELAY_SECONDS", 1.0),
            max_output_tokens=_get_int("MAX_OUTPUT_TOKENS", 700),
            temperature=_get_float("TEMPERATURE", 0.4),
            log_level=_get_env("LOG_LEVEL", "INFO").upper(),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        missing = [
            name
            for name, value in {
                "GEMINI_KEY": self.gemini_key,
                "TELEGRAM_BOT_TOKEN": self.telegram_bot_token,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required env variables: {', '.join(missing)}")

        if self.history_limit < 1:
            raise ValueError("HISTORY_LIMIT must be greater than 0")
        if self.max_user_message_length < 1:
            raise ValueError("MAX_USER_MESSAGE_LENGTH must be greater than 0")
        if self.assistant_timeout_seconds <= 0:
            raise ValueError("ASSISTANT_TIMEOUT_SECONDS must be greater than 0")
        if self.assistant_retry_attempts < 1:
            raise ValueError("ASSISTANT_RETRY_ATTEMPTS must be greater than 0")
        if self.max_output_tokens < 1:
            raise ValueError("MAX_OUTPUT_TOKENS must be greater than 0")
        if not 0 <= self.temperature <= 2:
            raise ValueError("TEMPERATURE must be between 0 and 2")


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _get_int(name: str, default: int) -> int:
    value = _get_env(name, "")
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _get_float(name: str, default: float) -> float:
    value = _get_env(name, "")
    if not value:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
