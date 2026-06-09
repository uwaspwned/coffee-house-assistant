from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import BotCommand, ErrorEvent, Message

from coffee_assistant.assistant import Assistant, AssistantError
from coffee_assistant.config import Settings
from coffee_assistant.database import Database
from coffee_assistant.prompts import MENU

logger = logging.getLogger(__name__)


def create_router() -> Router:
    router = Router(name=__name__)

    @router.message(CommandStart())
    async def start_command(message: Message) -> None:
        await message.answer(
            "Hi! I'm the dotwired cafe assistant.\n"
            "Ask me with: /assistant recommend breakfast and coffee"
        )

    @router.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer(
            "Commands:\n"
            "/assistant your request - ask the cafe assistant\n"
            "/menu - show the cafe menu\n"
            "/reset - reset your current session"
        )

    @router.message(Command("menu"))
    async def menu_command(message: Message) -> None:
        await message.answer(f"Here is our menu:\n\n{MENU}")

    @router.message(Command("assistant"))
    async def assistant_command(
        message: Message,
        command: CommandObject,
        db: Database,
        assistant: Assistant,
        settings: Settings,
    ) -> None:
        query = (command.args or "").strip()
        if not query:
            await message.answer("Write your question after the command: /assistant what should I order?")
            return

        if len(query) > settings.max_user_message_length:
            await message.answer(
                "Your message is too long. "
                f"Please keep it under {settings.max_user_message_length} characters."
            )
            return

        if message.from_user is None:
            await message.answer("I couldn't identify the user for this session.")
            return

        session_id = await db.get_or_create_session(
            telegram_user_id=message.from_user.id,
            telegram_chat_id=message.chat.id,
        )
        await db.add_message(session_id=session_id, role="user", content=query)
        history = await db.get_recent_messages(session_id, limit=settings.history_limit)

        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

        try:
            answer = await assistant.ask(history)
        except AssistantError:
            logger.exception("Assistant request failed")
            await message.answer("I couldn't reach the assistant right now. Please try again later.")
            return

        await db.add_message(session_id=session_id, role="assistant", content=answer)
        await answer_in_chunks(message, answer)

    @router.message(Command("reset"))
    async def reset_command(message: Message, db: Database) -> None:
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

    @router.message(F.text)
    async def text_without_command(message: Message) -> None:
        await message.answer("Please use /assistant followed by your question.")

    @router.errors()
    async def error_handler(event: ErrorEvent) -> bool:
        exception = event.exception
        logger.error(
            "Unhandled update error",
            exc_info=(type(exception), exception, exception.__traceback__),
        )
        return True

    return router


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(create_router())
    return dp


async def answer_in_chunks(message: Message, text: str, chunk_size: int = 3900) -> None:
    for start in range(0, len(text), chunk_size):
        await message.answer(text[start : start + chunk_size])


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="assistant", description="Ask the cafe assistant"),
            BotCommand(command="menu", description="Show the cafe menu"),
            BotCommand(command="reset", description="Reset your session"),
            BotCommand(command="help", description="Show help"),
        ]
    )


from coffee_assistant.proxy import session

async def run(settings: Settings | None = None) -> None:
    settings = settings or Settings.from_env()
    configure_logging(settings.log_level)

    bot = Bot(token=settings.telegram_bot_token, session=session)
    dp = create_dispatcher()
    db = Database(settings.database_path)
    assistant = Assistant(settings)

    await db.connect()
    await db.init_schema()

    try:
        await set_commands(bot)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot polling started")
        await dp.start_polling(bot, db=db, assistant=assistant, settings=settings)
    finally:
        await db.close()
        await bot.session.close()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
