from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from assistant import Assistant, AssistantError
from config import Config
from database import Database
from prompts import MENU

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Hi! I'm a coffee shop assistant. "
        "Ask me with: /assistant recommend breakfast and coffee"
    )


@dp.message(Command("menu"))
async def show_menu(message: Message) -> None:
    await message.answer(f"Here is our menu:\n{MENU}")


@dp.message(Command("assistant"))
async def assistant_command(
    message: Message,
    command: CommandObject,
    db: Database,
    assistant: Assistant,
) -> None:
    query = (command.args or "").strip()
    if not query:
        await message.answer("Write your question after the command: /assistant what should I order?")
        return

    if message.from_user is None:
        await message.answer("I couldn't identify the user for this session.")
        return

    session_id = await db.get_or_create_session(
        telegram_user_id=message.from_user.id,
        telegram_chat_id=message.chat.id,
    )
    await db.add_message(session_id=session_id, role="user", content=query)
    history = await db.get_recent_messages(session_id, limit=Config.HISTORY_LIMIT)

    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    try:
        answer = await assistant.ask(history)
    except AssistantError:
        logging.exception("Assistant request failed")
        await message.answer("I couldn't reach the assistant right now. Please try again later.")
        return

    await db.add_message(session_id=session_id, role="assistant", content=answer)
    await _answer_in_chunks(message, answer)


@dp.message(Command("reset"))
async def reset(message: Message, db: Database) -> None:
    if message.from_user is None:
        await message.answer("I couldn't identify the user for this session.")
        return

    reset_count = await db.reset_session(
        telegram_user_id=message.from_user.id,
        telegram_chat_id=message.chat.id,
    )

    if reset_count:
        await message.answer("Done, your current session has been reset.")
    else:
        await message.answer("You don't have an active session yet. Start with /assistant.")


async def _answer_in_chunks(message: Message, text: str, chunk_size: int = 3900) -> None:
    for start in range(0, len(text), chunk_size):
        await message.answer(text[start : start + chunk_size])


async def main() -> None:
    Config.validate_required()

    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN or "")
    db = Database(Config.DATABASE_PATH)
    assistant = Assistant()

    await db.connect()
    await db.init_schema()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, db=db, assistant=assistant)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
