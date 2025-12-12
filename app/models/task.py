"""
Task model for MongoDB tasks collection.
"""
from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from app.models.user import PyObjectId


class Task(BaseModel):
    """Task document model for MongoDB."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")   # MongoDB _id
    room_id: PyObjectId                                           # Reference to the room
    title: str = Field(..., min_length=1, max_length=200)         # Task title
    status: Literal["todo", "in_progress", "done"] = "todo"       # Task status
    assignee_id: Optional[Union[PyObjectId, Literal["ai"]]] = None  # Assigned user or AI
    due_date: Optional[datetime] = None                            # Optional due date
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Timestamp

    class Config:
        populate_by_name = True              # allow using _id alias
        arbitrary_types_allowed = True       # allow PyObjectId
        json_encoders = {PyObjectId: str}    # convert ObjectId to str in JSON
