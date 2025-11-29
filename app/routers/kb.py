"""
Room knowledge base router.
"""
from typing import Optional

from app.db import get_database
from app.schemas.kb import (KBAppend, KBLink, KBOut, KBResource, KBUpdate,
                            ResourceItem)
from app.services.kb_service import KBService
from app.services.room_service import RoomService
from app.utils.security import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

router = APIRouter(
    tags=["Knowledge Base"],
    responses={404: {"description": "Not found"}},
)


class DecisionInput(BaseModel):
    decision: str


class KBRemoveInput(BaseModel):
    item_type: str  # "decision" | "link" | "resource"
    value: str      # decision text or URL to remove


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

    # Broadcast KB update via WebSocket
    from app.routers.ws import manager
    await manager.broadcast_to_room(room_id, {
        "type": "kb_updated",
        "kb": {
            "id": kb.id,
            "room_id": kb.room_id,
            "summary": kb.summary,
            "key_decisions": kb.key_decisions,
            "important_links": kb.important_links,
            "resources": kb.resources,
            "last_updated": kb.last_updated
        }
    })

    return kb


@router.post("/rooms/{room_id}/kb/append", response_model=KBOut)
async def append_to_kb(
    room_id: str,
    append_data: KBAppend,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Append a single item to the knowledge base (decision, link, or resource).
    """
    # Verify user is a member of the room
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    service = KBService(db)
    kb = None
    
    if append_data.key_decision:
        kb = await service.append_key_decision(room_id, append_data.key_decision)
    elif append_data.important_link:
        kb = await service.append_important_link(room_id, append_data.important_link)
    elif append_data.resource:
        kb = await service.append_resource(room_id, append_data.resource)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No item to append provided"
        )
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to append to KB"
        )
    
    return kb


@router.post("/rooms/{room_id}/kb/decisions", response_model=KBOut)
async def add_kb_decision(
    room_id: str,
    data: DecisionInput,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Add a key decision to the knowledge base.
    """
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    service = KBService(db)
    kb = await service.append_key_decision(room_id, data.decision)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add decision"
        )
    
    return kb


@router.post("/rooms/{room_id}/kb/links", response_model=KBOut)
async def add_kb_link(
    room_id: str,
    link: KBLink,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Add an important link to the knowledge base.
    """
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    service = KBService(db)
    kb = await service.append_important_link(room_id, link)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add link"
        )
    
    return kb


@router.post("/rooms/{room_id}/kb/resources", response_model=KBOut)
async def add_kb_resource(
    room_id: str,
    resource: KBResource,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Add a resource to the knowledge base.
    """
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    service = KBService(db)
    kb = await service.append_resource(room_id, resource)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add resource"
        )
    
    return kb


@router.post("/rooms/{room_id}/kb/remove", response_model=KBOut)
async def remove_kb_item(
    room_id: str,
    data: KBRemoveInput,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user_id: str = Depends(get_current_user_id)
):
    """
    Remove an item from the KB (decision, link, or resource) by value/url.
    """
    room_service = RoomService(db)
    if not await room_service.is_member(room_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )

    service = KBService(db)
    kb = None
    if data.item_type == "decision":
        kb = await service.remove_decision(room_id, data.value)
    elif data.item_type == "link":
        kb = await service.remove_link_by_url(room_id, data.value)
    elif data.item_type == "resource":
        kb = await service.remove_resource_by_url(room_id, data.value)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item_type. Use decision, link, or resource."
        )

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove KB item"
        )

    from app.routers.ws import manager
    await manager.broadcast_to_room(room_id, {
        "type": "kb_updated",
        "kb": kb.model_dump()
    })

    return kb
