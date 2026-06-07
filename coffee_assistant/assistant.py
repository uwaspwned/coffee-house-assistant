from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from google import genai
from google.genai import types

from coffee_assistant.config import Settings
from coffee_assistant.database import StoredMessage
from coffee_assistant.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AssistantError(RuntimeError):
    pass


class Assistant:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = genai.Client(api_key=settings.gemini_key)

    async def ask(self, messages: Sequence[StoredMessage]) -> str:
        last_error: BaseException | None = None

        for attempt in range(1, self.settings.assistant_retry_attempts + 1):
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(self._generate, list(messages)),
                    timeout=self.settings.assistant_timeout_seconds,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Gemini request failed on attempt %s/%s: %s",
                    attempt,
                    self.settings.assistant_retry_attempts,
                    exc,
                )
                if attempt < self.settings.assistant_retry_attempts:
                    await asyncio.sleep(self.settings.assistant_retry_delay_seconds)

        raise AssistantError("Gemini request failed") from last_error

    def _generate(self, messages: list[StoredMessage]) -> str:
        response = self._client.models.generate_content(
            model=self.settings.gemini_model,
            contents=[_to_content(message) for message in messages],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=self.settings.max_output_tokens,
                temperature=self.settings.temperature,
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
