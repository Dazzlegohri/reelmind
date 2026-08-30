from pathlib import Path
from app.core.config import settings

def transcribe(audio_path: str) -> str:
    if not settings.OPENAI_API_KEY:
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return result.text
    except Exception:
        return ""
