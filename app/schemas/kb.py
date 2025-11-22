"""
Room knowledge base schemas for API requests and responses.
"""
from pydantic import BaseModel, Field


class KBUpdate(BaseModel):
    """Schema for knowledge base update request."""
    
    summary: str = Field(default="")
    key_decisions: list[str] = Field(default_factory=list)
    important_links: list[str] = Field(default_factory=list)


class KBOut(BaseModel):
    """Schema for knowledge base information in responses."""
    
    id: str
    room_id: str
    summary: str
    key_decisions: list[str]
    important_links: list[str]
    last_updated: str
    
    class Config:
        from_attributes = True
