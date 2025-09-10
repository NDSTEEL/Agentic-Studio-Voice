"""
Call Logger
Handles call logging and recording functionality for agent performance monitoring
"""
import json
import os
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging
import uuid
import csv
from io import StringIO

logger = logging.getLogger(__name__)


class CallStatus(Enum):
    """Call status enumeration"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DROPPED = "dropped"
    TIMEOUT = "timeout"


@dataclass
class CallRecord:
    """Individual call record with all metadata"""
    call_id: str
    agent_id: str
    tenant_id: str
    caller_number: str
    start_time: datetime
    status: CallStatus
    duration: float = 0.0
    end_time: Optional[datetime] = None
    end_reason: Optional[str] = None
    customer_satisfaction: Optional[int] = None
    events: List[Dict[str, Any]] = field(default_factory=list)
    recording_file: Optional[str] = None
    recording_size: int = 0
    transcription: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat() if self.end_time else None
        data['status'] = self.status.value
        return data
    
    def calculate_duration(self) -> float:
        """Calculate call duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()


class TranscriptionService:
    """Mock transcription service for call recordings"""
    
    def __init__(self):
        self.enabled = False
    
    def transcribe_audio(self, audio_file: str) -> Dict[str, Any]:
        """Transcribe audio file to text"""
        # Mock implementation for testing
        return {
            'text': 'Hello, this is a test conversation.',
            'confidence': 0.92,
            'words': [
                {'word': 'Hello', 'start': 0.0, 'end': 0.5},
                {'word': 'this', 'start': 0.6, 'end': 0.8}
            ]
        }


class CallLogger:
    """
    Call logging and recording system
    Handles call lifecycle logging, event tracking, and audio recording
    """
    
    def __init__(self, storage_path: str = "./call_logs"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Active calls being monitored
        self.active_calls: Dict[str, CallRecord] = {}
        
        # Completed call records
        self.call_records: Dict[str, CallRecord] = {}
        
        # Recording buffer for active calls
        self.recording_buffers: Dict[str, List[bytes]] = {}
        
        # Transcription service
        self.transcription_service = TranscriptionService()
        
        logger.info(f"CallLogger initialized with storage path: {self.storage_path}")
    
    def start_call(self,
                   call_id: str,
                   agent_id: str,
                   tenant_id: str,
                   caller_number: str,
                   enable_recording: bool = False,
                   enable_transcription: bool = False,
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start logging a new call
        
        Args:
            call_id: Unique call identifier
            agent_id: Agent handling the call
            tenant_id: Tenant identifier
            caller_number: Caller's phone number
            enable_recording: Whether to record audio
            enable_transcription: Whether to transcribe audio
            metadata: Additional call metadata
            
        Returns:
            Result dictionary with call start status
        """
        try:
            if call_id in self.active_calls:
                logger.warning(f"Call {call_id} already active, stopping previous")
                self.end_call(call_id, 'replaced')
            
            call_record = CallRecord(
                call_id=call_id,
                agent_id=agent_id,
                tenant_id=tenant_id,
                caller_number=caller_number,
                start_time=datetime.now(),
                status=CallStatus.IN_PROGRESS,
                metadata=metadata or {}
            )
            
            # Enable recording if requested
            if enable_recording:
                call_record.metadata['recording_enabled'] = True
                call_record.metadata['transcription_enabled'] = enable_transcription
                self.recording_buffers[call_id] = []
            
            self.active_calls[call_id] = call_record
            
            logger.info(f"Started call logging for {call_id} with agent {agent_id}")
            
            return {
                'status': 'started',
                'call_id': call_id,
                'recording_enabled': enable_recording,
                'transcription_enabled': enable_transcription
            }
            
        except Exception as e:
            logger.error(f"Error starting call {call_id}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def log_event(self, call_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log an event during the call
        
        Args:
            call_id: Call identifier
            event: Event data to log
            
        Returns:
            Result dictionary with logging status
        """
        try:
            if call_id not in self.active_calls:
                logger.warning(f"Call {call_id} not found in active calls")
                return {'status': 'error', 'error': 'Call not found'}
            
            # Add timestamp if not present
            if 'timestamp' not in event:
                event['timestamp'] = datetime.now()
            
            # Convert datetime to ISO format for JSON serialization
            if isinstance(event.get('timestamp'), datetime):
                event['timestamp'] = event['timestamp'].isoformat()
            
            self.active_calls[call_id].events.append(event)
            
            logger.debug(f"Logged event for call {call_id}: {event.get('type', 'unknown')}")
            
            return {'status': 'logged', 'event_count': len(self.active_calls[call_id].events)}
            
        except Exception as e:
            logger.error(f"Error logging event for call {call_id}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def record_audio_chunk(self, call_id: str, audio_chunk: bytes) -> Dict[str, Any]:
        """
        Record audio chunk for call
        
        Args:
            call_id: Call identifier
            audio_chunk: Audio data chunk
            
        Returns:
            Result dictionary with recording status
        """
        try:
            if call_id not in self.active_calls:
                return {'status': 'error', 'error': 'Call not found'}
            
            if call_id not in self.recording_buffers:
                return {'status': 'error', 'error': 'Recording not enabled for this call'}
            
            self.recording_buffers[call_id].append(audio_chunk)
            
            return {
                'status': 'recorded',
                'chunks_recorded': len(self.recording_buffers[call_id])
            }
            
        except Exception as e:
            logger.error(f"Error recording audio chunk for call {call_id}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def end_call(self,
                 call_id: str,
                 end_reason: str = 'completed',
                 customer_satisfaction: Optional[int] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        End call logging and finalize record
        
        Args:
            call_id: Call identifier
            end_reason: Reason for call ending
            customer_satisfaction: Customer satisfaction rating (1-10)
            metadata: Additional metadata
            
        Returns:
            Result dictionary with call end status and summary
        """
        try:
            if call_id not in self.active_calls:
                logger.warning(f"Call {call_id} not found in active calls")
                return {'status': 'error', 'error': 'Call not found'}
            
            call_record = self.active_calls[call_id]
            call_record.end_time = datetime.now()
            call_record.duration = call_record.calculate_duration()
            call_record.end_reason = end_reason
            call_record.customer_satisfaction = customer_satisfaction
            
            # Update status based on end reason
            if end_reason == 'completed':
                call_record.status = CallStatus.COMPLETED
            elif end_reason == 'dropped':
                call_record.status = CallStatus.DROPPED
            elif end_reason == 'timeout':
                call_record.status = CallStatus.TIMEOUT
            else:
                call_record.status = CallStatus.FAILED
            
            # Add additional metadata
            if metadata:
                call_record.metadata.update(metadata)
            
            # Process recording if enabled
            recording_result = self._process_recording(call_id, call_record)
            
            # Move to completed records
            self.call_records[call_id] = call_record
            del self.active_calls[call_id]
            
            # Clean up recording buffer
            if call_id in self.recording_buffers:
                del self.recording_buffers[call_id]
            
            # Save to persistent storage
            self._save_call_record(call_record)
            
            logger.info(f"Ended call {call_id} - Duration: {call_record.duration:.2f}s")
            
            result = {
                'status': 'completed',
                'call_id': call_id,
                'duration': call_record.duration,
                'event_count': len(call_record.events),
                'end_reason': end_reason
            }
            
            # Add recording info if available
            if recording_result:
                result.update(recording_result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error ending call {call_id}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def _process_recording(self, call_id: str, call_record: CallRecord) -> Optional[Dict[str, Any]]:
        """Process audio recording for completed call"""
        if call_id not in self.recording_buffers:
            return None
        
        try:
            audio_chunks = self.recording_buffers[call_id]
            if not audio_chunks:
                return None
            
            # Create recording file
            recording_filename = f"call_{call_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            recording_path = self.storage_path / "recordings" / recording_filename
            recording_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Combine audio chunks (mock implementation)
            combined_audio = b''.join(audio_chunks)
            
            # Save recording file (mock)
            with open(recording_path, 'wb') as f:
                f.write(combined_audio)
            
            call_record.recording_file = str(recording_path)
            call_record.recording_size = len(combined_audio)
            
            # Process transcription if enabled
            transcription_result = None
            if call_record.metadata.get('transcription_enabled', False):
                transcription_result = self._process_transcription(recording_path, call_record)
            
            result = {
                'recording_file': str(recording_path),
                'recording_size': len(combined_audio),
                'transcription_available': transcription_result is not None
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing recording for call {call_id}: {str(e)}")
            return None
    
    def _process_transcription(self, recording_path: Path, call_record: CallRecord) -> Optional[Dict[str, Any]]:
        """Process transcription for recorded call"""
        try:
            transcription = self.transcription_service.transcribe_audio(str(recording_path))
            call_record.transcription = transcription
            return transcription
        except Exception as e:
            logger.error(f"Error processing transcription: {str(e)}")
            return None
    
    def _save_call_record(self, call_record: CallRecord):
        """Save call record to persistent storage"""
        try:
            # Create date-based directory structure
            date_dir = self.storage_path / "calls" / call_record.start_time.strftime('%Y-%m-%d')
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Save as JSON
            filename = f"call_{call_record.call_id}.json"
            filepath = date_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(call_record.to_dict(), f, indent=2, default=str)
                
            logger.debug(f"Saved call record to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving call record {call_record.call_id}: {str(e)}")
    
    def search_calls(self,
                     agent_id: Optional[str] = None,
                     tenant_id: Optional[str] = None,
                     status: Optional[CallStatus] = None,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None,
                     caller_number: Optional[str] = None,
                     limit: int = 100) -> List[CallRecord]:
        """
        Search call records with filters
        
        Args:
            agent_id: Filter by agent
            tenant_id: Filter by tenant
            status: Filter by call status
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            caller_number: Filter by caller number
            limit: Maximum number of results
            
        Returns:
            List of matching call records
        """
        results = []
        
        # Search completed records
        for call_record in self.call_records.values():
            if self._matches_filter(call_record, agent_id, tenant_id, status, 
                                  start_date, end_date, caller_number):
                results.append(call_record)
        
        # Search active records if no status filter or status matches
        if not status or status == CallStatus.IN_PROGRESS:
            for call_record in self.active_calls.values():
                if self._matches_filter(call_record, agent_id, tenant_id, status,
                                      start_date, end_date, caller_number):
                    results.append(call_record)
        
        # Sort by start time (newest first)
        results.sort(key=lambda x: x.start_time, reverse=True)
        
        return results[:limit]
    
    def _matches_filter(self, call_record: CallRecord,
                       agent_id: Optional[str],
                       tenant_id: Optional[str],
                       status: Optional[CallStatus],
                       start_date: Optional[datetime],
                       end_date: Optional[datetime],
                       caller_number: Optional[str]) -> bool:
        """Check if call record matches search filters"""
        if agent_id and call_record.agent_id != agent_id:
            return False
        
        if tenant_id and call_record.tenant_id != tenant_id:
            return False
        
        if status and call_record.status != status:
            return False
        
        if start_date and call_record.start_time.date() < start_date.date():
            return False
        
        if end_date and call_record.start_time.date() > end_date.date():
            return False
        
        if caller_number and caller_number not in call_record.caller_number:
            return False
        
        return True
    
    def generate_analytics(self,
                          agent_id: Optional[str] = None,
                          tenant_id: Optional[str] = None,
                          time_period: timedelta = timedelta(days=7)) -> Dict[str, Any]:
        """
        Generate analytics for call data
        
        Args:
            agent_id: Filter by agent
            tenant_id: Filter by tenant
            time_period: Time period for analysis
            
        Returns:
            Analytics dictionary with key metrics
        """
        # Get calls within time period
        end_date = datetime.now()
        start_date = end_date - time_period
        
        calls = self.search_calls(
            agent_id=agent_id,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Large limit for analytics
        )
        
        if not calls:
            return {
                'total_calls': 0,
                'time_period_days': time_period.days
            }
        
        # Calculate metrics
        total_calls = len(calls)
        completed_calls = len([c for c in calls if c.status == CallStatus.COMPLETED])
        dropped_calls = len([c for c in calls if c.status == CallStatus.DROPPED])
        failed_calls = len([c for c in calls if c.status == CallStatus.FAILED])
        
        # Duration analytics
        completed_durations = [c.duration for c in calls if c.status == CallStatus.COMPLETED]
        average_duration = sum(completed_durations) / len(completed_durations) if completed_durations else 0
        
        # Satisfaction analytics
        satisfaction_scores = [c.customer_satisfaction for c in calls 
                             if c.customer_satisfaction is not None]
        average_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
        
        return {
            'total_calls': total_calls,
            'completed_calls': completed_calls,
            'dropped_calls': dropped_calls,
            'failed_calls': failed_calls,
            'completion_rate': completed_calls / total_calls if total_calls > 0 else 0,
            'average_duration': average_duration,
            'average_satisfaction': average_satisfaction,
            'time_period_days': time_period.days,
            'calls_per_day': total_calls / time_period.days if time_period.days > 0 else total_calls
        }
    
    def export_call_data(self,
                        calls: List[CallRecord],
                        format: str = 'json',
                        include_events: bool = True,
                        include_transcriptions: bool = False) -> str:
        """
        Export call data in specified format
        
        Args:
            calls: List of call records to export
            format: Export format ('json', 'csv')
            include_events: Whether to include event data
            include_transcriptions: Whether to include transcription data
            
        Returns:
            Exported data as string
        """
        if format == 'json':
            return self._export_json(calls, include_events, include_transcriptions)
        elif format == 'csv':
            return self._export_csv(calls, include_events)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, calls: List[CallRecord], 
                    include_events: bool, include_transcriptions: bool) -> str:
        """Export calls to JSON format"""
        export_data = []
        
        for call in calls:
            call_data = call.to_dict()
            
            if not include_events:
                call_data.pop('events', None)
            
            if not include_transcriptions:
                call_data.pop('transcription', None)
            
            export_data.append(call_data)
        
        return json.dumps(export_data, indent=2, default=str)
    
    def _export_csv(self, calls: List[CallRecord], include_events: bool) -> str:
        """Export calls to CSV format"""
        output = StringIO()
        
        if not calls:
            return ""
        
        # Define CSV headers
        headers = [
            'call_id', 'agent_id', 'tenant_id', 'caller_number',
            'start_time', 'end_time', 'duration', 'status',
            'end_reason', 'customer_satisfaction', 'event_count'
        ]
        
        if include_events:
            headers.append('events')
        
        writer = csv.writer(output)
        writer.writerow(headers)
        
        # Write call data
        for call in calls:
            row = [
                call.call_id,
                call.agent_id,
                call.tenant_id,
                call.caller_number,
                call.start_time.isoformat(),
                call.end_time.isoformat() if call.end_time else '',
                call.duration,
                call.status.value,
                call.end_reason or '',
                call.customer_satisfaction or '',
                len(call.events)
            ]
            
            if include_events:
                row.append(json.dumps(call.events))
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def get_call_summary(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary of specific call
        
        Args:
            call_id: Call identifier
            
        Returns:
            Call summary dictionary or None if not found
        """
        call_record = None
        
        # Check active calls first
        if call_id in self.active_calls:
            call_record = self.active_calls[call_id]
        # Check completed calls
        elif call_id in self.call_records:
            call_record = self.call_records[call_id]
        
        if not call_record:
            return None
        
        return {
            'call_id': call_record.call_id,
            'agent_id': call_record.agent_id,
            'tenant_id': call_record.tenant_id,
            'caller_number': call_record.caller_number,
            'start_time': call_record.start_time.isoformat(),
            'end_time': call_record.end_time.isoformat() if call_record.end_time else None,
            'duration': call_record.duration,
            'status': call_record.status.value,
            'end_reason': call_record.end_reason,
            'customer_satisfaction': call_record.customer_satisfaction,
            'event_count': len(call_record.events),
            'recording_available': call_record.recording_file is not None,
            'transcription_available': call_record.transcription is not None
        }