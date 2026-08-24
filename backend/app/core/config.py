from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Meeting Summarizer API"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/meeting_summarizer"
    UPLOAD_DIR: str = "uploads"
    LOG_LEVEL: str = "INFO"
    MAX_FILE_SIZE_MB: int = 25
    # Configurable CORS origins. In production, set to your frontend URL.
    # Example: ALLOWED_ORIGINS=http://localhost:5173,https://your-app.com
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Provider selection ──────────────────────────────────────────────────
    # Set to "groq" or "openai". The factory functions in providers/ read this.
    ASR_PROVIDER: str = "groq"
    LLM_PROVIDER: str = "groq"

    # ── Groq credentials ────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_ASR_MODEL: str = "whisper-large-v3-turbo"
    GROQ_LLM_MODEL: str = "llama-3.3-70b-versatile"

    # ── OpenAI credentials (kept for optional use) ──────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_ASR_MODEL: str = "whisper-1"
    OPENAI_LLM_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
