"""
Room service for room and room member management.
"""
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.room import RoomCreate, RoomJoin, RoomMemberOut, RoomOut


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
            
        TODO:
            - Generate unique join code (6-10 characters)
            - Create room document in rooms collection
            - Add creator as owner in room_members collection
            - Return room information
        """
        pass
    
    async def get_user_rooms(self, user_id: str) -> list[RoomOut]:
        """
        Get all rooms that a user is a member of.
        
        Args:
            user_id: User ID
            
        Returns:
            list[RoomOut]: List of rooms
            
        TODO:
            - Query room_members collection for user_id
            - Join with rooms collection
            - Return list of rooms
        """
        pass
    
    async def join_room(self, join_data: RoomJoin, user_id: str) -> RoomOut:
        """
        Join a room using a join code.
        
        Args:
            join_data: Join code data
            user_id: User ID joining the room
            
        Returns:
            RoomOut: Room information
            
        TODO:
            - Find room by join_code
            - Check if user is already a member
            - Add user to room_members collection with role "member"
            - Return room information
        """
        pass
    
    async def get_room_members(self, room_id: str) -> list[RoomMemberOut]:
        """
        Get all members of a room.
        
        Args:
            room_id: Room ID
            
        Returns:
            list[RoomMemberOut]: List of room members with user information
            
        TODO:
            - Query room_members collection for room_id
            - Join with users collection to get username
            - Return list of members
        """
        pass
    
    async def is_user_member(self, room_id: str, user_id: str) -> bool:
        """
        Check if a user is a member of a room.
        
        Args:
            room_id: Room ID
            user_id: User ID
            
        Returns:
            bool: True if user is a member
            
        TODO:
            - Query room_members collection
            - Return True if record exists
        """
        pass
