"""
Room service for room and room member management.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from app.schemas.room import RoomCreate, RoomJoin, RoomMemberOut, RoomOut
from motor.motor_asyncio import AsyncIOMotorDatabase


class RoomService:
    """Service for room operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize room service.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
    
    async def create_room(self, room_data: RoomCreate, owner_id: str) -> RoomOut:
        """
        Create a new room with a unique join code.
        
        Args:
            room_data: Room creation data
            owner_id: ID of the user creating the room
            
        Returns:
            RoomOut: Created room information
        """
        # Generate unique join code
        join_code = str(uuid.uuid4())[:8].upper()
        
        room_doc = {
            "id": str(uuid.uuid4()),
            "name": room_data.name,
            "join_code": join_code,
            "owner_id": owner_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "member_count": 1,
            "message_count": 0,
            "has_ai": True  # Default to true for now
        }
        
        # Create room document
        await self.db.rooms.insert_one(room_doc)
        
        # Add creator as owner in room_members collection
        member_doc = {
            "room_id": room_doc["id"],
            "user_id": owner_id,
            "role": "owner",
            "joined_at": datetime.utcnow()
        }
        await self.db.room_members.insert_one(member_doc)
        
        return RoomOut(**room_doc)
    
    async def get_user_rooms(self, user_id: str) -> List[RoomOut]:
        """
        Get all rooms that a user is a member of.
        
        Args:
            user_id: User ID
            
        Returns:
            List[RoomOut]: List of rooms
        """
        # Get room IDs where user is a member
        cursor = self.db.room_members.find({"user_id": user_id})
        room_ids = [doc["room_id"] async for doc in cursor]
        
        if not room_ids:
            return []
            
        # Fetch rooms
        rooms_cursor = self.db.rooms.find({"id": {"$in": room_ids}}).sort("updated_at", -1)
        rooms = []
        async for doc in rooms_cursor:
            rooms.append(RoomOut(**doc))
            
        return rooms
