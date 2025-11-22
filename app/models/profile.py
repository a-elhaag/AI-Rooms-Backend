"""
UserProfile model for MongoDB user_profiles collection.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import PyObjectId


class UserProfile(BaseModel):
    """User profile document model for MongoDB."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId
    preferred_language: str = Field(default="en")
    style_notes: str = Field(default="")
    sample_messages: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
