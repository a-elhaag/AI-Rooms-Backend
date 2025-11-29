"""
Rooms router for room creation, joining, and member management.
"""
from app.db import get_database
from app.schemas.room import RoomCreate, RoomJoin, RoomMemberOut, RoomOut
from app.services.room_service import RoomService
from app.utils.security import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("", response_model=list[RoomOut])
async def get_user_rooms(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> list[RoomOut]:
    """
    Get all rooms that the current user is a member of.
    
    Args:
        db: Database instance
        current_user_id: Current user ID from header
        
    Returns:
        list[RoomOut]: List of rooms
    """
    
    room_service = RoomService(db)
    return await room_service.get_user_rooms(current_user_id)


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> RoomOut:
    """
    Create a new room with auto-generated join code.
    
    Args:
        room_data: Room creation data (name)
        db: Database instance
        current_user_id: Current user ID from header
        
    Returns:
        RoomOut: Created room information
    """
    
    room_service = RoomService(db)
    return await room_service.create_room(room_data, current_user_id)


@router.get("/{room_id}", response_model=RoomOut)
async def get_room(
    room_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id),
) -> RoomOut:
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room",
        )
    room = await room_service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


@router.post("/join", response_model=RoomOut)
async def join_room(
    join_data: RoomJoin,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> RoomOut:
    """
    Join a room using a join code.
    
    Args:
        join_data: Join code
        db: Database instance
        current_user_id: Current user ID from header
        
    Returns:
        RoomOut: Joined room information
    """
    
    room_service = RoomService(db)
    room = await room_service.join_room(join_data.join_code, current_user_id)
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found with that join code"
        )
    
    return room


@router.get("/{room_id}/members", response_model=list[RoomMemberOut])
async def get_room_members(
    room_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> list[RoomMemberOut]:
    """
    Get all members of a room.
    
    Args:
        room_id: Room ID
        db: Database instance
        current_user_id: Current user ID from header
        
    Returns:
        list[RoomMemberOut]: List of room members
    """
    
    room_service = RoomService(db)
    
    # Verify user is a member
    if not await room_service.is_member(room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    return await room_service.get_room_members(room_id)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> None:
    """
    Delete a room (owner only).
    """
    room_service = RoomService(db)
    success = await room_service.delete_room(room_id, current_user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the room owner can delete the room or room not found"
        )

    from app.routers.ws import manager
    await manager.broadcast_to_room(room_id, {
        "type": "room_deleted",
        "room_id": room_id,
    })

    return None


@router.patch("/{room_id}/settings", response_model=RoomOut)
async def update_room_settings(
    room_id: str,
    settings: dict,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> RoomOut:
    """
    Update room settings (owner only). Supports custom_ai_instructions.
    """
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room",
        )

    updated = await room_service.update_room_settings(
        room_id,
        current_user_id,
        custom_ai_instructions=settings.get("custom_ai_instructions"),
        name=settings.get("name"),
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the room owner can update settings or room not found",
        )

    # Broadcast room update to connected WebSocket clients in the room
    from app.routers.ws import manager
    try:
        await manager.broadcast_to_room(room_id, {
            "type": "room_updated",
            "room": updated.dict()
        })
    except Exception:
        # Don't fail the request if broadcasting fails
        pass

    return updated
