import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


class Config:
    GEMINI_KEY = os.getenv("GEMINI_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    HISTORY_LIMIT = _get_int("HISTORY_LIMIT", 12)

    _database_path = Path(os.getenv("DATABASE_PATH", "coffee_assistant.sqlite3"))
    DATABASE_PATH = _database_path if _database_path.is_absolute() else BASE_DIR / _database_path

    @classmethod
    def validate_required(cls) -> None:
        missing = [
            name
            for name, value in {
                "GEMINI_KEY": cls.GEMINI_KEY,
                "TELEGRAM_BOT_TOKEN": cls.TELEGRAM_BOT_TOKEN,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required env variables: {', '.join(missing)}")
