"""ElevenLabs Voice Integration"""

import logging
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from ..config import get_config, AUDIOS_DIR

logger = logging.getLogger("codeatlas.elevenlabs")

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False


@dataclass
class VoiceConfig:
    voice_id: str = "JBFqnCBsd6RMkjVDRZzb"
    model_id: str = "eleven_multilingual_v2"
    output_format: str = "mp3_44100_128"


AVAILABLE_VOICES = {
    "George (Male)": "JBFqnCBsd6RMkjVDRZzb",
    "Rachel (Female)": "21m00Tcm4TlvDq8ikWAM",
    "Adam (Male)": "pNInz6obpgDQGcFmaJgB",
    "Bella (Female)": "EXAVITQu4vr4xnSDxMaL",
    "Antoni (Male)": "ErXwobaYiN019PkySvjV",
}


class VoiceNarrator:
    def __init__(self, api_key: Optional[str] = None, voice_config: Optional[VoiceConfig] = None):
        self.config = get_config()
        self.api_key = api_key or self.config.elevenlabs_api_key
        self.voice_config = voice_config or VoiceConfig()
        self.audios_dir = AUDIOS_DIR
        self._client = None
    
    @property
    def available(self) -> bool:
        return ELEVENLABS_AVAILABLE and bool(self.api_key)
    
    @property
    def client(self):
        if self._client is None and self.available:
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client
    
    def generate(self, text: str, voice_id: Optional[str] = None) -> Tuple[Optional[Path], Optional[str]]:
        if not ELEVENLABS_AVAILABLE:
            return None, "ElevenLabs not installed. Run: pip install elevenlabs"
        if not self.api_key:
            return None, "ElevenLabs API key not configured"
        if not text or not text.strip():
            return None, "No text provided"
        
        try:
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id or self.voice_config.voice_id,
                model_id=self.voice_config.model_id,
                output_format=self.voice_config.output_format,
            )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_path = self.audios_dir / f"summary_{timestamp}.mp3"
            
            with open(audio_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            
            logger.info(f"Generated audio: {audio_path}")
            return audio_path, None
            
        except Exception as e:
            logger.exception("Audio generation failed")
            return None, f"Error: {str(e)}"
    
    def get_voices(self) -> dict:
        return AVAILABLE_VOICES
