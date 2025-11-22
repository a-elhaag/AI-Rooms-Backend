"""
Room goal schemas for API requests and responses.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    """Schema for goal creation request."""
    
    description: str = Field(..., min_length=1)
    priority: int = Field(default=0, ge=0)


class GoalUpdate(BaseModel):
    """Schema for goal update request."""
    
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[int] = Field(None, ge=0)
    status: Optional[Literal["active", "done", "stalled"]] = None


class GoalOut(BaseModel):
    """Schema for goal information in responses."""
    
    id: str
    room_id: str
    description: str
    priority: int
    status: Literal["active", "done", "stalled"]
    created_by: str
    created_by_username: str  # Joined from user data
    created_at: str
    
    class Config:
        from_attributes = True
