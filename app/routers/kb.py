"""
Room knowledge base router.
"""
from app.db import get_database
from app.schemas.kb import KBOut, KBUpdate
from app.services.kb_service import KBService
from app.services.room_service import RoomService
from app.utils.security import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(
    tags=["Knowledge Base"],
    responses={404: {"description": "Not found"}},
)


@router.get("/rooms/{room_id}/kb", response_model=KBOut)
async def get_room_kb(
    room_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get knowledge base for a room.
    """
    # Verify user is a member of the room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    service = KBService(db)
    kb = await service.get_room_kb(room_id)

    if not kb:
        # Create default if not exists
        kb = await service.create_default_kb(room_id)

    return kb


@router.put("/rooms/{room_id}/kb", response_model=KBOut)
async def update_room_kb(
    room_id: str,
    kb_data: KBUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Update room knowledge base.
    """
    # Verify user is a member of the room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    service = KBService(db)
    kb = await service.update_kb(room_id, kb_data)

    if not kb:
        # Create default if not exists, then update
        await service.create_default_kb(room_id)
        kb = await service.update_kb(room_id, kb_data)

    return kb
