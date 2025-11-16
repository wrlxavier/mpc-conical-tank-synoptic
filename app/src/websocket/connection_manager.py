"""
WebSocket connection manager for handling multiple clients.

This module manages active WebSocket connections and provides
methods for broadcasting messages to connected clients.
"""

from typing import List
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manager for WebSocket connections.
    
    Handles connecting, disconnecting, and broadcasting to multiple clients.
    """
    
    def __init__(self):
        """Initialize connection manager with empty connection list."""
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket instance to connect.
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from active list.
        
        Args:
            websocket: WebSocket instance to disconnect.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """
        Send message to all connected clients.
        
        Args:
            message: Dictionary to send as JSON to all clients.
        """
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {str(e)}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_connection_count(self) -> int:
        """
        Get number of active connections.
        
        Returns:
            Count of active WebSocket connections.
        """
        return len(self.active_connections)
