"""
Task model for MongoDB tasks collection.
"""
from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from app.models.user import PyObjectId


class Task(BaseModel):
    """MongoDB Task document model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")           # MongoDB _id
    room_id: PyObjectId                                                   # Room reference
    title: str = Field(..., min_length=1, max_length=200)                 # Task title
    status: Literal["todo", "in_progress", "done"] = "todo"               # Task status
    assignee_id: Optional[Union[PyObjectId, Literal["ai"]]] = None        # Assigned user or AI
    due_date: Optional[datetime] = None                                    # Optional due date
    created_at: datetime = Field(default_factory=datetime.utcnow)         # Creation timestamp

    class Config:
        populate_by_name = True              # Allow using _id alias
        arbitrary_types_allowed = True       # Allow PyObjectId type
        json_encoders = {PyObjectId: str}    # Convert ObjectId to string for JSON
