"""
Voice configuration and personality settings for ElevenLabs voice synthesis.
"""
from typing import Dict, Any, Optional


class VoiceConfig:
    """Configuration class for voice synthesis parameters."""
    
    def __init__(
        self,
        stability: float = 0.75,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
        model_id: str = "eleven_multilingual_v2"
    ):
        """
        Initialize voice configuration.
        
        Args:
            stability: Voice stability (0.0-1.0). Higher = more consistent
            similarity_boost: Similarity to original voice (0.0-1.0)
            style: Voice expressiveness (0.0-1.0). Higher = more expressive
            use_speaker_boost: Whether to use speaker boost for clarity
            model_id: ElevenLabs model ID to use
        """
        self.stability = self._validate_range(stability, "Stability")
        self.similarity_boost = self._validate_range(similarity_boost, "Similarity boost")
        self.style = self._validate_range(style, "Style")
        self.use_speaker_boost = use_speaker_boost
        self.model_id = model_id
    
    def _validate_range(self, value: float, parameter_name: str) -> float:
        """Validate that parameter is within 0.0-1.0 range."""
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"{parameter_name} must be between 0 and 1")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format for API calls.
        
        Returns:
            Dictionary with voice settings
        """
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "style": self.style,
            "use_speaker_boost": self.use_speaker_boost
        }
    
    @classmethod
    def from_personality(cls, personality_type: str) -> 'VoiceConfig':
        """
        Create voice configuration from personality type.
        
        Args:
            personality_type: Type of personality (professional, casual, energetic, etc.)
        
        Returns:
            VoiceConfig instance configured for the personality
        """
        personality_configs = {
            "professional": {
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": 0.2,
                "use_speaker_boost": True
            },
            "casual": {
                "stability": 0.6,
                "similarity_boost": 0.75,
                "style": 0.4,
                "use_speaker_boost": True
            },
            "energetic": {
                "stability": 0.5,
                "similarity_boost": 0.7,
                "style": 0.6,
                "use_speaker_boost": True
            },
            "authoritative": {
                "stability": 0.85,
                "similarity_boost": 0.8,
                "style": 0.1,
                "use_speaker_boost": True
            },
            "friendly": {
                "stability": 0.65,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            },
            "calm": {
                "stability": 0.9,
                "similarity_boost": 0.85,
                "style": 0.1,
                "use_speaker_boost": False
            },
            "conversational": {
                "stability": 0.6,
                "similarity_boost": 0.7,
                "style": 0.45,
                "use_speaker_boost": True
            },
            "corporate": {
                "stability": 0.8,
                "similarity_boost": 0.85,
                "style": 0.15,
                "use_speaker_boost": True
            }
        }
        
        if personality_type not in personality_configs:
            raise ValueError(f"Unknown personality type: {personality_type}")
        
        config = personality_configs[personality_type]
        return cls(**config)
    
    @classmethod
    def from_business_context(
        cls, 
        industry: str, 
        tone: str, 
        target_audience: str,
        brand_personality: list = None
    ) -> 'VoiceConfig':
        """
        Create voice configuration based on business context.
        
        Args:
            industry: Business industry
            tone: Communication tone
            target_audience: Target audience description
            brand_personality: List of brand personality traits
        
        Returns:
            VoiceConfig instance optimized for the business context
        """
        if brand_personality is None:
            brand_personality = []
        
        # Base configuration
        config = {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True
        }
        
        # Adjust based on industry
        industry_adjustments = {
            "finance": {"stability": 0.85, "style": 0.15},
            "legal": {"stability": 0.9, "style": 0.1},
            "healthcare": {"stability": 0.8, "style": 0.25},
            "technology": {"stability": 0.7, "style": 0.4},
            "education": {"stability": 0.75, "style": 0.3},
            "marketing": {"stability": 0.6, "style": 0.5},
            "entertainment": {"stability": 0.5, "style": 0.6},
            "consulting": {"stability": 0.8, "style": 0.2},
            "retail": {"stability": 0.65, "style": 0.45}
        }
        
        for industry_key, adjustments in industry_adjustments.items():
            if industry_key.lower() in industry.lower():
                config.update(adjustments)
                break
        
        # Adjust based on tone
        tone_adjustments = {
            "professional": {"stability": 0.8, "style": 0.2},
            "casual": {"stability": 0.6, "style": 0.4},
            "formal": {"stability": 0.85, "style": 0.15},
            "energetic": {"stability": 0.55, "style": 0.55},
            "authoritative": {"stability": 0.85, "style": 0.1},
            "friendly": {"stability": 0.65, "style": 0.45},
            "conversational": {"stability": 0.6, "style": 0.4}
        }
        
        for tone_key, adjustments in tone_adjustments.items():
            if tone_key.lower() in tone.lower():
                config.update(adjustments)
                break
        
        # Adjust based on target audience
        if "executives" in target_audience.lower() or "leadership" in target_audience.lower():
            config["stability"] = min(config["stability"] + 0.1, 1.0)
            config["style"] = max(config["style"] - 0.1, 0.0)
        elif "young" in target_audience.lower() or "millennials" in target_audience.lower():
            config["style"] = min(config["style"] + 0.1, 1.0)
        elif "seniors" in target_audience.lower():
            config["stability"] = min(config["stability"] + 0.1, 1.0)
            config["style"] = max(config["style"] - 0.1, 0.0)
        
        # Adjust based on brand personality
        for trait in brand_personality:
            trait_lower = trait.lower()
            if trait_lower in ["energetic", "dynamic", "vibrant"]:
                config["style"] = min(config["style"] + 0.1, 1.0)
                config["stability"] = max(config["stability"] - 0.05, 0.0)
            elif trait_lower in ["reliable", "trustworthy", "stable"]:
                config["stability"] = min(config["stability"] + 0.1, 1.0)
                config["style"] = max(config["style"] - 0.05, 0.0)
            elif trait_lower in ["innovative", "creative", "bold"]:
                config["style"] = min(config["style"] + 0.15, 1.0)
            elif trait_lower in ["calm", "peaceful", "zen"]:
                config["stability"] = min(config["stability"] + 0.1, 1.0)
                config["style"] = max(config["style"] - 0.1, 0.0)
                config["use_speaker_boost"] = False
        
        return cls(**config)
    
    def adjust_for_content_type(self, content_type: str) -> 'VoiceConfig':
        """
        Create a new configuration adjusted for specific content type.
        
        Args:
            content_type: Type of content (announcement, conversation, presentation, etc.)
        
        Returns:
            New VoiceConfig instance adjusted for content type
        """
        adjustments = {
            "announcement": {"stability": 0.85, "style": 0.3},
            "presentation": {"stability": 0.8, "style": 0.25},
            "conversation": {"stability": 0.65, "style": 0.45},
            "narration": {"stability": 0.75, "style": 0.35},
            "advertisement": {"stability": 0.6, "style": 0.55},
            "tutorial": {"stability": 0.8, "style": 0.2},
            "storytelling": {"stability": 0.65, "style": 0.5},
            "phone_greeting": {"stability": 0.75, "style": 0.3},
            "voicemail": {"stability": 0.8, "style": 0.25}
        }
        
        if content_type not in adjustments:
            return self
        
        adjustment = adjustments[content_type]
        
        return VoiceConfig(
            stability=adjustment.get("stability", self.stability),
            similarity_boost=self.similarity_boost,
            style=adjustment.get("style", self.style),
            use_speaker_boost=self.use_speaker_boost,
            model_id=self.model_id
        )
    
    def get_optimization_suggestions(self) -> Dict[str, str]:
        """
        Get suggestions for optimizing voice configuration.
        
        Returns:
            Dictionary with optimization suggestions
        """
        suggestions = {}
        
        if self.stability < 0.5:
            suggestions["stability"] = "Consider increasing stability for more consistent voice output"
        elif self.stability > 0.9:
            suggestions["stability"] = "High stability may sound robotic. Consider slight reduction for naturalness"
        
        if self.style > 0.7:
            suggestions["style"] = "High style values may sound over-expressive for professional content"
        elif self.style < 0.1:
            suggestions["style"] = "Very low style may sound monotone. Consider slight increase"
        
        if self.similarity_boost < 0.6:
            suggestions["similarity_boost"] = "Low similarity boost may not maintain voice characteristics well"
        
        # Combination suggestions
        if self.stability > 0.8 and self.style > 0.5:
            suggestions["balance"] = "High stability with high style may create conflicting effects"
        
        return suggestions
    
    def __str__(self) -> str:
        """String representation of the voice configuration."""
        return (f"VoiceConfig(stability={self.stability}, similarity_boost={self.similarity_boost}, "
                f"style={self.style}, use_speaker_boost={self.use_speaker_boost}, model={self.model_id})")
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return self.__str__()