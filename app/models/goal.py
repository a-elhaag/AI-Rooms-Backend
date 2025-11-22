"""
RoomGoal model for MongoDB room_goals collection.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.user import PyObjectId


class RoomGoal(BaseModel):
    """Room goal document model for MongoDB."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    room_id: PyObjectId
    description: str = Field(..., min_length=1)
    priority: int = Field(default=0, ge=0)
    status: Literal["active", "done", "stalled"] = "active"
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
