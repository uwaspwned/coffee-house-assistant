# Coffee House Assistant

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![aiogram](https://img.shields.io/badge/aiogram-3.28.2+-green?style=flat-square&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![aioSQLite](https://img.shields.io/badge/aioSQLite-0.21.0+-blue?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![pytes](https://img.shields.io/badge/pytest-passed-brightgreen?style=flat-square&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Ruff](https://img.shields.io/badge/Ruff-0.9+-orange?style=flat-square&logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)


Telegram bot for a small cafe assistant powered by Gemini. Users ask the bot through
`/assistant your request`; the bot stores per-user sessions in SQLite and keeps a short
conversation history for contextual recommendations.

## Features

- Telegram bot built with aiogram 3.
- Gemini-powered cafe assistant with a strict menu/system prompt.
- `/assistant`, `/menu`, `/reset`, `/help`, and `/start` commands.
- SQLite-backed sessions and message history per user/chat.
- Request length limit, Gemini timeout, retry attempts, and friendly error messages.
- Dockerfile, CI workflow, tests, and clean environment configuration.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` and fill the required secrets:

```env
GEMINI_KEY=your-gemini-api-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

## Run

```bash
python bot.py
```

You can also run it as a module:

```bash
python -m coffee_assistant
```

## Commands

- `/assistant your request` - ask the AI cafe assistant.
- `/menu` - show the cafe menu.
- `/reset` - reset your current assistant session.
- `/help` - show command help.

## Environment Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `GEMINI_KEY` | yes | - | Gemini API key. |
| `TELEGRAM_BOT_TOKEN` | yes | - | Telegram bot token from BotFather. |
| `GEMINI_MODEL` | no | `gemini-3.5-flash` | Gemini model id. |
| `DATABASE_PATH` | no | `data/coffee_assistant.sqlite3` | SQLite database path. |
| `HISTORY_LIMIT` | no | `12` | Number of recent messages sent to Gemini. |
| `MAX_USER_MESSAGE_LENGTH` | no | `2000` | Max characters accepted after `/assistant`. |
| `ASSISTANT_TIMEOUT_SECONDS` | no | `45` | Gemini request timeout. |
| `ASSISTANT_RETRY_ATTEMPTS` | no | `2` | Number of Gemini retry attempts. |
| `ASSISTANT_RETRY_DELAY_SECONDS` | no | `1` | Delay between retries. |
| `MAX_OUTPUT_TOKENS` | no | `700` | Max Gemini response tokens. |
| `TEMPERATURE` | no | `0.4` | Gemini generation temperature. |
| `LOG_LEVEL` | no | `INFO` | Logging level. |

## Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run checks:

```bash
python -m ruff check .
python -m pytest
```

## Docker

Build the image:

```bash
docker build -t coffee-house-assistant .
```

Run it with your `.env` file:

```bash
docker run --env-file .env -v coffee_assistant_data:/app/data coffee-house-assistant
```
