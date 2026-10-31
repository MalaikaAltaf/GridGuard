"""
Consumer model - represents electricity consumers in the distribution system
"""
from sqlalchemy import Column, String, Float, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base
import enum


class MeterType(str, enum.Enum):
    """Meter type enumeration"""
    SINGLE_PHASE = "Single Phase"
    THREE_PHASE = "Three Phase"
    CT_METERED = "CT-Metered"


class Consumer(Base):
    """
    Consumer table - stores consumer/meter information
    
    Coordinates (latitude/longitude) are populated once at seed/ingest time
    for use in the Feeder Map visualization
    """
    __tablename__ = "consumers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_ref = Column(String, nullable=False, index=True, comment="Meter/consumer ID from source dataset")
    address = Column(String, nullable=False)
    feeder = Column(String, nullable=False, index=True, comment="Used for filtering and map visualization")
    tariff_class = Column(String, nullable=False)
    meter_type = Column(Enum(MeterType), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_demo_data = Column(Boolean, default=True, nullable=False, comment="Drives 'demo data' UI label")
