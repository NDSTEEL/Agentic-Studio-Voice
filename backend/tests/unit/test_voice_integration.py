"""
Test suite for ElevenLabs voice integration service.
TDD approach: Tests written first to define the expected behavior.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.services.voice.elevenlabs_client import ElevenLabsClient
from src.services.voice.voice_model import VoiceModel
from src.services.voice.voice_config import VoiceConfig


class TestElevenLabsClient:
    """Test ElevenLabs API client functionality."""
    
    @pytest.fixture
    def mock_api_key(self):
        return "test-api-key-123"
    
    @pytest.fixture
    def client(self, mock_api_key):
        return ElevenLabsClient(api_key=mock_api_key)
    
    def test_client_initialization(self, mock_api_key):
        """Test client initializes with proper configuration."""
        client = ElevenLabsClient(api_key=mock_api_key)
        assert client.api_key == mock_api_key
        assert client.base_url == "https://api.elevenlabs.io/v1"
        assert client.timeout == 30
    
    def test_client_initialization_without_api_key(self):
        """Test client raises error without API key."""
        with pytest.raises(ValueError, match="API key is required"):
            ElevenLabsClient(api_key=None)
    
    @patch('requests.get')
    def test_get_voices_success(self, mock_get, client):
        """Test successful retrieval of available voices."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": [
                {"voice_id": "voice1", "name": "Alice", "category": "premade"},
                {"voice_id": "voice2", "name": "Bob", "category": "cloned"}
            ]
        }
        mock_get.return_value = mock_response
        
        voices = client.get_voices()
        
        assert len(voices) == 2
        assert voices[0]["name"] == "Alice"
        mock_get.assert_called_once_with(
            f"{client.base_url}/voices",
            headers={"xi-api-key": client.api_key},
            timeout=client.timeout
        )
    
    @patch('requests.get')
    def test_get_voices_api_error(self, mock_get, client):
        """Test handling of API errors when getting voices."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="API error.*401"):
            client.get_voices()
    
    @patch('requests.post')
    def test_clone_voice_success(self, mock_post, client):
        """Test successful voice cloning from audio files."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"voice_id": "new_voice_123"}
        mock_post.return_value = mock_response
        
        audio_files = [b"audio_data_1", b"audio_data_2"]
        voice_name = "Custom Voice"
        
        result = client.clone_voice(voice_name, audio_files)
        
        assert result["voice_id"] == "new_voice_123"
        mock_post.assert_called_once()
        assert mock_post.call_args[1]["files"] is not None
    
    @patch('requests.post')
    def test_synthesize_speech_success(self, mock_post, client):
        """Test successful speech synthesis."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"audio_data"
        mock_post.return_value = mock_response
        
        voice_id = "voice123"
        text = "Hello, this is a test."
        
        audio_data = client.synthesize_speech(voice_id, text)
        
        assert audio_data == b"audio_data"
        mock_post.assert_called_once_with(
            f"{client.base_url}/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": client.api_key,
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            },
            timeout=client.timeout
        )
    
    def test_synthesize_speech_empty_text(self, client):
        """Test error handling for empty text input."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            client.synthesize_speech("voice123", "")


class TestVoiceModel:
    """Test voice model generation from business data."""
    
    @pytest.fixture
    def sample_business_data(self):
        return {
            "company_name": "TechCorp",
            "industry": "Technology",
            "tone": "professional",
            "target_audience": "business professionals",
            "brand_personality": ["innovative", "trustworthy", "approachable"]
        }
    
    def test_voice_model_initialization(self, sample_business_data):
        """Test voice model initializes with business data."""
        model = VoiceModel(sample_business_data)
        
        assert model.company_name == "TechCorp"
        assert model.industry == "Technology"
        assert model.tone == "professional"
        assert model.target_audience == "business professionals"
        assert model.brand_personality == ["innovative", "trustworthy", "approachable"]
    
    def test_generate_voice_description(self, sample_business_data):
        """Test generation of voice description from business data."""
        model = VoiceModel(sample_business_data)
        
        description = model.generate_voice_description()
        
        assert "TechCorp" in description
        assert "professional" in description
        assert "business professionals" in description
        assert len(description) > 50  # Reasonable length
    
    def test_get_voice_characteristics(self, sample_business_data):
        """Test extraction of voice characteristics."""
        model = VoiceModel(sample_business_data)
        
        characteristics = model.get_voice_characteristics()
        
        assert "pitch" in characteristics
        assert "pace" in characteristics
        assert "emphasis" in characteristics
        assert isinstance(characteristics["pitch"], str)
        assert characteristics["pitch"] in ["low", "medium", "high"]
    
    def test_generate_sample_scripts(self, sample_business_data):
        """Test generation of sample scripts for voice training."""
        model = VoiceModel(sample_business_data)
        
        scripts = model.generate_sample_scripts()
        
        assert isinstance(scripts, list)
        assert len(scripts) >= 3
        for script in scripts:
            assert len(script) > 20  # Reasonable length for training
            assert "TechCorp" in script  # Company name should be included
    
    def test_voice_model_missing_required_fields(self):
        """Test error handling for missing required business data."""
        incomplete_data = {"company_name": "TechCorp"}
        
        with pytest.raises(ValueError, match="Missing required fields"):
            VoiceModel(incomplete_data)


class TestVoiceConfig:
    """Test voice configuration and personality settings."""
    
    @pytest.fixture
    def default_config(self):
        return VoiceConfig()
    
    def test_default_configuration(self, default_config):
        """Test default voice configuration values."""
        assert default_config.stability == 0.75
        assert default_config.similarity_boost == 0.75
        assert default_config.style == 0.0
        assert default_config.use_speaker_boost is True
        assert default_config.model_id == "eleven_multilingual_v2"
    
    def test_custom_configuration(self):
        """Test custom voice configuration."""
        config = VoiceConfig(
            stability=0.5,
            similarity_boost=0.8,
            style=0.2,
            use_speaker_boost=False,
            model_id="custom_model"
        )
        
        assert config.stability == 0.5
        assert config.similarity_boost == 0.8
        assert config.style == 0.2
        assert config.use_speaker_boost is False
        assert config.model_id == "custom_model"
    
    def test_config_validation_stability(self):
        """Test validation of stability parameter."""
        with pytest.raises(ValueError, match="Stability must be between 0 and 1"):
            VoiceConfig(stability=1.5)
        
        with pytest.raises(ValueError, match="Stability must be between 0 and 1"):
            VoiceConfig(stability=-0.1)
    
    def test_config_validation_similarity_boost(self):
        """Test validation of similarity_boost parameter."""
        with pytest.raises(ValueError, match="Similarity boost must be between 0 and 1"):
            VoiceConfig(similarity_boost=2.0)
    
    def test_config_validation_style(self):
        """Test validation of style parameter."""
        with pytest.raises(ValueError, match="Style must be between 0 and 1"):
            VoiceConfig(style=-0.5)
    
    def test_to_dict(self, default_config):
        """Test conversion of config to dictionary."""
        config_dict = default_config.to_dict()
        
        expected_keys = ["stability", "similarity_boost", "style", "use_speaker_boost"]
        for key in expected_keys:
            assert key in config_dict
        assert config_dict["stability"] == 0.75
    
    def test_from_personality_professional(self):
        """Test config generation from professional personality."""
        config = VoiceConfig.from_personality("professional")
        
        assert config.stability >= 0.7  # Professional should be stable
        assert config.style <= 0.3      # Less expressive style
    
    def test_from_personality_casual(self):
        """Test config generation from casual personality."""
        config = VoiceConfig.from_personality("casual")
        
        assert config.stability <= 0.6  # More variation allowed
        assert config.style >= 0.3      # More expressive style
    
    def test_from_personality_energetic(self):
        """Test config generation from energetic personality."""
        config = VoiceConfig.from_personality("energetic")
        
        assert config.style >= 0.5      # High expressiveness
        assert config.use_speaker_boost is True
    
    def test_from_personality_unknown(self):
        """Test error handling for unknown personality."""
        with pytest.raises(ValueError, match="Unknown personality type"):
            VoiceConfig.from_personality("unknown_type")


class TestVoiceIntegrationWorkflow:
    """Integration tests for complete voice synthesis workflow."""
    
    @pytest.fixture
    def mock_elevenlabs_client(self):
        return Mock(spec=ElevenLabsClient)
    
    @pytest.fixture
    def business_data(self):
        return {
            "company_name": "InnovateAI",
            "industry": "Artificial Intelligence",
            "tone": "professional",
            "target_audience": "tech entrepreneurs",
            "brand_personality": ["cutting-edge", "reliable", "inspiring"]
        }
    
    def test_complete_voice_generation_workflow(self, mock_elevenlabs_client, business_data):
        """Test complete workflow from business data to voice synthesis."""
        # Setup mock responses
        mock_elevenlabs_client.get_voices.return_value = [
            {"voice_id": "voice1", "name": "Professional", "category": "premade"}
        ]
        mock_elevenlabs_client.clone_voice.return_value = {"voice_id": "custom_voice_123"}
        mock_elevenlabs_client.synthesize_speech.return_value = b"synthesized_audio_data"
        
        # Create voice model
        voice_model = VoiceModel(business_data)
        
        # Generate voice configuration
        config = VoiceConfig.from_personality("professional")
        
        # Generate sample scripts
        scripts = voice_model.generate_sample_scripts()
        
        # Simulate voice cloning (would normally use actual audio)
        audio_files = [b"mock_audio_1", b"mock_audio_2"]
        clone_result = mock_elevenlabs_client.clone_voice(
            f"{business_data['company_name']} Voice", 
            audio_files
        )
        
        # Synthesize speech with custom voice
        sample_text = "Welcome to InnovateAI, where cutting-edge technology meets reliable solutions."
        audio_data = mock_elevenlabs_client.synthesize_speech(
            clone_result["voice_id"], 
            sample_text
        )
        
        # Assertions
        assert len(scripts) >= 3
        assert clone_result["voice_id"] == "custom_voice_123"
        assert audio_data == b"synthesized_audio_data"
        assert config.stability == 0.75  # Professional personality
        
        # Verify method calls
        mock_elevenlabs_client.clone_voice.assert_called_once()
        mock_elevenlabs_client.synthesize_speech.assert_called_once()


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""
    
    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection timeout")
            
            client = ElevenLabsClient("test-key")
            with pytest.raises(Exception, match="Connection timeout"):
                client.get_voices()
    
    def test_invalid_audio_format(self):
        """Test handling of invalid audio formats for voice cloning."""
        client = ElevenLabsClient("test-key")
        
        invalid_audio = [b"not_audio_data"]
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Invalid audio format"
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception, match="API error.*400"):
                client.clone_voice("Test Voice", invalid_audio)
    
    def test_text_too_long_for_synthesis(self):
        """Test handling of text that's too long for synthesis."""
        client = ElevenLabsClient("test-key")
        
        # Text longer than typical API limits
        very_long_text = "This is a test. " * 1000
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 413
            mock_response.text = "Request entity too large"
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception, match="API error.*413"):
                client.synthesize_speech("voice123", very_long_text)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])