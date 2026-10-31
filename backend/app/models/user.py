"""
User model - represents officers, inspectors, and circle managers
"""
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    OFFICER = "officer"
    INSPECTOR = "inspector"
    CIRCLE_MANAGER = "circle_manager"


class User(Base):
    """
    User table - stores all system users with role-based access
    
    Availability rule: an inspector is considered "active" if last_seen_at 
    is within the last 15 minutes (threshold defined in config)
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
