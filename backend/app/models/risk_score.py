"""
Risk Score model - stores ML model predictions and explanations
"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.database import Base
import enum


class RiskBand(str, enum.Enum):
    """Risk band classification"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskScore(Base):
    """
    Risk Score table - stores ML predictions with bilingual SHAP explanations
    
    Explanation text is precomputed in both English and Urdu (hand-written 
    templates, not machine translation) for deterministic display
    """
    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consumer_id = Column(UUID(as_uuid=True), ForeignKey("consumers.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, nullable=False, comment="Probability score 0-1")
    risk_band = Column(Enum(RiskBand), nullable=False, index=True)
    explanation_text_en = Column(String, nullable=False, comment="Plain-language SHAP explanation in English")
    explanation_text_ur = Column(String, nullable=False, comment="Plain-language SHAP explanation in Urdu")
    explanation_raw = Column(JSONB, nullable=False, comment="Raw SHAP feature/value pairs for debugging")
    scored_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
