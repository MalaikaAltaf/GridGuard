"""
Case schemas - for case creation, listing, and detail views
"""
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from app.models.case import CaseStatus
from app.models.risk_score import RiskBand


class CaseCreate(BaseModel):
    """Request schema for creating a new case"""
    consumer_id: UUID
    risk_score_id: UUID
    assigned_to: UUID
    assignment_note: Optional[str] = None


class CaseBase(BaseModel):
    """Base case information"""
    id: UUID
    consumer_id: UUID
    risk_score_id: UUID
    assigned_by: Optional[UUID]
    assigned_to: Optional[UUID]
    status: CaseStatus
    assignment_note: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CaseListItem(BaseModel):
    """Case item for list view with joined data"""
    id: UUID
    consumer_external_ref: str
    consumer_address: str
    feeder: str
    risk_band: RiskBand
    inspector_name: Optional[str]
    status: CaseStatus
    created_at: datetime


class CaseDetail(BaseModel):
    """Full case detail with embedded consumer and risk info"""
    id: UUID
    status: CaseStatus
    assignment_note: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Consumer info
    consumer_id: UUID
    consumer_external_ref: str
    consumer_address: str
    feeder: str
    meter_type: str
    
    # Risk info
    risk_score: float
    risk_band: RiskBand
    explanation_text_en: str
    explanation_text_ur: str
    
    # Assignment info
    assigned_by_name: Optional[str]
    assigned_to_name: Optional[str]
    inspector_id: Optional[UUID]


class CaseResponse(BaseModel):
    """Response after case creation"""
    case_id: UUID
    status: CaseStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    """Paginated case list response"""
    items: List[CaseListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
