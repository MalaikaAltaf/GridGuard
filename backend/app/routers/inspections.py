"""
Inspections router - photo upload and inspection submission
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
import os
import shutil
from app.database import get_db
from app.models.user import User, UserRole
from app.models.case import Case, CaseStatus
from app.models.inspection import Inspection, InspectionOutcome
from app.models.audit_log import AuditLog
from app.schemas.inspection import InspectionResponse
from app.auth.dependencies import get_current_user
from app.config import settings

router = APIRouter()


@router.post("/{case_id}/inspection", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
async def submit_inspection(
    case_id: UUID,
    outcome: str = Form(..., description="Inspection outcome: confirmed, false_positive, or inconclusive"),
    tampering_type: Optional[str] = Form(None, description="Comma-separated tampering types"),
    note: Optional[str] = Form(None, description="Inspector's notes"),
    gps_lat: Optional[float] = Form(None, description="GPS latitude"),
    gps_lng: Optional[float] = Form(None, description="GPS longitude"),
    submitted_at: str = Form(..., description="Device-local submission time (ISO 8601)"),
    photo: Optional[UploadFile] = File(None, description="Inspection photo"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit inspection results with optional photo and GPS.
    
    This endpoint handles multipart/form-data for photo upload.
    Updates case status based on outcome and logs to audit trail.
    
    Args:
        case_id: Case UUID
        outcome: Inspection outcome (confirmed/false_positive/inconclusive)
        tampering_type: Comma-separated list of tampering types
        note: Optional inspector notes
        gps_lat: GPS latitude
        gps_lng: GPS longitude
        submitted_at: Device-local submission timestamp (ISO string)
        photo: Optional inspection photo file
        current_user: Authenticated user (must be inspector)
        db: Database session
        
    Returns:
        InspectionResponse with inspection ID and sync timestamp
        
    Raises:
        HTTPException: 404 if case not found
        HTTPException: 403 if user is not the assigned inspector
        HTTPException: 400 if outcome is invalid
    """
    # Authorization: Only inspectors can submit inspections
    if current_user.role != UserRole.INSPECTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only inspectors can submit inspections"
        )
    
    # Verify case exists and is assigned to current inspector
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found"
        )
    
    if case.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit inspections for your assigned cases"
        )
    
    # Validate outcome
    try:
        outcome_enum = InspectionOutcome(outcome.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid outcome. Must be: confirmed, false_positive, or inconclusive"
        )
    
    # Parse tampering types
    tampering_list = None
    if tampering_type:
        tampering_list = [t.strip() for t in tampering_type.split(",") if t.strip()]
    
    # Parse submitted_at timestamp
    try:
        submitted_timestamp = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid submitted_at format. Use ISO 8601 format"
        )
    
    # Handle photo upload
    photo_url = None
    if photo:
        # Generate unique filename
        file_extension = os.path.splitext(photo.filename)[1] if photo.filename else ".jpg"
        unique_filename = f"{uuid4()}{file_extension}"
        
        # Ensure storage directory exists
        storage_path = settings.storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(storage_path, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        
        # Store relative path
        photo_url = f"{storage_path}/{unique_filename}"
    
    # Create inspection record
    inspection = Inspection(
        case_id=case_id,
        inspector_id=current_user.id,
        outcome=outcome_enum,
        tampering_type=tampering_list,
        note=note,
        photo_url=photo_url,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        submitted_at=submitted_timestamp,
        synced_at=datetime.utcnow()  # Server receipt time
    )
    
    db.add(inspection)
    db.flush()
    
    # Update case status based on outcome
    if outcome_enum == InspectionOutcome.CONFIRMED:
        case.status = CaseStatus.CLOSED_CONFIRMED
    elif outcome_enum == InspectionOutcome.FALSE_POSITIVE:
        case.status = CaseStatus.CLOSED_FALSE_POSITIVE
    else:
        case.status = CaseStatus.CLOSED_INCONCLUSIVE
    
    case.updated_at = datetime.utcnow()
    
    # Create audit log entry
    audit_entry = AuditLog(
        actor_id=current_user.id,
        action="inspection_submitted",
        entity_type="case",
        entity_id=case_id,
        details={
            "inspection_id": str(inspection.id),
            "outcome": outcome_enum.value,
            "has_photo": photo_url is not None,
            "has_gps": gps_lat is not None and gps_lng is not None
        }
    )
    db.add(audit_entry)
    
    db.commit()
    db.refresh(inspection)
    
    return InspectionResponse(
        id=inspection.id,
        case_id=inspection.case_id,
        outcome=inspection.outcome,
        synced_at=inspection.synced_at
    )
