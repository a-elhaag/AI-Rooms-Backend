"""
Message model for MongoDB messages collection.
"""
from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from app.models.user import PyObjectId


class Message(BaseModel):
    """Message document model for MongoDB."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")  # MongoDB document _id
    room_id: PyObjectId                                         # reference to Room
    user_id: Optional[Union[PyObjectId, Literal["ai"]]] = None  # user or AI sender
    content: str                                                # message content
    type: Literal["text", "image", "system"] = "text"           # message type
    created_at: datetime = Field(default_factory=datetime.utcnow)  # creation timestamp

    class Config:
        populate_by_name = True              # allows alias usage (_id) in input/output
        arbitrary_types_allowed = True       # allows PyObjectId type
        json_encoders = {PyObjectId: str}    # encode ObjectId as str in JSON