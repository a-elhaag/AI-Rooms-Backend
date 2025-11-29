"""
Authentication schemas for API requests and responses.
"""
from typing import Optional

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


class ProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    preferred_language: Optional[str] = Field(None, pattern="^(en|ar)$")


class PasswordChange(BaseModel):
    """Schema for changing user password."""
    
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=100)
