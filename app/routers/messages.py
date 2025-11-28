"""
Messages router for message retrieval and creation.
"""
from typing import Optional

from app.db import get_database
from app.schemas.message import MessageCreate, MessageOut
from app.services.message_service import MessageService
from app.services.room_service import RoomService
from app.utils.security import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/rooms/{room_id}/messages", tags=["Messages"])


@router.get("", response_model=list[MessageOut])
async def get_room_messages(
    room_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    before: Optional[str] = Query(default=None),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> list[MessageOut]:
    """
    Get messages from a room with pagination.
    
    Args:
        room_id: Room ID
        limit: Maximum number of messages to return
        before: Message ID for cursor-based pagination
        db: Database instance
        current_user_id: Current user ID from header
        
    Returns:
        list[MessageOut]: List of messages
    """
    # Verify user is a member of the room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    message_service = MessageService(db)
    return await message_service.get_room_messages(room_id, limit, before)


@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def create_message(
    room_id: str,
    message_data: MessageCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> MessageOut:
    """
    Create a new message in a room.
    
    This endpoint will later trigger the AI pipeline.
    
    Args:
        room_id: Room ID
        message_data: Message content and type
        db: Database instance
        current_user_id: Current user ID from header
        
    Returns:
        MessageOut: Created message information
    """
    
    message_service = MessageService(db)
    return await message_service.create_message(room_id, message_data, current_user_id)
