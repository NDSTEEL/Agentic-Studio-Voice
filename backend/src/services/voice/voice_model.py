"""
Voice model definitions and data structures.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum
import random


class VoiceProvider(Enum):
    """Voice service providers."""
    ELEVENLABS = "elevenlabs"
    AZURE = "azure"
    AWS_POLLY = "aws_polly"
    GOOGLE = "google"


class VoiceType(Enum):
    """Voice types."""
    PREMADE = "premade"
    CLONED = "cloned" 
    GENERATED = "generated"


class VoiceModel:
    """Voice model for business-driven voice generation."""
    
    def __init__(self, business_data: Dict[str, Any]):
        """Initialize with business data dictionary."""
        required_fields = ["company_name", "industry", "tone", "target_audience", "brand_personality"]
        
        missing_fields = [field for field in required_fields if field not in business_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        self.company_name = business_data["company_name"]
        self.industry = business_data["industry"]
        self.tone = business_data["tone"]
        self.target_audience = business_data["target_audience"]
        self.brand_personality = business_data["brand_personality"]
        
        # Optional fields
        self.voice_id = business_data.get("voice_id", f"voice_{self.company_name.lower()}")
        self.language = business_data.get("language", "en")
        self.provider = business_data.get("provider", VoiceProvider.ELEVENLABS)
        self.voice_type = business_data.get("voice_type", VoiceType.GENERATED)
    
    def generate_voice_description(self) -> str:
        """Generate voice description from business data."""
        personality_str = ", ".join(self.brand_personality)
        
        description = (
            f"A {self.tone} voice for {self.company_name}, targeting {self.target_audience} "
            f"in the {self.industry} industry. The voice should convey {personality_str} "
            f"characteristics and align with the company's brand values."
        )
        
        return description
    
    def get_voice_characteristics(self) -> Dict[str, str]:
        """Extract voice characteristics based on business data."""
        # Map tone to vocal characteristics
        tone_mapping = {
            "professional": {"pitch": "medium", "pace": "steady", "emphasis": "clear"},
            "friendly": {"pitch": "medium", "pace": "relaxed", "emphasis": "warm"},
            "authoritative": {"pitch": "low", "pace": "deliberate", "emphasis": "strong"},
            "casual": {"pitch": "high", "pace": "quick", "emphasis": "light"},
        }
        
        characteristics = tone_mapping.get(self.tone, {
            "pitch": "medium",
            "pace": "steady", 
            "emphasis": "clear"
        })
        
        return characteristics
    
    def generate_sample_scripts(self) -> List[str]:
        """Generate sample scripts for voice training."""
        scripts = []
        
        # Company introduction scripts
        scripts.append(
            f"Hello, welcome to {self.company_name}. We're leaders in the {self.industry} "
            f"industry, committed to providing {self.target_audience} with innovative solutions."
        )
        
        # Service-oriented script
        scripts.append(
            f"At {self.company_name}, we understand the needs of {self.target_audience}. "
            f"Our {self.tone} approach ensures you get the best service every time."
        )
        
        # Brand personality script
        personality = " and ".join(self.brand_personality)
        scripts.append(
            f"What makes {self.company_name} different? We're {personality}, "
            f"which means you can trust us to deliver excellence in everything we do."
        )
        
        # Common phrases script
        scripts.append(
            f"Thank you for choosing {self.company_name}. How can we help you today? "
            f"We're here to support {self.target_audience} with {self.tone} service."
        )
        
        return scripts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "voice_id": self.voice_id,
            "company_name": self.company_name,
            "industry": self.industry,
            "tone": self.tone,
            "target_audience": self.target_audience,
            "brand_personality": self.brand_personality,
            "language": self.language,
            "provider": self.provider.value if isinstance(self.provider, VoiceProvider) else self.provider,
            "voice_type": self.voice_type.value if isinstance(self.voice_type, VoiceType) else self.voice_type
        }


@dataclass
class VoiceConfiguration:
    """Traditional voice configuration for technical settings."""
    voice_id: str
    name: str
    provider: VoiceProvider
    voice_type: VoiceType
    language: str = "en"
    gender: Optional[str] = None
    accent: Optional[str] = None
    age: Optional[str] = None
    description: Optional[str] = None
    sample_rate: int = 22050
    settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "voice_id": self.voice_id,
            "name": self.name,
            "provider": self.provider.value,
            "voice_type": self.voice_type.value,
            "language": self.language,
            "gender": self.gender,
            "accent": self.accent,
            "age": self.age,
            "description": self.description,
            "sample_rate": self.sample_rate,
            "settings": self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceConfiguration':
        """Create from dictionary."""
        return cls(
            voice_id=data["voice_id"],
            name=data["name"],
            provider=VoiceProvider(data["provider"]),
            voice_type=VoiceType(data["voice_type"]),
            language=data.get("language", "en"),
            gender=data.get("gender"),
            accent=data.get("accent"),
            age=data.get("age"),
            description=data.get("description"),
            sample_rate=data.get("sample_rate", 22050),
            settings=data.get("settings", {})
        )