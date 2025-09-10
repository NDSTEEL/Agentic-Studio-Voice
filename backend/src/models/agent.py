"""
Agent Model Alias
Alias for VoiceAgent model to maintain compatibility with tests
"""

# Import the actual VoiceAgent model
from .voice_agent import VoiceAgent

# Create alias for backward compatibility
__all__ = ['VoiceAgent']