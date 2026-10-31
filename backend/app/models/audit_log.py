"""
Audit Log model - immutable log of all state changes for auditability
"""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.database import Base


class AuditLog(Base):
    """
    Audit Log table - append-only, never updated or deleted
    
    Records every significant state change with timestamp and actor
    Provides complete audit trail for compliance and debugging
    """
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="null = system event")
    action = Column(String, nullable=False, index=True, comment="e.g., flag_generated, case_assigned, inspection_submitted")
    entity_type = Column(String, nullable=False, comment="Type of entity affected (case, consumer, inspection)")
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    details = Column(JSONB, nullable=True, comment="Additional context as JSON")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
