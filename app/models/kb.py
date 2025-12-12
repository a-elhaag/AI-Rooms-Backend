"""
RoomKB (Knowledge Base) model for MongoDB room_kb collection.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import PyObjectId


class RoomKB(BaseModel):
    """Room knowledge base document model for MongoDB."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    room_id: PyObjectId
    summary: str = ""
    key_decisions: List[str] = Field(default_factory=list)
    important_links: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class KnowledgeBaseResponse(BaseModel):
    """Response schema for Knowledge Base updates."""

    room_id: str
    summary: str
    key_decisions: List[str] = Field(default_factory=list)
    important_links: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True