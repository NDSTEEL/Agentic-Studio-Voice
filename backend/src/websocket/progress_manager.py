"""
Progress tracking manager for real-time updates.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any


class ProgressManager:
    """
    Manages progress tracking sessions for various operations.
    
    This class provides functionality to create, update, and complete
    progress tracking sessions, enabling real-time progress updates
    for long-running operations like agent creation.
    """
    
    def __init__(self):
        """Initialize the progress manager."""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_progress: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_session(self, session_type: str) -> str:
        """
        Create a new progress tracking session.
        
        Args:
            session_type: Type of session (e.g., 'agent_creation', 'knowledge_update')
        
        Returns:
            session_id: Unique identifier for the session
        """
        session_id = str(uuid.uuid4())
        
        self.active_sessions[session_id] = {
            "type": session_type,
            "status": "started",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "success": None,
            "result": None
        }
        
        self.session_progress[session_id] = []
        
        return session_id
    
    def update_progress(self, session_id: str, message: str, progress: int) -> None:
        """
        Update progress for a session.
        
        Args:
            session_id: Session identifier
            message: Progress message
            progress: Progress percentage (0-100)
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        progress_entry = {
            "message": message,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.session_progress[session_id].append(progress_entry)
        self.active_sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
    
    def complete_session(self, session_id: str, success: bool, result: str) -> None:
        """
        Mark a session as completed.
        
        Args:
            session_id: Session identifier
            success: Whether the operation was successful
            result: Result message
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        self.active_sessions[session_id].update({
            "status": "completed",
            "success": success,
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session status data or None if session doesn't exist
        """
        if session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id].copy()
        session_data["session_id"] = session_id
        session_data["progress"] = self.session_progress.get(session_id, [])
        
        return session_data
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed sessions.
        
        Args:
            max_age_hours: Maximum age of sessions to keep in hours
        
        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        sessions_to_remove = []
        
        for session_id, session_data in self.active_sessions.items():
            if session_data["status"] == "completed":
                created_at = datetime.fromisoformat(session_data["created_at"])
                if created_at.timestamp() < cutoff_time:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            del self.session_progress[session_id]
        
        return len(sessions_to_remove)
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active (non-completed) sessions.
        
        Returns:
            Dictionary of active sessions
        """
        active = {}
        for session_id, session_data in self.active_sessions.items():
            if session_data["status"] != "completed":
                active[session_id] = self.get_session_status(session_id)
        
        return active
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a session without full progress history.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session summary or None if session doesn't exist
        """
        if session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id].copy()
        session_data["session_id"] = session_id
        
        # Add latest progress if available
        progress_history = self.session_progress.get(session_id, [])
        if progress_history:
            session_data["latest_progress"] = progress_history[-1]
            session_data["progress_count"] = len(progress_history)
        else:
            session_data["latest_progress"] = None
            session_data["progress_count"] = 0
        
        return session_data