"""
User schemas - for inspector listing and availability
"""
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user information"""
    id: UUID
    name: str
    role: UserRole
    email: str
    
    class Config:
        from_attributes = True


class InspectorListItem(BaseModel):
    """Inspector with computed availability status"""
    id: UUID
    name: str
    email: str
    last_seen_at: Optional[datetime]
    available: bool  # Computed from last_seen_at threshold
    
    class Config:
        from_attributes = True
