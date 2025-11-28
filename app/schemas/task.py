"""
Task schemas for API requests and responses.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Schema for task creation request."""
    
    title: str = Field(..., min_length=1, max_length=200)
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Schema for task update request."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[Literal["todo", "in_progress", "done"]] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskOut(BaseModel):
    """Schema for task information in responses."""
    
    id: str
    room_id: str
    room_name: Optional[str] = None  # Room name for display in global tasks view
    title: str
    status: Literal["todo", "in_progress", "done"]
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None  # "AI" or username
    due_date: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True
