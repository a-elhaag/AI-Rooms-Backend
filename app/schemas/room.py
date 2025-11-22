"""
Room schemas for API requests and responses.
"""
from typing import Literal

from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    """Schema for room creation request."""
    
    name: str = Field(..., min_length=1, max_length=100)


class RoomJoin(BaseModel):
    """Schema for joining a room request."""
    
    join_code: str = Field(..., min_length=6, max_length=10)


class RoomOut(BaseModel):
    """Schema for room information in responses."""
    
    id: str
    name: str
    join_code: str
    created_at: str
    
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
