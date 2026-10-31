"""
Cases router - CRUD operations for inspection cases
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import math
from app.database import get_db
from app.models.user import User, UserRole
from app.models.consumer import Consumer
from app.models.risk_score import RiskScore
from app.models.case import Case, CaseStatus
from app.models.audit_log import AuditLog
from app.schemas.case import (
    CaseCreate,
    CaseResponse,
    CaseListResponse,
    CaseListItem,
    CaseDetail
)
from app.schemas.audit_log import AuditLogResponse, AuditLogEntry
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create and assign a new inspection case.
    
    Creates a case record and logs the assignment to audit trail.
    
    Args:
        case_data: Case creation data (consumer_id, risk_score_id, assigned_to, note)
        current_user: Authenticated user (must be officer)
        db: Database session
        
    Returns:
        CaseResponse with created case info
        
    Raises:
        HTTPException: 404 if consumer/risk_score/inspector not found
        HTTPException: 403 if user is not an officer
    """
    # Authorization: Only officers can create cases
    if current_user.role != UserRole.OFFICER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only officers can create cases"
        )
    
    # Verify consumer exists
    consumer = db.query(Consumer).filter(Consumer.id == case_data.consumer_id).first()
    if not consumer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {case_data.consumer_id} not found"
        )
    
    # Verify risk score exists
    risk_score = db.query(RiskScore).filter(RiskScore.id == case_data.risk_score_id).first()
    if not risk_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk score {case_data.risk_score_id} not found"
        )
    
    # Verify inspector exists
    inspector = db.query(User).filter(
        User.id == case_data.assigned_to,
        User.role == UserRole.INSPECTOR
    ).first()
    if not inspector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspector {case_data.assigned_to} not found"
        )
    
    # Create case
    new_case = Case(
        consumer_id=case_data.consumer_id,
        risk_score_id=case_data.risk_score_id,
        assigned_by=current_user.id,
        assigned_to=case_data.assigned_to,
        status=CaseStatus.ASSIGNED,
        assignment_note=case_data.assignment_note
    )
    
    db.add(new_case)
    db.flush()  # Get the case ID
    
    # Create audit log entry
    audit_entry = AuditLog(
        actor_id=current_user.id,
        action="case_assigned",
        entity_type="case",
        entity_id=new_case.id,
        details={
            "consumer_id": str(case_data.consumer_id),
            "assigned_to": str(case_data.assigned_to),
            "assignment_note": case_data.assignment_note
        }
    )
    db.add(audit_entry)
    
    db.commit()
    db.refresh(new_case)
    
    return CaseResponse(
        case_id=new_case.id,
        status=new_case.status,
        created_at=new_case.created_at
    )


@router.get("", response_model=CaseListResponse)
def list_cases(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    feeder: Optional[str] = Query(None, description="Filter by feeder"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all cases with optional filters.
    
    Officers and circle managers see all cases.
    Inspectors see only their assigned cases.
    
    Args:
        status_filter: Optional status filter
        feeder: Optional feeder filter
        page: Page number
        page_size: Items per page
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Paginated case list with joined consumer/inspector data
    """
    # Build query with joins
    query = db.query(
        Case.id,
        Case.status,
        Case.created_at,
        Consumer.external_ref,
        Consumer.address,
        Consumer.feeder,
        RiskScore.risk_band,
        User.name.label("inspector_name")
    ).join(
        Consumer, Case.consumer_id == Consumer.id
    ).join(
        RiskScore, Case.risk_score_id == RiskScore.id
    ).outerjoin(
        User, Case.assigned_to == User.id
    )
    
    # Authorization: inspectors can only see their own cases
    if current_user.role == UserRole.INSPECTOR:
        query = query.filter(Case.assigned_to == current_user.id)
    
    # Apply filters
    if status_filter:
        try:
            status_enum = CaseStatus(status_filter.lower())
            query = query.filter(Case.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value"
            )
    
    if feeder:
        query = query.filter(Consumer.feeder == feeder)
    
    # Order by created date descending
    query = query.order_by(desc(Case.created_at))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    # Convert to response schema
    case_list_items = [
        CaseListItem(
            id=item[0],
            status=item[1],
            created_at=item[2],
            consumer_external_ref=item[3],
            consumer_address=item[4],
            feeder=item[5],
            risk_band=item[6],
            inspector_name=item[7]
        )
        for item in items
    ]
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return CaseListResponse(
        items=case_list_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/mine", response_model=CaseListResponse)
def get_my_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get cases assigned to the current inspector (mobile endpoint).
    
    Args:
        page: Page number
        page_size: Items per page
        current_user: Authenticated user (must be inspector)
        db: Database session
        
    Returns:
        Paginated case list for current inspector
        
    Raises:
        HTTPException: 403 if user is not an inspector
    """
    # Authorization: Only inspectors can access this endpoint
    if current_user.role != UserRole.INSPECTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for inspectors"
        )
    
    # Reuse list_cases logic but force inspector filter
    return list_cases(
        status_filter=None,
        feeder=None,
        page=page,
        page_size=page_size,
        current_user=current_user,
        db=db
    )


@router.get("/{case_id}", response_model=CaseDetail)
def get_case_detail(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full case detail with embedded consumer and risk info.
    
    Args:
        case_id: Case UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Full case detail with all related data
        
    Raises:
        HTTPException: 404 if case not found
        HTTPException: 403 if inspector tries to access another's case
    """
    # Query with all joins
    result = db.query(
        Case,
        Consumer,
        RiskScore,
        User.name.label("assigned_by_name"),
        User.id.label("assigned_by_id")
    ).join(
        Consumer, Case.consumer_id == Consumer.id
    ).join(
        RiskScore, Case.risk_score_id == RiskScore.id
    ).outerjoin(
        User, Case.assigned_by == User.id
    ).filter(
        Case.id == case_id
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found"
        )
    
    case, consumer, risk_score, assigned_by_name, assigned_by_id = result
    
    # Authorization: inspectors can only access their own cases
    if current_user.role == UserRole.INSPECTOR and case.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own cases"
        )
    
    # Get inspector name
    inspector = None
    inspector_name = None
    if case.assigned_to:
        inspector = db.query(User).filter(User.id == case.assigned_to).first()
        inspector_name = inspector.name if inspector else None
    
    return CaseDetail(
        id=case.id,
        status=case.status,
        assignment_note=case.assignment_note,
        created_at=case.created_at,
        updated_at=case.updated_at,
        consumer_id=consumer.id,
        consumer_external_ref=consumer.external_ref,
        consumer_address=consumer.address,
        feeder=consumer.feeder,
        meter_type=consumer.meter_type.value,
        risk_score=risk_score.score,
        risk_band=risk_score.risk_band,
        explanation_text_en=risk_score.explanation_text_en,
        explanation_text_ur=risk_score.explanation_text_ur,
        assigned_by_name=assigned_by_name,
        assigned_to_name=inspector_name,
        inspector_id=case.assigned_to
    )


@router.get("/{case_id}/audit-log", response_model=AuditLogResponse)
def get_case_audit_log(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit trail for a specific case.
    
    Returns all state changes for the case in chronological order.
    
    Args:
        case_id: Case UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of audit log entries with actor names
        
    Raises:
        HTTPException: 404 if case not found
    """
    # Verify case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found"
        )
    
    # Get audit log entries with actor names
    entries = db.query(
        AuditLog,
        User.name.label("actor_name")
    ).outerjoin(
        User, AuditLog.actor_id == User.id
    ).filter(
        AuditLog.entity_type == "case",
        AuditLog.entity_id == case_id
    ).order_by(
        AuditLog.created_at
    ).all()
    
    # Convert to response schema
    audit_entries = [
        AuditLogEntry(
            id=entry[0].id,
            actor_id=entry[0].actor_id,
            actor_name=entry[1] if entry[1] else "System",
            action=entry[0].action,
            entity_type=entry[0].entity_type,
            entity_id=entry[0].entity_id,
            details=entry[0].details,
            created_at=entry[0].created_at
        )
        for entry in entries
    ]
    
    return AuditLogResponse(entries=audit_entries)
