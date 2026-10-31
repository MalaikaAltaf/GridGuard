"""
Audit Log schemas - for viewing audit trail
"""
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime


class AuditLogEntry(BaseModel):
    """Single audit log entry"""
    id: UUID
    actor_id: Optional[UUID]
    actor_name: Optional[str]  # Joined from users table
    action: str
    entity_type: str
    entity_id: UUID
    details: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """List of audit log entries"""
    entries: List[AuditLogEntry]
