"""
Message model for MongoDB messages collection.
"""
from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from app.models.user import PyObjectId


class Message(BaseModel):
    """Message document model for MongoDB."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    room_id: PyObjectId
    user_id: Optional[Union[PyObjectId, Literal["ai"]]] = None
    content: str
    type: Literal["text", "image", "system"] = "text"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
