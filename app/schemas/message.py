"""
Message schemas for API requests and responses.
"""
from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for message creation request."""
    
    content: str = Field(..., min_length=1)
    sender_type: Literal["user", "ai", "system"] = "user"
    reply_to: Optional[str] = None  # Message ID being replied to


class MessageOut(BaseModel):
    """Schema for message information in responses."""
    
    id: str
    room_id: str
    sender_id: Optional[str] = None  # User ID or 'ai'
    sender_name: Optional[str] = None  # Username or 'AI Assistant'
    sender_type: Literal["user", "ai", "system"] = "user"
    content: str
    reply_to: Optional[str] = None  # Message ID this is replying to
    reactions: Optional[Dict[str, int]] = None  # {emoji: count}
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageListParams(BaseModel):
    """Schema for message list query parameters."""
    
    limit: int = Field(default=50, ge=1, le=100)
    before: Optional[str] = None  # Message ID for pagination
