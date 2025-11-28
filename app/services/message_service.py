"""
Message service for message management and retrieval.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from app.schemas.message import MessageCreate, MessageOut
from motor.motor_asyncio import AsyncIOMotorDatabase


class MessageService:
    """Service for message operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize message service.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
    
    async def create_message(
        self,
        room_id: str,
        message_data: MessageCreate,
        user_id: Optional[str] = None
    ) -> MessageOut:
        """
        Create a new message in a room.
        
        Args:
            room_id: Room ID
            message_data: Message content and type
            user_id: User ID (None for AI messages)
            
        Returns:
            MessageOut: Created message information
        """
        message_doc = {
            "id": str(uuid.uuid4()),
            "room_id": room_id,
            "user_id": user_id or "ai",
            "username": "AI" if not user_id else "User",
            "content": message_data.content,
            "type": message_data.type,
            "created_at": datetime.utcnow()
        }
        
        await self.db.messages.insert_one(message_doc)
        return MessageOut(**message_doc)
    
    async def get_room_messages(
        self,
        room_id: str,
        limit: int = 50,
        before: Optional[str] = None
    ) -> List[MessageOut]:
        """
        Get messages from a room with pagination.
        
        Args:
            room_id: Room ID
            limit: Maximum number of messages to return
            before: Message ID for cursor-based pagination
            
        Returns:
            List[MessageOut]: List of messages with user information
        """
        query = {"room_id": room_id}
        
        if before:
            # Find the "before" message to get its timestamp
            before_msg = await self.db.messages.find_one({"id": before})
            if before_msg:
                query["created_at"] = {"$lt": before_msg["created_at"]}
        
        cursor = self.db.messages.find(query).sort("created_at", -1).limit(limit)
        messages = []
        async for doc in cursor:
            messages.append(MessageOut(**doc))
            
        return messages
    
    async def get_recent_messages_for_context(
        self,
        room_id: str,
        limit: int = 20
    ) -> list[dict]:
        """
        Get recent messages for AI context.
        
        Args:
            room_id: Room ID
            limit: Number of recent messages
            
        Returns:
            list[dict]: List of message dictionaries
        """
        cursor = self.db.messages.find({"room_id": room_id}).sort("created_at", -1).limit(limit)
        messages = []
        async for doc in cursor:
            # Convert ObjectId to string if present (though this service uses UUID strings for id)
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])

            # Format dates
            if "created_at" in doc and isinstance(doc["created_at"], datetime):
                doc["created_at"] = doc["created_at"].isoformat()

            messages.append(doc)

        # Return in chronological order (oldest first) for context window
        return list(reversed(messages))
