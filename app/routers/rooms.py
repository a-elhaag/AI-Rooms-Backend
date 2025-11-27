"""
Rooms router for room creation, joining, and member management.
"""
from app.db import get_database
from app.schemas.room import RoomCreate, RoomJoin, RoomMemberOut, RoomOut
from app.services.room_service import RoomService
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("", response_model=list[RoomOut])
async def get_user_rooms(
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> list[RoomOut]:
    """
    Get all rooms that the current user is a member of.
    
    Args:
        db: Database instance
        
    Returns:
        list[RoomOut]: List of rooms
    """
    # Temporary hardcoded user for POC
    current_user_id = "demo_user_123"
    
    room_service = RoomService(db)
    return await room_service.get_user_rooms(current_user_id)


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> RoomOut:
    """
    Create a new room with auto-generated join code.
    
    Args:
        room_data: Room creation data (name)
        db: Database instance
        
    Returns:
        RoomOut: Created room information
    """
    # Temporary hardcoded user for POC
    current_user_id = "demo_user_123"
    
    room_service = RoomService(db)
    return await room_service.create_room(room_data, current_user_id)


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> RoomOut:
    """
    Create a new room with auto-generated join code.
    
    Args:
        room_data: Room creation data (name)
        db: Database instance
        
    Returns:
        RoomOut: Created room information
        
    TODO:
        - Get user_id from current_user dependency
        - Initialize RoomService
        - Call create_room method
        - Return room information
    """
    pass


@router.post("/join", response_model=RoomOut)
async def join_room(
    join_data: RoomJoin,
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> RoomOut:
    """
    Join a room using a join code.
    
    Args:
        join_data: Join code
        db: Database instance
        
    Returns:
        RoomOut: Joined room information
        
    TODO:
        - Get user_id from current_user dependency
        - Initialize RoomService
        - Call join_room method
        - Handle invalid join code error
        - Handle already member error
        - Return room information
    """
    pass


@router.get("/{room_id}/members", response_model=list[RoomMemberOut])
async def get_room_members(
    room_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    # TODO: Add current_user dependency
) -> list[RoomMemberOut]:
    """
    Get all members of a room.
    
    Args:
        room_id: Room ID
        db: Database instance
        
    Returns:
        list[RoomMemberOut]: List of room members
        
    TODO:
        - Get user_id from current_user dependency
        - Initialize RoomService
        - Verify user is a member of the room
        - Call get_room_members method
        - Return list of members
    """
    pass
