"""
Case model - represents inspection cases assigned to field inspectors
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base
import enum


class CaseStatus(str, enum.Enum):
    """Case status enumeration"""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    CLOSED_CONFIRMED = "closed_confirmed"
    CLOSED_FALSE_POSITIVE = "closed_false_positive"
    CLOSED_INCONCLUSIVE = "closed_inconclusive"


class Case(Base):
    """
    Case table - tracks inspection assignments from creation to closure
    
    Status workflow: assigned → in_progress → closed_*
    """
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consumer_id = Column(UUID(as_uuid=True), ForeignKey("consumers.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score_id = Column(UUID(as_uuid=True), ForeignKey("risk_scores.id", ondelete="CASCADE"), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Officer who assigned")
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="Inspector assigned to case")
    status = Column(Enum(CaseStatus), nullable=False, default=CaseStatus.ASSIGNED, index=True)
    assignment_note = Column(String, nullable=True, comment="Optional note from officer")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
