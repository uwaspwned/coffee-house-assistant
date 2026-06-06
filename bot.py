import asyncio

import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from config import Config

logging.basicConfig(level=logging.INFO)

API_TOKEN=Config.TELEGRAM_BOT_TOKEN

bot = Bot(token=API_TOKEN) # type: ignore

dp = Dispatcher() # type: ignore


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Hi! I'm a coffee shop bot. How can I help you?")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
