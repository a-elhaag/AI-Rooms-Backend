"""
Room and RoomMember models for MongoDB.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.user import PyObjectId


class Room(BaseModel):
    """Room document model for MongoDB."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    join_code: str = Field(..., min_length=6, max_length=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class RoomMember(BaseModel):
    """Room member document model for MongoDB."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    room_id: PyObjectId
    user_id: PyObjectId
    role: Literal["owner", "member"] = "member"
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
