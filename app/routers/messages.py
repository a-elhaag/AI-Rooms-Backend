"""
Messages router for message retrieval and creation.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_database
from app.schemas.message import MessageCreate, MessageOut
from app.services.message_service import MessageService
from app.services.room_service import RoomService

router = APIRouter(prefix="/rooms/{room_id}/messages", tags=["Messages"])


@router.get("", response_model=list[MessageOut])
async def get_room_messages(
    room_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    before: Optional[str] = Query(default=None),
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> list[MessageOut]:
    """
    Get messages from a room with pagination.
    
    Args:
        room_id: Room ID
        limit: Maximum number of messages to return
        before: Message ID for cursor-based pagination
        db: Database instance
        
    Returns:
        list[MessageOut]: List of messages
        
    TODO:
        - Get user_id from current_user dependency
        - Initialize RoomService and verify user is member
        - Initialize MessageService
        - Call get_room_messages method
        - Return list of messages
    """
    pass


@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def create_message(
    room_id: str,
    message_data: MessageCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> MessageOut:
    """
    Create a new message in a room.
    
    This endpoint will later trigger the AI pipeline.
    
    Args:
        room_id: Room ID
        message_data: Message content and type
        db: Database instance
        
    Returns:
        MessageOut: Created message information
        
    TODO:
        - Get user_id from current_user dependency
        - Initialize RoomService and verify user is member
        - Initialize MessageService
        - Call create_message method
        - TODO: Trigger AI orchestrator pipeline
        - TODO: Broadcast message via WebSocket
        - Return message information
    """
    pass
