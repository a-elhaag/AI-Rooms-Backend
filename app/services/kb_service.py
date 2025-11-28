"""
Room knowledge base service for managing room KB.
"""
import uuid
from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.kb import KBOut, KBUpdate


class KBService:
    """Service for room knowledge base operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize KB service.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.room_kb
    
    async def get_room_kb(self, room_id: str) -> Optional[KBOut]:
        """
        Get knowledge base for a room.
        
        Args:
            room_id: Room ID
            
        Returns:
            Optional[KBOut]: Room KB or None
        """
        doc = await self.collection.find_one({"room_id": room_id})

        if not doc:
            return None

        return KBOut(
            id=doc["id"],
            room_id=doc["room_id"],
            summary=doc.get("summary", ""),
            key_decisions=doc.get("key_decisions", []),
            important_links=doc.get("important_links", []),
            last_updated=doc["updated_at"].isoformat() if isinstance(doc["updated_at"], datetime) else doc["updated_at"]
        )
    
    async def create_default_kb(self, room_id: str) -> KBOut:
        """
        Create a default knowledge base for a new room.
        
        Args:
            room_id: Room ID
            
        Returns:
            KBOut: Created KB
        """
        existing = await self.get_room_kb(room_id)
        if existing:
            return existing

        now = datetime.utcnow()
        kb_id = str(uuid.uuid4())

        kb_doc = {
            "id": kb_id,
            "room_id": room_id,
            "summary": "",
            "key_decisions": [],
            "important_links": [],
            "created_at": now,
            "updated_at": now
        }

        await self.collection.insert_one(kb_doc)

        return KBOut(
            id=kb_id,
            room_id=room_id,
            summary="",
            key_decisions=[],
            important_links=[],
            last_updated=now.isoformat()
        )
    
    async def update_kb(self, room_id: str, kb_data: KBUpdate) -> Optional[KBOut]:
        """
        Update room knowledge base.
        
        Args:
            room_id: Room ID
            kb_data: KB update data
            
        Returns:
            Optional[KBOut]: Updated KB or None
        """
        # Ensure KB exists
        await self.create_default_kb(room_id)

        update_fields = {"updated_at": datetime.utcnow()}

        if kb_data.summary is not None:
            update_fields["summary"] = kb_data.summary

        # Note: This replaces the lists. To append, we'd need a different schema or method.
        # Based on schema, it seems we replace the list.
        if kb_data.key_decisions is not None:
            update_fields["key_decisions"] = kb_data.key_decisions

        if kb_data.important_links is not None:
            update_fields["important_links"] = kb_data.important_links

        result = await self.collection.find_one_and_update(
            {"room_id": room_id},
            {"$set": update_fields},
            return_document=True
        )

        if not result:
            return None

        return KBOut(
            id=result["id"],
            room_id=result["room_id"],
            summary=result.get("summary", ""),
            key_decisions=result.get("key_decisions", []),
            important_links=result.get("important_links", []),
            last_updated=result["updated_at"].isoformat() if isinstance(result["updated_at"], datetime) else result["updated_at"]
        )
    
    async def append_key_decision(self, room_id: str, decision: str) -> Optional[KBOut]:
        """
        Append a key decision to the KB.
        
        Args:
            room_id: Room ID
            decision: Decision text to append
            
        Returns:
            Optional[KBOut]: Updated KB or None
        """
        # Ensure KB exists
        await self.create_default_kb(room_id)

        result = await self.collection.find_one_and_update(
            {"room_id": room_id},
            {
                "$push": {"key_decisions": decision},
                "$set": {"updated_at": datetime.utcnow()}
            },
            return_document=True
        )

        if not result:
            return None

        return KBOut(
            id=result["id"],
            room_id=result["room_id"],
            summary=result.get("summary", ""),
            key_decisions=result.get("key_decisions", []),
            important_links=result.get("important_links", []),
            last_updated=result["updated_at"].isoformat() if isinstance(result["updated_at"], datetime) else result["updated_at"]
        )
