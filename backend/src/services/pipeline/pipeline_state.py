"""
Pipeline State Management
Tracks pipeline execution state and resources for rollback
"""
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4


class PipelineStatus(Enum):
    """Pipeline execution status states"""
    INITIALIZING = "initializing"
    WEB_CRAWLING = "web_crawling"
    CONTENT_EXTRACTION = "content_extraction"
    KNOWLEDGE_BASE_CREATION = "knowledge_base_creation"
    VOICE_AGENT_CREATION = "voice_agent_creation"
    PHONE_PROVISIONING = "phone_provisioning"
    FINAL_INTEGRATION = "final_integration"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


@dataclass
class StageResult:
    """Individual stage execution result"""
    stage_name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    
    def mark_completed(self, result_data: Dict[str, Any]):
        """Mark stage as completed with results"""
        self.end_time = datetime.now()
        self.result_data = result_data
        self.status = 'completed'
        if self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()
    
    def mark_failed(self, error_message: str):
        """Mark stage as failed with error"""
        self.end_time = datetime.now()
        self.error_message = error_message
        self.status = 'failed'
        if self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()


@dataclass
class CreatedResource:
    """Track resources created during pipeline for rollback"""
    resource_type: str  # 'agent', 'phone', 'webhook', etc.
    resource_id: str
    resource_data: Dict[str, Any]
    created_at: datetime
    stage_name: str
    rollback_method: str  # Method name to call for rollback
    rollback_priority: int = 0  # Higher priority rolled back first


@dataclass
class PipelineState:
    """Complete pipeline execution state"""
    pipeline_id: str = field(default_factory=lambda: str(uuid4()))
    tenant_id: str = ""
    status: PipelineStatus = PipelineStatus.INITIALIZING
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Execution tracking
    current_stage: Optional[str] = None
    completed_stages: List[str] = field(default_factory=list)
    failed_stages: List[str] = field(default_factory=list)
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    
    # Resource tracking for rollback
    created_resources: List[CreatedResource] = field(default_factory=list)
    
    # Pipeline configuration
    request_data: Dict[str, Any] = field(default_factory=dict)
    optimization_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    total_execution_time: Optional[float] = None
    stage_timing: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Error handling
    last_error: Optional[str] = None
    rollback_attempted: bool = False
    rollback_successful: bool = False
    
    def start_stage(self, stage_name: str) -> StageResult:
        """Start executing a pipeline stage"""
        self.current_stage = stage_name
        stage_result = StageResult(
            stage_name=stage_name,
            status='running',
            start_time=datetime.now()
        )
        self.stage_results[stage_name] = stage_result
        return stage_result
    
    def complete_stage(self, stage_name: str, result_data: Dict[str, Any]):
        """Mark stage as completed"""
        if stage_name in self.stage_results:
            self.stage_results[stage_name].mark_completed(result_data)
            self.completed_stages.append(stage_name)
            if stage_name == self.current_stage:
                self.current_stage = None
        
        # Update stage timing
        if stage_name in self.stage_results:
            execution_time = self.stage_results[stage_name].execution_time
            if execution_time:
                self.stage_timing[stage_name] = execution_time
    
    def fail_stage(self, stage_name: str, error_message: str):
        """Mark stage as failed"""
        if stage_name in self.stage_results:
            self.stage_results[stage_name].mark_failed(error_message)
            self.failed_stages.append(stage_name)
            self.last_error = error_message
            if stage_name == self.current_stage:
                self.current_stage = None
    
    def add_created_resource(self, 
                           resource_type: str, 
                           resource_id: str, 
                           resource_data: Dict[str, Any],
                           stage_name: str,
                           rollback_method: str,
                           rollback_priority: int = 0):
        """Track a resource created during pipeline execution"""
        resource = CreatedResource(
            resource_type=resource_type,
            resource_id=resource_id,
            resource_data=resource_data,
            created_at=datetime.now(),
            stage_name=stage_name,
            rollback_method=rollback_method,
            rollback_priority=rollback_priority
        )
        self.created_resources.append(resource)
    
    def get_resources_for_rollback(self) -> List[CreatedResource]:
        """Get resources sorted by rollback priority (highest first)"""
        return sorted(self.created_resources, 
                     key=lambda r: r.rollback_priority, 
                     reverse=True)
    
    def mark_completed(self):
        """Mark pipeline as completed"""
        self.status = PipelineStatus.COMPLETED
        self.completed_at = datetime.now()
        if self.started_at:
            self.total_execution_time = (self.completed_at - self.started_at).total_seconds()
    
    def mark_failed(self, error_message: str):
        """Mark pipeline as failed"""
        self.status = PipelineStatus.FAILED
        self.completed_at = datetime.now()
        self.last_error = error_message
        if self.started_at:
            self.total_execution_time = (self.completed_at - self.started_at).total_seconds()
    
    def start_rollback(self):
        """Mark pipeline as starting rollback"""
        self.status = PipelineStatus.ROLLING_BACK
        self.rollback_attempted = True
    
    def complete_rollback(self, successful: bool):
        """Mark rollback as completed"""
        self.status = PipelineStatus.ROLLED_BACK
        self.rollback_successful = successful
        if not hasattr(self, 'rollback_completed_at'):
            self.rollback_completed_at = datetime.now()
    
    def get_progress_percentage(self) -> float:
        """Calculate pipeline progress percentage"""
        total_stages = 6  # web_crawling, content_extraction, knowledge_base, agent_creation, phone, integration
        completed_count = len(self.completed_stages)
        return (completed_count / total_stages) * 100
    
    def get_time_remaining(self, max_execution_time: int = 180) -> float:
        """Get estimated time remaining in seconds"""
        elapsed = (datetime.now() - self.started_at).total_seconds()
        return max(0, max_execution_time - elapsed)
    
    def is_approaching_timeout(self, max_execution_time: int = 180, warning_threshold: int = 30) -> bool:
        """Check if pipeline is approaching timeout"""
        time_remaining = self.get_time_remaining(max_execution_time)
        return time_remaining <= warning_threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline state to dictionary for serialization"""
        return {
            'pipeline_id': self.pipeline_id,
            'tenant_id': self.tenant_id,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'current_stage': self.current_stage,
            'completed_stages': self.completed_stages,
            'failed_stages': self.failed_stages,
            'total_execution_time': self.total_execution_time,
            'stage_timing': self.stage_timing,
            'progress_percentage': self.get_progress_percentage(),
            'created_resources_count': len(self.created_resources),
            'last_error': self.last_error,
            'rollback_attempted': self.rollback_attempted,
            'rollback_successful': self.rollback_successful
        }