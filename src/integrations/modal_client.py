"""
CodeAtlas Modal Client

Optional client to call Modal backend endpoints.
Falls back to local processing if Modal is not available.
"""

import os
import requests
import base64
from typing import Optional, Tuple
import logging

logger = logging.getLogger("codeatlas.modal_client")


class ModalClient:
    """Client for calling Modal backend endpoints."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Modal client.
        
        Args:
            base_url: Base URL for Modal endpoints. If not provided,
                     reads from MODAL_BACKEND_URL environment variable.
                     If neither is set, Modal will not be used.
        """
        self.base_url = base_url or os.environ.get("MODAL_BACKEND_URL", "")
        self.enabled = bool(self.base_url)
        
        if self.enabled:
            logger.info(f"Modal backend enabled: {self.base_url}")
        else:
            logger.info("Modal backend not configured, using local processing")
    
    def is_available(self) -> bool:
        """Check if Modal backend is available."""
        if not self.enabled:
            return False
        
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
    
    def generate_diagram(
        self,
        github_url: str,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        focus_area: str = "",
    ) -> Tuple[Optional[str], Optional[str], Optional[dict]]:
        """
        Generate diagram using Modal backend.
        
        Returns:
            Tuple of (dot_source, summary, stats) or (None, None, None) on failure
        """
        if not self.enabled:
            return None, None, None
        
        try:
            resp = requests.post(
                f"{self.base_url}/generate_diagram",
                json={
                    "github_url": github_url,
                    "api_key": api_key,
                    "model_name": model_name,
                    "focus_area": focus_area,
                },
                timeout=300,
            )
            
            data = resp.json()
            
            if data.get("success"):
                return (
                    data.get("dot_source"),
                    data.get("summary"),
                    data.get("stats"),
                )
            else:
                logger.error(f"Modal error: {data.get('error')}")
                return None, None, None
                
        except Exception as e:
            logger.error(f"Modal request failed: {e}")
            return None, None, None
    
    def generate_voice(
        self,
        text: str,
        api_key: str,
        voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
    ) -> Optional[bytes]:
        """
        Generate voice narration using Modal backend.
        
        Returns:
            Audio bytes or None on failure
        """
        if not self.enabled:
            return None
        
        try:
            resp = requests.post(
                f"{self.base_url}/generate_voice",
                json={
                    "text": text,
                    "api_key": api_key,
                    "voice_id": voice_id,
                },
                timeout=120,
            )
            
            data = resp.json()
            
            if data.get("success"):
                audio_base64 = data.get("audio_base64", "")
                return base64.b64decode(audio_base64)
            else:
                logger.error(f"Modal error: {data.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Modal request failed: {e}")
            return None
    
    def analyze_codebase(
        self,
        github_url: str,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        question: str = "",
    ) -> Optional[str]:
        """
        Analyze codebase using Modal backend.
        
        Returns:
            Analysis text or None on failure
        """
        if not self.enabled:
            return None
        
        try:
            resp = requests.post(
                f"{self.base_url}/analyze_codebase",
                json={
                    "github_url": github_url,
                    "api_key": api_key,
                    "model_name": model_name,
                    "question": question,
                },
                timeout=300,
            )
            
            data = resp.json()
            
            if data.get("success"):
                return data.get("analysis")
            else:
                logger.error(f"Modal error: {data.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Modal request failed: {e}")
            return None


# Global client instance
_modal_client: Optional[ModalClient] = None


def get_modal_client() -> ModalClient:
    """Get the global Modal client instance."""
    global _modal_client
    if _modal_client is None:
        _modal_client = ModalClient()
    return _modal_client
