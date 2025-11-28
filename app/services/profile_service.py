"""
User profile service for managing user style and preferences.
"""
import uuid
from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.schemas.profile import ProfileOut, ProfileUpdate


class ProfileService:
    """Service for user profile operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize profile service.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.user_profiles
    
    async def get_user_profile(self, user_id: str) -> Optional[ProfileOut]:
        """
        Get user profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[ProfileOut]: User profile or None
        """
        doc = await self.collection.find_one({"user_id": user_id})

        if not doc:
            return None

        return ProfileOut(
            id=doc["id"],
            user_id=doc["user_id"],
            preferred_language=doc.get("preferred_language", "en"),
            style_notes=doc.get("style_notes", ""),
            sample_messages=doc.get("sample_messages", []),
            last_updated=doc["updated_at"].isoformat() if isinstance(doc["updated_at"], datetime) else doc["updated_at"]
        )
    
    async def create_default_profile(self, user_id: str, language: str = "en") -> ProfileOut:
        """
        Create a default profile for a new user.
        
        Args:
            user_id: User ID
            language: Preferred language
            
        Returns:
            ProfileOut: Created profile
        """
        existing = await self.get_user_profile(user_id)
        if existing:
            return existing

        now = datetime.utcnow()
        profile_id = str(uuid.uuid4())

        profile_doc = {
            "id": profile_id,
            "user_id": user_id,
            "preferred_language": language,
            "style_notes": "",
            "sample_messages": [],
            "created_at": now,
            "updated_at": now
        }

        await self.collection.insert_one(profile_doc)

        return ProfileOut(
            id=profile_id,
            user_id=user_id,
            preferred_language=language,
            style_notes="",
            sample_messages=[],
            last_updated=now.isoformat()
        )
    
    async def update_profile(self, user_id: str, profile_data: ProfileUpdate) -> Optional[ProfileOut]:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            profile_data: Profile update data
            
        Returns:
            Optional[ProfileOut]: Updated profile or None
        """
        # Ensure profile exists
        if not await self.collection.find_one({"user_id": user_id}):
             await self.create_default_profile(user_id)

        update_fields = {"updated_at": datetime.utcnow()}

        if profile_data.preferred_language is not None:
            update_fields["preferred_language"] = profile_data.preferred_language
        if profile_data.style_notes is not None:
            update_fields["style_notes"] = profile_data.style_notes
        if profile_data.sample_messages is not None:
            update_fields["sample_messages"] = profile_data.sample_messages

        result = await self.collection.find_one_and_update(
            {"user_id": user_id},
            {"$set": update_fields},
            return_document=ReturnDocument.AFTER
        )

        if not result:
            return None

        return ProfileOut(
            id=result["id"],
            user_id=result["user_id"],
            preferred_language=result.get("preferred_language", "en"),
            style_notes=result.get("style_notes", ""),
            sample_messages=result.get("sample_messages", []),
            last_updated=result["updated_at"].isoformat() if isinstance(result["updated_at"], datetime) else result["updated_at"]
        )
