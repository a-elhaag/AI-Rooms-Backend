"""
WebSocket router for real-time communication.
"""
import json
from typing import Dict, List, Optional
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status

from app.db import get_database
from app.services.auth_service import AuthService
from app.services.message_service import MessageService
from app.schemas.message import MessageCreate

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasting.
    """
    
    def __init__(self):
        """Initialize connection manager with empty connections dict."""
        # Dictionary mapping room_id to list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Mapping websocket to user_id for cleanup
        self.ws_to_user: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str, user_id: str) -> None:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            room_id: Room to join
            user_id: User ID connecting
        """
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        self.ws_to_user[websocket] = user_id
    
    async def disconnect(self, websocket: WebSocket, room_id: str) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
            room_id: Room to leave
        """
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]

        if websocket in self.ws_to_user:
            del self.ws_to_user[websocket]
    
    async def broadcast_to_room(self, room_id: str, message: dict) -> None:
        """
        Broadcast a message to all connections in a room.
        
        Args:
            room_id: Room ID
            message: Message data to broadcast
        """
        if room_id in self.active_connections:
            # Create a copy to avoid modification during iteration issues
            connections = list(self.active_connections[room_id])
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    # If sending fails, assume disconnected and cleanup
                    await self.disconnect(connection, room_id)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: Optional[str] = Query(None),
    # In a real app we'd inject services, but here we construct them or get from app state
    # For now we'll get DB directly
) -> None:
    """
    WebSocket endpoint for real-time chat.
    
    Args:
        websocket: WebSocket connection
        room_id: Room ID to join
        token: Authentication token (using user_id as token for POC)
    """
    # Simple validation - in POC token is just user_id
    user_id = token
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify user exists
    db = await get_database()
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, room_id, user_id)
    
    # Broadcast join message
    await manager.broadcast_to_room(room_id, {
        "type": "system",
        "content": f"{user.username} joined the chat",
        "room_id": room_id
    })
    
    try:
        while True:
            data = await websocket.receive_json()

            # Process message
            message_type = data.get("type")

            if message_type == "message":
                content = data.get("content")
                if content:
                    # Save to DB
                    message_service = MessageService(db)
                    message_data = MessageCreate(content=content)

                    saved_message = await message_service.create_message(
                        room_id=room_id,
                        message_data=message_data,
                        user_id=user_id
                    )

                    # Broadcast to room
                    await manager.broadcast_to_room(room_id, {
                        "type": "message",
                        "message": saved_message.dict(),
                        "user": user.dict()
                    })
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
        await manager.broadcast_to_room(room_id, {
            "type": "system",
            "content": f"{user.username} left the chat",
            "room_id": room_id
        })
    except Exception as e:
        # Log error in real app
        print(f"WebSocket error: {e}")
        await manager.disconnect(websocket, room_id)
