"""
Progress tracking utilities for real-time updates.
"""

import asyncio
import logging
from typing import Optional, Callable, Any
from contextlib import asynccontextmanager

from .progress_manager import ProgressManager
from .websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    A utility class for tracking progress of operations with real-time updates.
    
    This class provides a context manager for tracking long-running operations
    and automatically broadcasting updates via WebSocket.
    """
    
    def __init__(self, progress_manager: ProgressManager, websocket_manager: WebSocketManager):
        """
        Initialize the progress tracker.
        
        Args:
            progress_manager: The progress manager instance
            websocket_manager: The WebSocket manager instance
        """
        self.progress_manager = progress_manager
        self.websocket_manager = websocket_manager
    
    @asynccontextmanager
    async def track_operation(self, operation_type: str, description: str = ""):
        """
        Context manager for tracking an operation's progress.
        
        Args:
            operation_type: Type of operation (e.g., 'agent_creation')
            description: Optional description of the operation
        
        Yields:
            ProgressSession: A session object for updating progress
        """
        session_id = self.progress_manager.create_session(operation_type)
        session = ProgressSession(
            session_id=session_id,
            progress_manager=self.progress_manager,
            websocket_manager=self.websocket_manager,
            operation_type=operation_type,
            description=description
        )
        
        logger.info(f"Started progress tracking for {operation_type} (session: {session_id})")
        
        # Send initial update
        await self.websocket_manager.broadcast_progress_update(session_id)
        
        try:
            yield session
            
            # If we reach here without explicit completion, mark as successful
            if not session._completed:
                await session.complete(success=True, result="Operation completed successfully")
        
        except Exception as e:
            # Mark as failed if an exception occurred
            if not session._completed:
                await session.complete(
                    success=False, 
                    result=f"Operation failed: {str(e)}"
                )
            raise
        
        finally:
            logger.info(f"Finished progress tracking for {operation_type} (session: {session_id})")


class ProgressSession:
    """
    Represents a progress tracking session for a specific operation.
    """
    
    def __init__(
        self,
        session_id: str,
        progress_manager: ProgressManager,
        websocket_manager: WebSocketManager,
        operation_type: str,
        description: str = ""
    ):
        """
        Initialize a progress session.
        
        Args:
            session_id: Unique session identifier
            progress_manager: The progress manager instance
            websocket_manager: The WebSocket manager instance
            operation_type: Type of operation
            description: Optional description
        """
        self.session_id = session_id
        self.progress_manager = progress_manager
        self.websocket_manager = websocket_manager
        self.operation_type = operation_type
        self.description = description
        self._completed = False
        self._current_progress = 0
    
    async def update(self, message: str, progress: int) -> None:
        """
        Update the progress of this session.
        
        Args:
            message: Progress message
            progress: Progress percentage (0-100)
        """
        if self._completed:
            logger.warning(f"Attempted to update completed session {self.session_id}")
            return
        
        self.progress_manager.update_progress(self.session_id, message, progress)
        self._current_progress = progress
        
        # Broadcast the update
        await self.websocket_manager.broadcast_progress_update(self.session_id)
        
        logger.debug(f"Progress update [{self.session_id}]: {message} ({progress}%)")
    
    async def complete(self, success: bool, result: str) -> None:
        """
        Mark this session as completed.
        
        Args:
            success: Whether the operation was successful
            result: Result message
        """
        if self._completed:
            logger.warning(f"Session {self.session_id} already completed")
            return
        
        self.progress_manager.complete_session(self.session_id, success, result)
        self._completed = True
        
        # Broadcast completion
        await self.websocket_manager.broadcast_session_complete(self.session_id)
        
        status = "successful" if success else "failed"
        logger.info(f"Session {self.session_id} completed ({status}): {result}")
    
    async def step(self, message: str, progress_increment: int = 10) -> None:
        """
        Increment progress by a step.
        
        Args:
            message: Progress message
            progress_increment: Amount to increment progress by
        """
        new_progress = min(100, self._current_progress + progress_increment)
        await self.update(message, new_progress)
    
    def get_session_id(self) -> str:
        """Get the session ID."""
        return self.session_id
    
    def is_completed(self) -> bool:
        """Check if the session is completed."""
        return self._completed


# Convenience functions for common operations
async def track_agent_creation(
    progress_tracker: ProgressTracker,
    agent_name: str,
    creation_function: Callable,
    *args,
    **kwargs
) -> Any:
    """
    Track the progress of agent creation.
    
    Args:
        progress_tracker: The progress tracker instance
        agent_name: Name of the agent being created
        creation_function: Function that creates the agent
        *args: Arguments to pass to creation_function
        **kwargs: Keyword arguments to pass to creation_function
    
    Returns:
        Result of the creation function
    """
    async with progress_tracker.track_operation(
        "agent_creation", 
        f"Creating agent: {agent_name}"
    ) as session:
        await session.update("Initializing agent creation", 10)
        
        try:
            # Execute the creation function
            if asyncio.iscoroutinefunction(creation_function):
                result = await creation_function(*args, **kwargs)
            else:
                result = creation_function(*args, **kwargs)
            
            await session.update("Agent creation completed", 100)
            return result
            
        except Exception as e:
            await session.update(f"Agent creation failed: {str(e)}", 100)
            raise


async def track_knowledge_update(
    progress_tracker: ProgressTracker,
    update_function: Callable,
    *args,
    **kwargs
) -> Any:
    """
    Track the progress of knowledge base updates.
    
    Args:
        progress_tracker: The progress tracker instance
        update_function: Function that performs the update
        *args: Arguments to pass to update_function
        **kwargs: Keyword arguments to pass to update_function
    
    Returns:
        Result of the update function
    """
    async with progress_tracker.track_operation(
        "knowledge_update", 
        "Updating knowledge base"
    ) as session:
        await session.update("Starting knowledge update", 10)
        
        try:
            if asyncio.iscoroutinefunction(update_function):
                result = await update_function(*args, **kwargs)
            else:
                result = update_function(*args, **kwargs)
            
            await session.update("Knowledge update completed", 100)
            return result
            
        except Exception as e:
            await session.update(f"Knowledge update failed: {str(e)}", 100)
            raise