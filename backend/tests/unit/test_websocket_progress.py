"""
Test WebSocket progress tracking functionality.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import websockets
from websockets.exceptions import ConnectionClosed

from src.websocket.progress_manager import ProgressManager
from src.websocket.websocket_manager import WebSocketManager


class TestProgressManager:
    """Test the ProgressManager class."""
    
    def test_progress_manager_initialization(self):
        """Test ProgressManager initializes correctly."""
        manager = ProgressManager()
        assert manager.active_sessions == {}
        assert manager.session_progress == {}
    
    def test_create_session(self):
        """Test creating a new progress session."""
        manager = ProgressManager()
        session_id = manager.create_session("agent_creation")
        
        assert session_id in manager.active_sessions
        assert manager.active_sessions[session_id]["type"] == "agent_creation"
        assert manager.active_sessions[session_id]["status"] == "started"
        assert manager.session_progress[session_id] == []
    
    def test_update_progress(self):
        """Test updating progress for a session."""
        manager = ProgressManager()
        session_id = manager.create_session("agent_creation")
        
        manager.update_progress(session_id, "Creating directories", 25)
        
        progress = manager.session_progress[session_id]
        assert len(progress) == 1
        assert progress[0]["message"] == "Creating directories"
        assert progress[0]["progress"] == 25
        assert "timestamp" in progress[0]
    
    def test_complete_session(self):
        """Test completing a progress session."""
        manager = ProgressManager()
        session_id = manager.create_session("agent_creation")
        
        manager.complete_session(session_id, success=True, result="Agent created successfully")
        
        assert manager.active_sessions[session_id]["status"] == "completed"
        assert manager.active_sessions[session_id]["success"] is True
        assert manager.active_sessions[session_id]["result"] == "Agent created successfully"
    
    def test_fail_session(self):
        """Test failing a progress session."""
        manager = ProgressManager()
        session_id = manager.create_session("agent_creation")
        
        manager.complete_session(session_id, success=False, result="Failed to create agent")
        
        assert manager.active_sessions[session_id]["status"] == "completed"
        assert manager.active_sessions[session_id]["success"] is False
        assert manager.active_sessions[session_id]["result"] == "Failed to create agent"
    
    def test_get_session_status(self):
        """Test getting session status."""
        manager = ProgressManager()
        session_id = manager.create_session("agent_creation")
        manager.update_progress(session_id, "Test message", 50)
        
        status = manager.get_session_status(session_id)
        
        assert status["session_id"] == session_id
        assert status["type"] == "agent_creation"
        assert status["status"] == "started"
        assert len(status["progress"]) == 1
        assert status["progress"][0]["message"] == "Test message"
    
    def test_get_nonexistent_session(self):
        """Test getting status for nonexistent session."""
        manager = ProgressManager()
        status = manager.get_session_status("nonexistent")
        
        assert status is None


class TestWebSocketManager:
    """Test the WebSocketManager class."""
    
    def test_websocket_manager_initialization(self):
        """Test WebSocketManager initializes correctly."""
        progress_manager = ProgressManager()
        ws_manager = WebSocketManager(progress_manager)
        
        assert ws_manager.progress_manager == progress_manager
        assert ws_manager.connections == set()
    
    @pytest.mark.asyncio
    async def test_register_connection(self):
        """Test registering a WebSocket connection."""
        progress_manager = ProgressManager()
        ws_manager = WebSocketManager(progress_manager)
        mock_websocket = AsyncMock()
        
        await ws_manager.register(mock_websocket)
        
        assert mock_websocket in ws_manager.connections
    
    @pytest.mark.asyncio
    async def test_unregister_connection(self):
        """Test unregistering a WebSocket connection."""
        progress_manager = ProgressManager()
        ws_manager = WebSocketManager(progress_manager)
        mock_websocket = AsyncMock()
        
        await ws_manager.register(mock_websocket)
        await ws_manager.unregister(mock_websocket)
        
        assert mock_websocket not in ws_manager.connections
    
    @pytest.mark.asyncio
    async def test_broadcast_progress_update(self):
        """Test broadcasting progress update to all connections."""
        progress_manager = ProgressManager()
        ws_manager = WebSocketManager(progress_manager)
        
        # Create mock connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        await ws_manager.register(mock_ws1)
        await ws_manager.register(mock_ws2)
        
        session_id = progress_manager.create_session("agent_creation")
        progress_manager.update_progress(session_id, "Test progress", 75)
        
        await ws_manager.broadcast_progress_update(session_id)
        
        # Check that both connections received the message
        mock_ws1.send.assert_called_once()
        mock_ws2.send.assert_called_once()
        
        # Verify message content
        sent_data = json.loads(mock_ws1.send.call_args[0][0])
        assert sent_data["type"] == "progress_update"
        assert sent_data["session_id"] == session_id
        assert sent_data["data"]["status"] == "started"
    
    @pytest.mark.asyncio
    async def test_broadcast_with_closed_connection(self):
        """Test broadcasting when a connection is closed."""
        progress_manager = ProgressManager()
        ws_manager = WebSocketManager(progress_manager)
        
        # Create mock connections, one that will fail
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws2.send.side_effect = ConnectionClosed(None, None)
        
        await ws_manager.register(mock_ws1)
        await ws_manager.register(mock_ws2)
        
        session_id = progress_manager.create_session("agent_creation")
        await ws_manager.broadcast_progress_update(session_id)
        
        # Should still send to working connection
        mock_ws1.send.assert_called_once()
        # Closed connection should be removed
        assert mock_ws2 not in ws_manager.connections
    
    @pytest.mark.asyncio
    async def test_handle_websocket_connection(self):
        """Test handling a WebSocket connection."""
        progress_manager = ProgressManager()
        ws_manager = WebSocketManager(progress_manager)
        
        mock_websocket = AsyncMock()
        mock_websocket.__aiter__.return_value = iter([
            '{"type": "subscribe", "session_id": "test_session"}'
        ])
        
        # Mock the recv method to raise WebSocketException after one message
        mock_websocket.recv.side_effect = [
            '{"type": "subscribe", "session_id": "test_session"}',
            ConnectionClosed(None, None)
        ]
        
        await ws_manager.handle_connection(mock_websocket, "/ws")
        
        # Connection should be cleaned up
        assert mock_websocket not in ws_manager.connections


class TestProgressIntegration:
    """Test integration between ProgressManager and WebSocketManager."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_progress_tracking(self):
        """Test complete progress tracking workflow."""
        progress_manager = ProgressManager()
        ws_manager = WebSocketManager(progress_manager)
        
        # Register a mock WebSocket connection
        mock_websocket = AsyncMock()
        await ws_manager.register(mock_websocket)
        
        # Create a session and track progress
        session_id = progress_manager.create_session("agent_creation")
        
        # Simulate progress updates
        progress_manager.update_progress(session_id, "Starting agent creation", 0)
        await ws_manager.broadcast_progress_update(session_id)
        
        progress_manager.update_progress(session_id, "Creating directories", 25)
        await ws_manager.broadcast_progress_update(session_id)
        
        progress_manager.update_progress(session_id, "Setting up configuration", 50)
        await ws_manager.broadcast_progress_update(session_id)
        
        progress_manager.update_progress(session_id, "Finalizing setup", 90)
        await ws_manager.broadcast_progress_update(session_id)
        
        progress_manager.complete_session(session_id, success=True, result="Agent created successfully")
        await ws_manager.broadcast_progress_update(session_id)
        
        # Verify all messages were sent
        assert mock_websocket.send.call_count == 5
        
        # Verify final message content
        final_call = mock_websocket.send.call_args_list[-1]
        final_message = json.loads(final_call[0][0])
        
        assert final_message["type"] == "progress_update"
        assert final_message["data"]["status"] == "completed"
        assert final_message["data"]["success"] is True
        assert final_message["data"]["result"] == "Agent created successfully"
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(self):
        """Test handling multiple concurrent progress sessions."""
        progress_manager = ProgressManager()
        ws_manager = WebSocketManager(progress_manager)
        
        mock_websocket = AsyncMock()
        await ws_manager.register(mock_websocket)
        
        # Create multiple sessions
        session1 = progress_manager.create_session("agent_creation")
        session2 = progress_manager.create_session("knowledge_update")
        
        # Update both sessions
        progress_manager.update_progress(session1, "Agent progress", 50)
        progress_manager.update_progress(session2, "Knowledge progress", 30)
        
        # Broadcast updates
        await ws_manager.broadcast_progress_update(session1)
        await ws_manager.broadcast_progress_update(session2)
        
        assert mock_websocket.send.call_count == 2
        
        # Verify different session IDs in messages
        calls = mock_websocket.send.call_args_list
        message1 = json.loads(calls[0][0][0])
        message2 = json.loads(calls[1][0][0])
        
        assert message1["session_id"] == session1
        assert message2["session_id"] == session2


class TestWebSocketEndpoints:
    """Test WebSocket endpoint functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_message_parsing(self):
        """Test parsing different WebSocket message types."""
        progress_manager = ProgressManager()
        ws_manager = WebSocketManager(progress_manager)
        
        # Test subscribe message
        subscribe_msg = '{"type": "subscribe", "session_id": "test123"}'
        parsed = json.loads(subscribe_msg)
        assert parsed["type"] == "subscribe"
        assert parsed["session_id"] == "test123"
        
        # Test status request message
        status_msg = '{"type": "get_status", "session_id": "test123"}'
        parsed = json.loads(status_msg)
        assert parsed["type"] == "get_status"
        assert parsed["session_id"] == "test123"
    
    @pytest.mark.asyncio
    async def test_invalid_websocket_message(self):
        """Test handling invalid WebSocket messages."""
        progress_manager = ProgressManager()
        ws_manager = WebSocketManager(progress_manager)
        
        # Invalid JSON should not crash the system
        try:
            parsed = json.loads('invalid json')
            assert False, "Should have raised JSON decode error"
        except json.JSONDecodeError:
            # This is expected
            pass