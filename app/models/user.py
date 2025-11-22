"""
User model for MongoDB users collection.
"""
from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class User(BaseModel):
    """User document model for MongoDB."""
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    username: str = Field(..., min_length=3, max_length=50)
    password_hash: str
    preferred_language: str = Field(default="en", pattern="^(en|ar)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
