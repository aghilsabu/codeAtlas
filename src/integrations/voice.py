"""Voice Module - AI description + ElevenLabs TTS"""

import logging
from typing import Tuple, Optional
from pathlib import Path

from ..config import get_config
from ..core.analyzer import CodeAnalyzer
from .elevenlabs import VoiceNarrator

logger = logging.getLogger("codeatlas.voice")

NARRATION_PROMPT = """Analyze this architecture diagram and provide a brief, conversational summary suitable for audio narration. 
Keep it under 200 words. Focus on what the codebase does, key components and their relationships, and the overall architecture pattern.
Provide a natural, spoken summary (no bullet points, no markdown)."""


def generate_audio_summary(
    dot_source: str,
    gemini_api_key: Optional[str] = None,
    elevenlabs_api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    voice_id: Optional[str] = None,
) -> Tuple[Optional[Path], str]:
    config = get_config()
    gemini_key = gemini_api_key or config.gemini_api_key
    elevenlabs_key = elevenlabs_api_key or config.elevenlabs_api_key
    
    if not elevenlabs_key:
        return None, "⚠️ ElevenLabs API key not set. Go to Settings."
    if not gemini_key:
        return None, "⚠️ Gemini API key not set. Go to Settings."
    if not dot_source:
        return None, "⚠️ No diagram loaded. Generate or load a diagram first."
    
    try:
        logger.info("Generating description for audio...")
        analyzer = CodeAnalyzer(api_key=gemini_key, model_name="gemini-2.0-flash")
        
        prompt = f"{NARRATION_PROMPT}\n\nDOT diagram:\n```\n{dot_source}\n```"
        result = analyzer.chat(prompt, "", None)
        
        if not result.success or not result.content:
            return None, f"⚠️ Failed to generate description: {result.error or 'Empty response'}"
        
        logger.info(f"Generated description: {len(result.content)} chars")
        
        narrator = VoiceNarrator(api_key=elevenlabs_key)
        if not narrator.available:
            return None, "⚠️ ElevenLabs not available"
        
        audio_path, error = narrator.generate(result.content, voice_id)
        
        if error:
            return None, f"❌ {error}"
        
        return audio_path, "✅ Audio generated!"
        
    except Exception as e:
        logger.exception("Audio generation failed")
        return None, f"❌ Error: {str(e)}"
