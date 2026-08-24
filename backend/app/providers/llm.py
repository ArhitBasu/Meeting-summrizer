from abc import ABC, abstractmethod
from typing import Optional, List
import json
from openai import OpenAI
from groq import Groq
from pydantic import BaseModel, ValidationError
from app.core.config import settings
from app.core.logging import logger


class ActionItemParsed(BaseModel):
    task: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None


class StructuredMeetingSummary(BaseModel):
    title: str
    summary: str
    key_points: List[str]
    decisions: List[str]
    action_items: List[ActionItemParsed]
    participants: List[str]


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_meeting_summary(self, transcript: str) -> StructuredMeetingSummary:
        """Analyze a transcript and return structured output."""
        pass


class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not set.")
            raise ValueError("OpenAI API key is missing")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def generate_meeting_summary(self, transcript: str) -> StructuredMeetingSummary:
        from app.prompts.meeting_summary_v1 import MEETING_SUMMARY_SYSTEM_PROMPT_V1
        
        try:
            logger.info(f"Starting LLM summarization with model {settings.OPENAI_LLM_MODEL}")
            completion = self.client.beta.chat.completions.parse(
                model=settings.OPENAI_LLM_MODEL,
                messages=[
                    {"role": "system", "content": MEETING_SUMMARY_SYSTEM_PROMPT_V1},
                    {"role": "user", "content": f"Transcript:\n\n{transcript}"}
                ],
                response_format=StructuredMeetingSummary,
            )
            
            parsed_result = completion.choices[0].message.parsed
            if not parsed_result:
                raise ValueError("LLM returned empty parsed result")
                
            logger.info("Successfully completed LLM summarization and structured parsing")
            return parsed_result
            
        except ValidationError as e:
            logger.error(f"Pydantic validation failed for LLM output: {e}")
            raise
        except Exception as e:
            logger.error(f"OpenAI LLM API failure: {e}")
            raise RuntimeError(f"Summarization failed: {e}")


class GroqLLMProvider(BaseLLMProvider):
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.error("GROQ_API_KEY is not set.")
            raise ValueError("Groq API key is missing")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        
    def generate_meeting_summary(self, transcript: str) -> StructuredMeetingSummary:
        from app.prompts.meeting_summary_v1 import MEETING_SUMMARY_SYSTEM_PROMPT_V1
        
        try:
            logger.info(f"Starting Groq LLM summarization with model {settings.GROQ_LLM_MODEL}")
            
            schema = StructuredMeetingSummary.model_json_schema()
            
            # We inject the JSON schema into the system prompt to enforce structure
            system_prompt = f"{MEETING_SUMMARY_SYSTEM_PROMPT_V1}\n\nYou MUST return a valid JSON object matching this JSON schema:\n{json.dumps(schema, indent=2)}"
            
            completion = self.client.chat.completions.create(
                model=settings.GROQ_LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Transcript:\n\n{transcript}"}
                ],
                response_format={"type": "json_object"},
            )
            
            response_content = completion.choices[0].message.content
            if not response_content:
                raise ValueError("LLM returned empty string")
            
            parsed_result = StructuredMeetingSummary.model_validate_json(response_content)
                
            logger.info("Successfully completed Groq LLM summarization and structured parsing")
            return parsed_result
            
        except ValidationError as e:
            logger.error(f"Pydantic validation failed for Groq LLM output: {e}")
            raise
        except Exception as e:
            logger.error(f"Groq LLM API failure: {e}")
            raise RuntimeError(f"Summarization failed: {e}")


def get_llm_provider() -> BaseLLMProvider:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "groq":
        return GroqLLMProvider()
    elif provider == "openai":
        return OpenAILLMProvider()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER configured: {provider}")
