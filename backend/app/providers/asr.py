from abc import ABC, abstractmethod
import os
from openai import OpenAI
from groq import Groq
from app.core.config import settings
from app.core.logging import logger


class BaseASRProvider(ABC):
    @abstractmethod
    def transcribe(self, file_path: str) -> str:
        """Transcribe an audio file and return the text."""
        pass


class OpenAIWhisperProvider(BaseASRProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not set.")
            raise ValueError("OpenAI API key is missing")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def transcribe(self, file_path: str) -> str:
        try:
            logger.info(f"Starting OpenAI Whisper transcription for {file_path}")
            with open(file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=settings.OPENAI_ASR_MODEL,
                    file=audio_file,
                    response_format="text"
                )
            logger.info(f"Successfully completed transcription for {file_path}")
            return transcript
        except Exception as e:
            logger.error(f"OpenAI Whisper API failure: {e}")
            raise RuntimeError(f"Transcription failed: {e}")


class GroqWhisperProvider(BaseASRProvider):
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.error("GROQ_API_KEY is not set.")
            raise ValueError("Groq API key is missing")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        
    def transcribe(self, file_path: str) -> str:
        try:
            logger.info(f"Starting Groq Whisper transcription for {file_path}")
            with open(file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=settings.GROQ_ASR_MODEL,
                    file=(os.path.basename(file_path), audio_file.read()),
                    response_format="text"
                )
            logger.info(f"Successfully completed transcription for {file_path}")
            return transcript
        except Exception as e:
            logger.error(f"Groq Whisper API failure: {e}")
            raise RuntimeError(f"Transcription failed: {e}")


def get_asr_provider() -> BaseASRProvider:
    provider = settings.ASR_PROVIDER.lower()
    if provider == "groq":
        return GroqWhisperProvider()
    elif provider == "openai":
        return OpenAIWhisperProvider()
    else:
        raise ValueError(f"Unknown ASR_PROVIDER configured: {provider}")
