"""
Authentication schemas for API requests and responses.
"""
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """Schema for user registration request."""
    
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=3, max_length=100)  # Relaxed for POC
    preferred_language: str = Field(default="en", pattern="^(en|ar)$")


class UserLogin(BaseModel):
    """Schema for user login request."""
    
    username: str
    password: str


class UserOut(BaseModel):
    """Schema for user information in responses."""
    
    id: str
    username: str
    preferred_language: str
    created_at: str
    
    class Config:
        from_attributes = True
