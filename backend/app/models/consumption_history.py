"""
Consumption History model - stores monthly consumption data for trend charts
"""
from sqlalchemy import Column, Float, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base


class ConsumptionHistory(Base):
    """
    Consumption History table - monthly kWh data per consumer
    
    Populated at data-ingest time from source dataset (SGCC/PRECON)
    One row per consumer per billing month
    This is the sole source for the Consumer Detail 12-month trend chart
    """
    __tablename__ = "consumption_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consumer_id = Column(UUID(as_uuid=True), ForeignKey("consumers.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start = Column(Date, nullable=False, comment="First day of the billing month")
    kwh = Column(Float, nullable=False, comment="Billed/recorded consumption for that period")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
