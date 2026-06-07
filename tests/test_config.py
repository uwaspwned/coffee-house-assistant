from pathlib import Path

import pytest

from coffee_assistant.config import BASE_DIR, Settings


def test_settings_loads_required_and_optional_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_KEY", "gemini-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("DATABASE_PATH", "data/test.sqlite3")
    monkeypatch.setenv("HISTORY_LIMIT", "5")
    monkeypatch.setenv("MAX_USER_MESSAGE_LENGTH", "1500")
    monkeypatch.setenv("ASSISTANT_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("TEMPERATURE", "0.2")

    settings = Settings.from_env(env_path=None)

    assert settings.gemini_key == "gemini-key"
    assert settings.telegram_bot_token == "telegram-token"
    assert settings.database_path == BASE_DIR / Path("data/test.sqlite3")
    assert settings.history_limit == 5
    assert settings.max_user_message_length == 1500
    assert settings.assistant_timeout_seconds == 12.5
    assert settings.temperature == 0.2


def test_settings_requires_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="Missing required env variables"):
        Settings.from_env(env_path=None)
