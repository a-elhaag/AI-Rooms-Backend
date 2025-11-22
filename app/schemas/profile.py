"""
User profile schemas for API requests and responses.
"""
from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    """Schema for profile update request."""
    
    preferred_language: str = Field(default="en")
    style_notes: str = Field(default="")
    sample_messages: list[str] = Field(default_factory=list)


class ProfileOut(BaseModel):
    """Schema for profile information in responses."""
    
    id: str
    user_id: str
    preferred_language: str
    style_notes: str
    sample_messages: list[str]
    last_updated: str
    
    class Config:
        from_attributes = True
