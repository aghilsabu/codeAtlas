"""CodeAtlas Integrations"""

from .elevenlabs import VoiceNarrator
from .voice import generate_audio_summary
from .modal_client import ModalClient, get_modal_client

__all__ = ["VoiceNarrator", "generate_audio_summary", "ModalClient", "get_modal_client"]
