"""
Authentication schemas - login request and response
"""
from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class UserInfo(BaseModel):
    """User information returned in auth responses"""
    id: UUID
    name: str
    role: UserRole
    email: str
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Login response with JWT token and user info"""
    token: str
    user: UserInfo
