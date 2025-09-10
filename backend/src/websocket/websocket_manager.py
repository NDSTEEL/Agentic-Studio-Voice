"""
WebSocket manager for real-time progress updates.
"""

import json
import logging
import asyncio
from typing import Set, Dict, Any
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from .progress_manager import ProgressManager

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts progress updates.
    
    This class handles WebSocket connections from clients and broadcasts
    real-time progress updates to all connected clients.
    """
    
    def __init__(self, progress_manager: ProgressManager):
        """
        Initialize the WebSocket manager.
        
        Args:
            progress_manager: The progress manager instance to use
        """
        self.progress_manager = progress_manager
        self.connections: Set[websockets.WebSocketServerProtocol] = set()
        self.subscriptions: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
    
    async def register(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to register
        """
        self.connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.connections)}")
    
    async def unregister(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """
        Unregister a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to unregister
        """
        self.connections.discard(websocket)
        
        # Remove from all subscriptions
        for session_id, subscribers in self.subscriptions.items():
            subscribers.discard(websocket)
        
        logger.info(f"Client disconnected. Total connections: {len(self.connections)}")
    
    async def subscribe_to_session(
        self, 
        websocket: websockets.WebSocketServerProtocol, 
        session_id: str
    ) -> None:
        """
        Subscribe a WebSocket connection to a specific session.
        
        Args:
            websocket: The WebSocket connection
            session_id: The session to subscribe to
        """
        if session_id not in self.subscriptions:
            self.subscriptions[session_id] = set()
        
        self.subscriptions[session_id].add(websocket)
        logger.info(f"Client subscribed to session {session_id}")
        
        # Send current session status immediately
        status = self.progress_manager.get_session_status(session_id)
        if status:
            await self._send_to_websocket(websocket, {
                "type": "progress_update",
                "session_id": session_id,
                "data": status
            })
    
    async def unsubscribe_from_session(
        self, 
        websocket: websockets.WebSocketServerProtocol, 
        session_id: str
    ) -> None:
        """
        Unsubscribe a WebSocket connection from a specific session.
        
        Args:
            websocket: The WebSocket connection
            session_id: The session to unsubscribe from
        """
        if session_id in self.subscriptions:
            self.subscriptions[session_id].discard(websocket)
            logger.info(f"Client unsubscribed from session {session_id}")
    
    async def broadcast_progress_update(self, session_id: str) -> None:
        """
        Broadcast a progress update to all subscribed connections.
        
        Args:
            session_id: The session that was updated
        """
        status = self.progress_manager.get_session_status(session_id)
        if not status:
            logger.warning(f"No status found for session {session_id}")
            return
        
        message = {
            "type": "progress_update",
            "session_id": session_id,
            "data": status
        }
        
        # Send to subscribers of this specific session
        subscribers = self.subscriptions.get(session_id, set())
        if subscribers:
            await self._broadcast_to_connections(subscribers, message)
        
        # Also broadcast to all general connections
        await self._broadcast_to_connections(self.connections, message)
    
    async def broadcast_session_complete(self, session_id: str) -> None:
        """
        Broadcast session completion to all subscribed connections.
        
        Args:
            session_id: The session that completed
        """
        status = self.progress_manager.get_session_status(session_id)
        if not status:
            return
        
        message = {
            "type": "session_complete",
            "session_id": session_id,
            "data": status
        }
        
        # Send to subscribers of this specific session
        subscribers = self.subscriptions.get(session_id, set())
        if subscribers:
            await self._broadcast_to_connections(subscribers, message)
        
        # Also broadcast to all general connections
        await self._broadcast_to_connections(self.connections, message)
    
    async def _broadcast_to_connections(
        self, 
        connections: Set[websockets.WebSocketServerProtocol], 
        message: Dict[str, Any]
    ) -> None:
        """
        Broadcast a message to a set of connections.
        
        Args:
            connections: Set of WebSocket connections
            message: Message to broadcast
        """
        if not connections:
            return
        
        # Create a copy of connections to avoid modification during iteration
        connections_copy = connections.copy()
        
        # Use asyncio.gather for concurrent sending
        tasks = []
        for websocket in connections_copy:
            tasks.append(self._send_to_websocket(websocket, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_to_websocket(
        self, 
        websocket: websockets.WebSocketServerProtocol, 
        message: Dict[str, Any]
    ) -> None:
        """
        Send a message to a single WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            message: Message to send
        """
        try:
            await websocket.send(json.dumps(message))
        except ConnectionClosed:
            logger.info("Connection closed during send")
            await self.unregister(websocket)
        except WebSocketException as e:
            logger.error(f"WebSocket error during send: {e}")
            await self.unregister(websocket)
        except Exception as e:
            logger.error(f"Unexpected error during send: {e}")
            await self.unregister(websocket)
    
    async def handle_connection(
        self, 
        websocket: websockets.WebSocketServerProtocol, 
        path: str
    ) -> None:
        """
        Handle a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            path: The WebSocket path
        """
        await self.register(websocket)
        
        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except ConnectionClosed:
            logger.info("Connection closed normally")
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error handling connection: {e}")
        finally:
            await self.unregister(websocket)
    
    async def _handle_message(
        self, 
        websocket: websockets.WebSocketServerProtocol, 
        message: str
    ) -> None:
        """
        Handle a message from a WebSocket client.
        
        Args:
            websocket: The WebSocket connection
            message: The message received
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                session_id = data.get("session_id")
                if session_id:
                    await self.subscribe_to_session(websocket, session_id)
                else:
                    await self._send_error(websocket, "Missing session_id for subscription")
            
            elif message_type == "unsubscribe":
                session_id = data.get("session_id")
                if session_id:
                    await self.unsubscribe_from_session(websocket, session_id)
                else:
                    await self._send_error(websocket, "Missing session_id for unsubscription")
            
            elif message_type == "get_status":
                session_id = data.get("session_id")
                if session_id:
                    status = self.progress_manager.get_session_status(session_id)
                    if status:
                        await self._send_to_websocket(websocket, {
                            "type": "status_response",
                            "session_id": session_id,
                            "data": status
                        })
                    else:
                        await self._send_error(websocket, f"Session {session_id} not found")
                else:
                    await self._send_error(websocket, "Missing session_id for status request")
            
            elif message_type == "get_active_sessions":
                active_sessions = self.progress_manager.get_active_sessions()
                await self._send_to_websocket(websocket, {
                    "type": "active_sessions_response",
                    "data": active_sessions
                })
            
            else:
                await self._send_error(websocket, f"Unknown message type: {message_type}")
        
        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error(websocket, "Internal server error")
    
    async def _send_error(
        self, 
        websocket: websockets.WebSocketServerProtocol, 
        error_message: str
    ) -> None:
        """
        Send an error message to a WebSocket client.
        
        Args:
            websocket: The WebSocket connection
            error_message: The error message
        """
        await self._send_to_websocket(websocket, {
            "type": "error",
            "message": error_message
        })
    
    def get_connection_count(self) -> int:
        """
        Get the number of active connections.
        
        Returns:
            Number of active connections
        """
        return len(self.connections)
    
    def get_subscription_info(self) -> Dict[str, int]:
        """
        Get information about current subscriptions.
        
        Returns:
            Dictionary mapping session_id to subscriber count
        """
        return {
            session_id: len(subscribers)
            for session_id, subscribers in self.subscriptions.items()
        }