"""
Message schemas for API requests and responses.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for message creation request."""
    
    content: str = Field(..., min_length=1)
    sender_type: Literal["user", "ai", "system"] = "user"


class MessageOut(BaseModel):
    """Schema for message information in responses."""
    
    id: str
    room_id: str
    sender_id: Optional[str] = None  # User ID or 'ai'
    sender_name: Optional[str] = None  # Username or 'AI Assistant'
    sender_type: Literal["user", "ai", "system"] = "user"
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageListParams(BaseModel):
    """Schema for message list query parameters."""
    
    limit: int = Field(default=50, ge=1, le=100)
    before: Optional[str] = None  # Message ID for pagination
