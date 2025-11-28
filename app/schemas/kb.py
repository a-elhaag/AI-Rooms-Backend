"""
Room knowledge base schemas for API requests and responses.
"""
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class ResourceItem(BaseModel):
    """A resource item in the knowledge base."""
    title: str
    url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None  # doc, code, design, reference, etc.


class KBLink(BaseModel):
    """An important link in the knowledge base."""
    title: str
    url: str


class KBResource(BaseModel):
    """A resource in the knowledge base."""
    title: str
    url: str
    description: Optional[str] = None


class KBUpdate(BaseModel):
    """Schema for knowledge base update request."""
    
    summary: Optional[str] = Field(default=None)
    key_decisions: Optional[List[str]] = Field(default=None)
    important_links: Optional[List[Union[str, KBLink]]] = Field(default=None)
    resources: Optional[List[Union[ResourceItem, KBResource]]] = Field(default=None)


class KBAppend(BaseModel):
    """Schema for appending items to KB lists."""
    
    key_decision: Optional[str] = None
    important_link: Optional[Union[str, KBLink]] = None
    resource: Optional[Union[ResourceItem, KBResource]] = None


class KBOut(BaseModel):
    """Schema for knowledge base information in responses."""
    
    id: str
    room_id: str
    summary: str
    key_decisions: List[str]
    important_links: List[Union[str, KBLink]] = Field(default_factory=list)
    resources: List[Union[ResourceItem, KBResource]] = Field(default_factory=list)
    last_updated: str
    
    class Config:
        from_attributes = True
