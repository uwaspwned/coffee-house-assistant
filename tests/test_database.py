from pathlib import Path

import pytest

from coffee_assistant.database import Database


@pytest.mark.asyncio
async def test_database_stores_history_and_resets_session(tmp_path: Path) -> None:
    db = Database(tmp_path / "assistant.sqlite3")
    await db.connect()
    await db.init_schema()

    first_session_id = await db.get_or_create_session(telegram_user_id=1, telegram_chat_id=10)
    same_session_id = await db.get_or_create_session(telegram_user_id=1, telegram_chat_id=10)

    assert same_session_id == first_session_id

    await db.add_message(first_session_id, "user", "Recommend breakfast")
    await db.add_message(first_session_id, "assistant", "Try pancakes with cappuccino.")

    history = await db.get_recent_messages(first_session_id, limit=10)

    assert [(message.role, message.content) for message in history] == [
        ("user", "Recommend breakfast"),
        ("assistant", "Try pancakes with cappuccino."),
    ]

    assert await db.reset_session(telegram_user_id=1, telegram_chat_id=10) == 1

    second_session_id = await db.get_or_create_session(telegram_user_id=1, telegram_chat_id=10)

    assert second_session_id != first_session_id
    assert await db.get_recent_messages(second_session_id, limit=10) == []

    await db.close()
