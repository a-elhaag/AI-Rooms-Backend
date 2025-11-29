"""
Room knowledge base service for managing room KB.
"""
import uuid
from datetime import datetime
from typing import Optional, Union

from app.schemas.kb import KBLink, KBOut, KBResource, KBUpdate, ResourceItem
from motor.motor_asyncio import AsyncIOMotorDatabase


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

        # Convert resources to ResourceItem objects
        resources = []
        for r in doc.get("resources", []):
            if isinstance(r, dict):
                resources.append(r)

        # Convert links - handle both string and dict formats
        links = []
        for link in doc.get("important_links", []):
            if isinstance(link, dict):
                links.append(link)
            else:
                # Legacy string format - convert to object
                links.append({"title": link, "url": link})

        return KBOut(
            id=doc["id"],
            room_id=doc["room_id"],
            summary=doc.get("summary", ""),
            key_decisions=doc.get("key_decisions", []),
            important_links=links,
            resources=resources,
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
            "resources": [],
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
            resources=[],
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

        if kb_data.key_decisions is not None:
            update_fields["key_decisions"] = kb_data.key_decisions

        if kb_data.important_links is not None:
            # Handle both string and dict formats
            links = []
            for link in kb_data.important_links:
                if isinstance(link, str):
                    links.append({"title": link, "url": link})
                elif hasattr(link, 'model_dump'):
                    links.append(link.model_dump())
                else:
                    links.append(link)
            update_fields["important_links"] = links

        if kb_data.resources is not None:
            resources = []
            for r in kb_data.resources:
                if hasattr(r, 'model_dump'):
                    resources.append(r.model_dump())
                else:
                    resources.append(r)
            update_fields["resources"] = resources

        result = await self.collection.find_one_and_update(
            {"room_id": room_id},
            {"$set": update_fields},
            return_document=True
        )

        if not result:
            return None

        # Convert resources
        resources = []
        for r in result.get("resources", []):
            if isinstance(r, dict):
                resources.append(r)

        # Convert links
        links = []
        for link in result.get("important_links", []):
            if isinstance(link, dict):
                links.append(link)
            else:
                links.append({"title": link, "url": link})

        return KBOut(
            id=result["id"],
            room_id=result["room_id"],
            summary=result.get("summary", ""),
            key_decisions=result.get("key_decisions", []),
            important_links=links,
            resources=resources,
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

        resources = []
        for r in result.get("resources", []):
            if isinstance(r, dict):
                resources.append(r)

        links = []
        for link in result.get("important_links", []):
            if isinstance(link, dict):
                links.append(link)
            else:
                links.append({"title": link, "url": link})

        return KBOut(
            id=result["id"],
            room_id=result["room_id"],
            summary=result.get("summary", ""),
            key_decisions=result.get("key_decisions", []),
            important_links=links,
            resources=resources,
            last_updated=result["updated_at"].isoformat() if isinstance(result["updated_at"], datetime) else result["updated_at"]
        )

    async def append_important_link(self, room_id: str, link: Union[str, KBLink]) -> Optional[KBOut]:
        """
        Append an important link to the KB.
        
        Args:
            room_id: Room ID
            link: Link object or URL string to append
            
        Returns:
            Optional[KBOut]: Updated KB or None
        """
        await self.create_default_kb(room_id)

        # Convert to dict format
        if isinstance(link, str):
            link_data = {"title": link, "url": link}
        elif hasattr(link, 'model_dump'):
            link_data = link.model_dump()
        else:
            link_data = link

        result = await self.collection.find_one_and_update(
            {"room_id": room_id},
            {
                "$push": {"important_links": link_data},
                "$set": {"updated_at": datetime.utcnow()}
            },
            return_document=True
        )

        if not result:
            return None

        resources = []
        for r in result.get("resources", []):
            if isinstance(r, dict):
                resources.append(r)

        links = []
        for l in result.get("important_links", []):
            if isinstance(l, dict):
                links.append(l)
            else:
                links.append({"title": l, "url": l})

        return KBOut(
            id=result["id"],
            room_id=result["room_id"],
            summary=result.get("summary", ""),
            key_decisions=result.get("key_decisions", []),
            important_links=links,
            resources=resources,
            last_updated=result["updated_at"].isoformat() if isinstance(result["updated_at"], datetime) else result["updated_at"]
        )

    async def append_resource(self, room_id: str, resource: Union[ResourceItem, KBResource]) -> Optional[KBOut]:
        """
        Append a resource to the KB.
        
        Args:
            room_id: Room ID
            resource: Resource item to append
            
        Returns:
            Optional[KBOut]: Updated KB or None
        """
        await self.create_default_kb(room_id)

        # Convert to dict
        if hasattr(resource, 'model_dump'):
            resource_data = resource.model_dump()
        else:
            resource_data = resource

        result = await self.collection.find_one_and_update(
            {"room_id": room_id},
            {
                "$push": {"resources": resource_data},
                "$set": {"updated_at": datetime.utcnow()}
            },
            return_document=True
        )

        if not result:
            return None

        resources = []
        for r in result.get("resources", []):
            if isinstance(r, dict):
                resources.append(r)

        links = []
        for link in result.get("important_links", []):
            if isinstance(link, dict):
                links.append(link)
            else:
                links.append({"title": link, "url": link})

        return KBOut(
            id=result["id"],
            room_id=result["room_id"],
            summary=result.get("summary", ""),
            key_decisions=result.get("key_decisions", []),
            important_links=links,
            resources=resources,
            last_updated=result["updated_at"].isoformat() if isinstance(result["updated_at"], datetime) else result["updated_at"]
        )

    async def remove_decision(self, room_id: str, decision: str) -> Optional[KBOut]:
        await self.create_default_kb(room_id)
        await self.collection.update_one(
            {"room_id": room_id},
            {"$pull": {"key_decisions": decision}, "$set": {"updated_at": datetime.utcnow()}},
        )
        return await self.get_room_kb(room_id)

    async def remove_link_by_url(self, room_id: str, url: str) -> Optional[KBOut]:
        await self.create_default_kb(room_id)
        await self.collection.update_one(
            {"room_id": room_id},
            {"$pull": {"important_links": {"url": url}}, "$set": {"updated_at": datetime.utcnow()}},
        )
        return await self.get_room_kb(room_id)

    async def remove_resource_by_url(self, room_id: str, url: str) -> Optional[KBOut]:
        await self.create_default_kb(room_id)
        await self.collection.update_one(
            {"room_id": room_id},
            {"$pull": {"resources": {"url": url}}, "$set": {"updated_at": datetime.utcnow()}},
        )
        return await self.get_room_kb(room_id)
