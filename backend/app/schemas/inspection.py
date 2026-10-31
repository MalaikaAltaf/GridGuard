"""
Inspection schemas - for submitting and viewing inspection results
"""
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from app.models.inspection import InspectionOutcome


class InspectionCreate(BaseModel):
    """Request schema for creating an inspection (from mobile app)"""
    outcome: InspectionOutcome
    tampering_type: Optional[List[str]] = None
    note: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    submitted_at: datetime  # Device-local time


class InspectionResponse(BaseModel):
    """Response after inspection submission"""
    id: UUID
    case_id: UUID
    outcome: InspectionOutcome
    synced_at: datetime
    
    class Config:
        from_attributes = True


class InspectionDetail(BaseModel):
    """Full inspection detail"""
    id: UUID
    case_id: UUID
    inspector_id: Optional[UUID]
    outcome: InspectionOutcome
    tampering_type: Optional[List[str]]
    note: Optional[str]
    photo_url: Optional[str]
    gps_lat: Optional[float]
    gps_lng: Optional[float]
    submitted_at: datetime
    synced_at: Optional[datetime]
    
    class Config:
        from_attributes = True
