"""
Consumer schemas - for risk queue, detail views, and explanations
"""
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from app.models.consumer import MeterType
from app.models.risk_score import RiskBand


class ConsumerBase(BaseModel):
    """Base consumer information"""
    id: UUID
    external_ref: str
    address: str
    feeder: str
    tariff_class: str
    meter_type: MeterType
    
    class Config:
        from_attributes = True


class RiskQueueItem(BaseModel):
    """Consumer item in the risk queue with score"""
    id: UUID
    external_ref: str
    address: str
    feeder: str
    tariff_class: str
    meter_type: MeterType
    score: float
    risk_band: RiskBand
    scored_at: datetime
    is_demo_data: bool
    
    class Config:
        from_attributes = True


class RiskQueueResponse(BaseModel):
    """Paginated risk queue response"""
    items: List[RiskQueueItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ConsumptionDataPoint(BaseModel):
    """Single month's consumption data"""
    period_start: str  # ISO date string
    kwh: float


class ExplanationResponse(BaseModel):
    """SHAP explanation with bilingual text"""
    consumer_id: UUID
    score: float
    risk_band: RiskBand
    explanation_text_en: str
    explanation_text_ur: str
    explanation_raw: dict
    scored_at: datetime
    
    class Config:
        from_attributes = True


class ConsumptionHistoryResponse(BaseModel):
    """Monthly consumption trend data"""
    consumer_id: UUID
    trend_series: List[ConsumptionDataPoint]
