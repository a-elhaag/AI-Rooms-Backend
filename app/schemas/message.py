"""
Message schemas for API requests and responses.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for message creation request."""
    
    content: str = Field(..., min_length=1)
    type: Literal["text", "image", "system"] = "text"


class MessageOut(BaseModel):
    """Schema for message information in responses."""
    
    id: str
    room_id: str
    user_id: Optional[str] = None
    username: Optional[str] = None  # "AI" for AI messages, username for user messages
    content: str
    type: Literal["text", "image", "system"]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageListParams(BaseModel):
    """Schema for message list query parameters."""
    
    limit: int = Field(default=50, ge=1, le=100)
    before: Optional[str] = None  # Message ID for pagination
