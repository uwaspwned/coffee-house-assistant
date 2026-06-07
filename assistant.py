from __future__ import annotations

import asyncio
from collections.abc import Sequence

from google import genai
from google.genai import types

from config import Config
from database import StoredMessage
from prompts import SYSTEM_PROMPT


class AssistantError(RuntimeError):
    pass


class Assistant:
    def __init__(self) -> None:
        if not Config.GEMINI_KEY:
            raise ValueError("GEMINI_KEY is required")

        self._client = genai.Client(api_key=Config.GEMINI_KEY)

    async def ask(self, messages: Sequence[StoredMessage]) -> str:
        try:
            return await asyncio.to_thread(self._generate, list(messages))
        except Exception as exc:
            raise AssistantError("Gemini request failed") from exc

    def _generate(self, messages: list[StoredMessage]) -> str:
        response = self._client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=[_to_content(message) for message in messages],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )

        text = (response.text or "").strip()
        if not text:
            raise AssistantError("Gemini returned an empty response")
        return text


def _to_content(message: StoredMessage) -> types.Content:
    role = "model" if message.role == "assistant" else "user"
    return types.Content(
        role=role,
        parts=[types.Part.from_text(text=message.content)],
    )
