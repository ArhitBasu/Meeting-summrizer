import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.providers.asr import get_asr_provider
from app.providers.llm import get_llm_provider
import json

def main():
    print("Initializing providers...")
    asr_provider = get_asr_provider()
    llm_provider = get_llm_provider()
    
    audio_file = "ami_test_audio/EN2001a_sample.mp3"
    
    print(f"Transcribing {audio_file} with Groq Whisper...")
    transcript_obj = asr_provider.transcribe(audio_file)
    
    # The SDK usually returns an object with a .text attribute or a dict
    # We need to extract the text
    transcript_text = getattr(transcript_obj, "text", str(transcript_obj))
    print("\n--- TRANSCRIPT ---\n")
    print(transcript_text[:500] + "...\n(truncated)")
    
    print("\nGenerating summary with Groq LLM...")
    summary = llm_provider.generate_meeting_summary(transcript_text)
    
    print("\n--- SUMMARY ---\n")
    print(summary.model_dump_json(indent=2))
    
    print("\nPipeline completed successfully!")

if __name__ == "__main__":
    main()
