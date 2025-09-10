"""
Call record model for monitoring.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class CallStatus(Enum):
    """Call status enumeration."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DROPPED = "dropped"
    TIMEOUT = "timeout"


@dataclass
class CallRecord:
    """Call record data model."""
    call_id: str
    agent_id: str
    tenant_id: str
    caller_number: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    status: CallStatus = CallStatus.IN_PROGRESS
    end_reason: Optional[str] = None
    customer_satisfaction: Optional[int] = None
    events: Optional[List[Dict[str, Any]]] = None
    recording_file: Optional[str] = None
    recording_size: int = 0
    transcription: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "call_id": self.call_id,
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "caller_number": self.caller_number,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "status": self.status.value,
            "end_reason": self.end_reason,
            "customer_satisfaction": self.customer_satisfaction,
            "events": self.events,
            "recording_file": self.recording_file,
            "recording_size": self.recording_size,
            "transcription": self.transcription,
            "metadata": self.metadata
        }