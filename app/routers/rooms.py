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
    
    room_service = RoomService(db)
    return await room_service.get_user_rooms(current_user_id)


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> RoomOut:
    
    room_service = RoomService(db)
    return await room_service.create_room(room_data, current_user_id)


@router.post("/join", response_model=RoomOut)
async def join_room(
    join_data: RoomJoin,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user_id: str = Depends(get_current_user_id)
) -> RoomOut:
    
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
    
    room_service = RoomService(db)
    
    # Verify user is a member
    if not await room_service.is_member(room_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    return await room_service.get_room_members(room_id)
