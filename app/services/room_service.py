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
            "has_ai": True,  # Default to true for now
            "custom_ai_instructions": room_data.custom_ai_instructions or None,
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
    
    async def join_room(self, join_code: str, user_id: str) -> Optional[RoomOut]:
        """
        Join a room using a join code.
        
        Args:
            join_code: Room join code
            user_id: User ID
            
        Returns:
            Optional[RoomOut]: Room information if found and joined
        """
        # Find room by join code
        room = await self.db.rooms.find_one({"join_code": join_code})
        if not room:
            return None
        
        # Check if already a member
        existing = await self.db.room_members.find_one({
            "room_id": room["id"],
            "user_id": user_id
        })
        if existing:
            # Already a member, just return room
            return RoomOut(**room)
        
        # Add as member
        member_doc = {
            "room_id": room["id"],
            "user_id": user_id,
            "role": "member",
            "joined_at": datetime.utcnow()
        }
        await self.db.room_members.insert_one(member_doc)
        
        # Increment member count
        await self.db.rooms.update_one(
            {"id": room["id"]},
            {"$inc": {"member_count": 1}}
        )
        
        # Fetch updated room
        updated_room = await self.db.rooms.find_one({"id": room["id"]})
        return RoomOut(**updated_room) if updated_room else RoomOut(**room)

    async def get_room(self, room_id: str) -> Optional[RoomOut]:
        doc = await self.db.rooms.find_one({"id": room_id})
        return RoomOut(**doc) if doc else None

    async def update_room_settings(
        self,
        room_id: str,
        requester_id: str,
        custom_ai_instructions: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[RoomOut]:
        """
        Update room settings (owner only). Supports updating `custom_ai_instructions` and `name`.

        Args:
            room_id: Room ID
            requester_id: ID of the user requesting the change
            custom_ai_instructions: Optional AI instructions to set (can be None to clear)
            name: Optional new room name (if provided, will update name)

        Returns:
            Optional[RoomOut]: Updated room or None if not allowed/found
        """
        room = await self.db.rooms.find_one({"id": room_id})
        if not room or room.get("owner_id") != requester_id:
            return None

        # Build the $set payload dynamically so we only change provided fields
        set_payload = {"updated_at": datetime.utcnow()}

        if custom_ai_instructions is not None:
            set_payload["custom_ai_instructions"] = custom_ai_instructions

        if name is not None:
            # Trim and ensure non-empty names are applied; empty string will be ignored
            new_name = name.strip()
            if new_name:
                set_payload["name"] = new_name

        if len(set_payload) > 0:
            await self.db.rooms.update_one({"id": room_id}, {"$set": set_payload})

        updated = await self.db.rooms.find_one({"id": room_id})
        return RoomOut(**updated) if updated else None

    async def delete_room(self, room_id: str, requester_id: str) -> bool:
        """Delete a room and related data if requester is owner."""
        room = await self.db.rooms.find_one({"id": room_id})
        if not room or room.get("owner_id") != requester_id:
            return False

        await self.db.rooms.delete_one({"id": room_id})
        await self.db.room_members.delete_many({"room_id": room_id})
        await self.db.messages.delete_many({"room_id": room_id})
        await self.db.tasks.delete_many({"room_id": room_id})
        await self.db.room_goals.delete_many({"room_id": room_id})
        await self.db.room_kb.delete_many({"room_id": room_id})
        await self.db.documents.delete_many({"room_id": room_id})
        await self.db.document_chunks.delete_many({"room_id": room_id})
        return True
    
    async def get_room_members(self, room_id: str) -> List[RoomMemberOut]:
        """
        Get all members of a room.
        
        Args:
            room_id: Room ID
            
        Returns:
            List[RoomMemberOut]: List of room members with user details
        """
        from bson import ObjectId

        # Get all members for the room
        members_cursor = self.db.room_members.find({"room_id": room_id})
        members = []
        
        async for member_doc in members_cursor:
            # Fetch user details
            try:
                user = await self.db.users.find_one({"_id": ObjectId(member_doc["user_id"])})
                username = user.get("username", "Unknown") if user else "Unknown"
            except:
                username = "Unknown"
            
            members.append(RoomMemberOut(
                id=str(member_doc.get("_id")),
                room_id=member_doc["room_id"],
                user_id=member_doc["user_id"],
                username=username,
                role=member_doc["role"],
                joined_at=member_doc["joined_at"].isoformat() if isinstance(member_doc["joined_at"], datetime) else member_doc["joined_at"]
            ))
        
        return members
    
    async def is_member(self, room_id: str, user_id: str) -> bool:
        """
        Check if a user is a member of a room.
        
        Args:
            room_id: Room ID
            user_id: User ID
            
        Returns:
            bool: True if user is a member
        """
        member = await self.db.room_members.find_one({
            "room_id": room_id,
            "user_id": user_id
        })
        return member is not None
