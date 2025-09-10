"""
WebSocket routes for real-time progress tracking.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from ..websocket.progress_manager import ProgressManager
from ..websocket.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

# Create global instances
progress_manager = ProgressManager()
websocket_manager = WebSocketManager(progress_manager)

router = APIRouter()


@router.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time progress tracking.
    
    Clients can connect to this endpoint to receive real-time updates
    about ongoing operations like agent creation.
    
    Message types supported:
    - subscribe: Subscribe to a specific session
    - unsubscribe: Unsubscribe from a specific session  
    - get_status: Get current status of a session
    - get_active_sessions: Get all active sessions
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    try:
        await websocket_manager.handle_connection(websocket, "/ws/progress")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket server status.
    
    Returns information about active connections and subscriptions.
    """
    return {
        "status": "running",
        "active_connections": websocket_manager.get_connection_count(),
        "subscriptions": websocket_manager.get_subscription_info(),
        "active_sessions": len(progress_manager.get_active_sessions())
    }


@router.get("/ws/test-page")
async def websocket_test_page():
    """
    Serve a simple test page for WebSocket functionality.
    
    This is useful for testing WebSocket connections during development.
    """
    html = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>WebSocket Progress Test</title>
        </head>
        <body>
            <h1>WebSocket Progress Tracker Test</h1>
            <div id="status">Disconnected</div>
            <div>
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <button onclick="subscribe()">Subscribe to Test Session</button>
                <button onclick="getActiveSessionsData()">Get Active Sessions</button>
            </div>
            <div>
                <h3>Session ID:</h3>
                <input type="text" id="sessionId" value="test-session" />
            </div>
            <div>
                <h3>Messages:</h3>
                <div id="messages" style="height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px;">
                </div>
            </div>

            <script>
                let ws;
                
                function connect() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/ws/progress`;
                    
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = function(event) {
                        document.getElementById('status').innerText = 'Connected';
                        addMessage('Connected to WebSocket');
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        addMessage(`Received: ${JSON.stringify(data, null, 2)}`);
                    };
                    
                    ws.onclose = function(event) {
                        document.getElementById('status').innerText = 'Disconnected';
                        addMessage('WebSocket connection closed');
                    };
                    
                    ws.onerror = function(error) {
                        addMessage(`Error: ${error}`);
                    };
                }
                
                function disconnect() {
                    if (ws) {
                        ws.close();
                    }
                }
                
                function subscribe() {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        const sessionId = document.getElementById('sessionId').value;
                        const message = {
                            type: 'subscribe',
                            session_id: sessionId
                        };
                        ws.send(JSON.stringify(message));
                        addMessage(`Subscribed to session: ${sessionId}`);
                    } else {
                        addMessage('WebSocket not connected');
                    }
                }
                
                function getActiveSessionsData() {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        const message = {
                            type: 'get_active_sessions'
                        };
                        ws.send(JSON.stringify(message));
                        addMessage('Requested active sessions');
                    } else {
                        addMessage('WebSocket not connected');
                    }
                }
                
                function addMessage(message) {
                    const messagesDiv = document.getElementById('messages');
                    const timestamp = new Date().toLocaleTimeString();
                    messagesDiv.innerHTML += `<div>[${timestamp}] ${message}</div>`;
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html)


# Export the managers for use in other modules
def get_progress_manager() -> ProgressManager:
    """Get the global progress manager instance."""
    return progress_manager


def get_websocket_manager() -> WebSocketManager:
    """Get the global websocket manager instance."""
    return websocket_manager