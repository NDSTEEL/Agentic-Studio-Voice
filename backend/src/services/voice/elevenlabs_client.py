"""
ElevenLabs API client for voice synthesis and cloning.
"""
import requests
from typing import List, Dict, Optional, Any
import json


class ElevenLabsClient:
    """Client for interacting with ElevenLabs API."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.elevenlabs.io/v1", timeout: int = 30):
        """
        Initialize the ElevenLabs client.
        
        Args:
            api_key: ElevenLabs API key
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
    
    def get_voices(self) -> List[Dict[str, Any]]:
        """
        Retrieve available voices from ElevenLabs.
        
        Returns:
            List of voice dictionaries with voice_id, name, and category
        """
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}
        
        response = requests.get(url, headers=headers, timeout=self.timeout)
        
        if response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text}")
        
        return response.json().get("voices", [])
    
    def clone_voice(self, voice_name: str, audio_files: List[bytes]) -> Dict[str, str]:
        """
        Clone a voice from audio samples.
        
        Args:
            voice_name: Name for the cloned voice
            audio_files: List of audio file data (bytes)
        
        Returns:
            Dictionary containing the new voice_id
        """
        url = f"{self.base_url}/voices/add"
        headers = {"xi-api-key": self.api_key}
        
        # Prepare files for multipart upload
        files = []
        for i, audio_data in enumerate(audio_files):
            files.append(('files', (f'sample_{i}.wav', audio_data, 'audio/wav')))
        
        # Prepare form data
        data = {'name': voice_name}
        
        response = requests.post(url, headers=headers, files=files, data=data, timeout=self.timeout)
        
        if response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text}")
        
        return response.json()
    
    def synthesize_speech(
        self, 
        voice_id: str, 
        text: str, 
        model_id: str = "eleven_multilingual_v2",
        voice_settings: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Synthesize speech from text using a specific voice.
        
        Args:
            voice_id: ID of the voice to use
            text: Text to synthesize
            model_id: Model to use for synthesis
            voice_settings: Voice configuration settings
        
        Returns:
            Audio data as bytes
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Default voice settings
        if voice_settings is None:
            voice_settings = {
                "stability": 0.75,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        
        if response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text}")
        
        return response.content
    
    def get_voice_settings(self, voice_id: str) -> Dict[str, Any]:
        """
        Get current settings for a specific voice.
        
        Args:
            voice_id: ID of the voice
        
        Returns:
            Voice settings dictionary
        """
        url = f"{self.base_url}/voices/{voice_id}/settings"
        headers = {"xi-api-key": self.api_key}
        
        response = requests.get(url, headers=headers, timeout=self.timeout)
        
        if response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text}")
        
        return response.json()
    
    def update_voice_settings(self, voice_id: str, settings: Dict[str, Any]) -> bool:
        """
        Update settings for a specific voice.
        
        Args:
            voice_id: ID of the voice
            settings: New voice settings
        
        Returns:
            True if successful
        """
        url = f"{self.base_url}/voices/{voice_id}/settings/edit"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json=settings, timeout=self.timeout)
        
        if response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text}")
        
        return True