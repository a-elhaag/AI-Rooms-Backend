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
        from bson import ObjectId

        # Fetch username from database
        sender_name = "AI Assistant"
        sender_id = user_id or "ai"
        
        if user_id and user_id != "ai_assistant":
            try:
                user = await self.db.users.find_one({"_id": ObjectId(user_id)})
                if user:
                    sender_name = user.get("username", "Unknown User")
                else:
                    sender_name = "Unknown User"
            except:
                sender_name = "Unknown User"
        
        message_doc = {
            "id": str(uuid.uuid4()),
            "room_id": room_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "sender_type": message_data.sender_type,
            "content": message_data.content,
            "reply_to": message_data.reply_to,
            "reactions": {},
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
            # Ensure reply_to and reactions exist
            doc.setdefault("reply_to", None)
            doc.setdefault("reactions", {})
            messages.append(MessageOut(**doc))
            
        return messages
    
    async def get_message_by_id(self, message_id: str) -> Optional[MessageOut]:
        """
        Get a message by ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            Optional[MessageOut]: Message or None
        """
        doc = await self.db.messages.find_one({"id": message_id})
        if doc:
            doc.setdefault("reply_to", None)
            doc.setdefault("reactions", {})
            return MessageOut(**doc)
        return None
    
    async def add_reaction(
        self,
        message_id: str,
        user_id: str,
        emoji: str
    ) -> Optional[MessageOut]:
        """
        Add a reaction to a message.
        
        Args:
            message_id: Message ID
            user_id: User who reacted
            emoji: Reaction emoji
            
        Returns:
            Optional[MessageOut]: Updated message
        """
        # Increment reaction count
        result = await self.db.messages.find_one_and_update(
            {"id": message_id},
            {"$inc": {f"reactions.{emoji}": 1}},
            return_document=True
        )
        
        if result:
            result.setdefault("reply_to", None)
            result.setdefault("reactions", {})
            return MessageOut(**result)
        return None
    
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
