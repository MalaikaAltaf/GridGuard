"""
Inspection model - stores field inspection results with photo and GPS
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base
import enum


class InspectionOutcome(str, enum.Enum):
    """Inspection outcome classification"""
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    INCONCLUSIVE = "inconclusive"


class Inspection(Base):
    """
    Inspection table - records field inspection results
    
    submitted_at: device-local time (may predate server receipt)
    synced_at: null while pending mobile sync, set when successfully uploaded
    """
    __tablename__ = "inspections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    inspector_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    outcome = Column(Enum(InspectionOutcome), nullable=False, index=True)
    tampering_type = Column(ARRAY(String), nullable=True, comment="Checklist selections (e.g., bypass wire, meter reversed)")
    note = Column(String, nullable=True)
    photo_url = Column(String, nullable=True, comment="Path/URL in object storage")
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    submitted_at = Column(DateTime, nullable=False, comment="Device-local submission time")
    synced_at = Column(DateTime, nullable=True, default=datetime.utcnow, comment="Server receipt timestamp")
