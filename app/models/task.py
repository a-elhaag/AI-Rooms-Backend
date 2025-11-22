"""
Task model for MongoDB tasks collection.
"""
from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from app.models.user import PyObjectId


class Task(BaseModel):
    """Task document model for MongoDB."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    room_id: PyObjectId
    title: str = Field(..., min_length=1, max_length=200)
    status: Literal["todo", "in_progress", "done"] = "todo"
    assignee_id: Optional[Union[PyObjectId, Literal["ai"]]] = None
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
