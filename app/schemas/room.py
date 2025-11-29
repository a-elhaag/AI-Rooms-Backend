"""
Room schemas for API requests and responses.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    """Schema for room creation request."""
    
    name: str = Field(..., min_length=1, max_length=100)
    custom_ai_instructions: Optional[str] = None


class RoomJoin(BaseModel):
    """Schema for joining a room request."""
    
    join_code: str = Field(..., min_length=6, max_length=10)


class RoomOut(BaseModel):
    """Schema for room information in responses."""
    
    id: str
    name: str
    join_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    member_count: int = 1
    message_count: int = 0
    has_ai: bool = True
    description: Optional[str] = None
    custom_ai_instructions: Optional[str] = None
    
    class Config:
        from_attributes = True


class RoomMemberOut(BaseModel):
    """Schema for room member information in responses."""
    
    id: str
    room_id: str
    user_id: str
    username: str  # Joined from user data
    role: Literal["owner", "member"]
    joined_at: str
    
    class Config:
        from_attributes = True
