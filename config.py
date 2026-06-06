import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(".env")

load_dotenv(dotenv_path=ENV_PATH)

class Config:
    GEMINI_KEY=os.getenv("GEMINI_KEY")

    TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")    
