from google import genai
from google.genai import types

from config import Config

from prompts import SYSTEM_PROMPT

client = genai.Client(api_key=Config.GEMINI_KEY)

chat_history = []

while True:
    user_input = input("Guest: ").strip()

    if not user_input:
        continue

    else:
        try:
            chat_history.append(f"Guest: {user_input}")

            input_to_model = "\n".join(chat_history) + "\nAI-assistant: "

            response = client.models.generate_content_stream(
                model="gemini-3.5-flash",
                contents=input_to_model,
                config=types.GenerateContentConfig(
                        # thinking_config=types.ThinkingConfig(thinking_level="low"), # type: ignore
                        system_instruction=SYSTEM_PROMPT
                    ),
            )

            print("\nAI-assistant: ", end="", flush=True)

            full_response = ""
            for chunk in response:
                print(chunk.text, end="", flush=True)
                full_response += chunk.text # type: ignore

            print()

            chat_history.append(f"AI-assistant: {full_response}")

        except Exception as e:
            print(f"Error: {e}")
