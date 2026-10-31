"""
Users router - inspector listing with availability status
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import InspectorListItem
from app.auth.dependencies import get_current_user
from app.config import settings

router = APIRouter()


@router.get("", response_model=List[InspectorListItem])
def list_inspectors(
    role: str = Query("inspector", description="Filter by role"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List inspectors with computed availability status.
    
    An inspector is considered "available" if their last_seen_at timestamp
    is within the configured threshold (default 15 minutes).
    
    This endpoint is used by the "Assign Case" modal to show which
    inspectors are currently active.
    
    Args:
        role: Role filter (default: "inspector")
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of inspectors with availability flag
    """
    # Get all inspectors
    inspectors = db.query(User).filter(
        User.role == UserRole.INSPECTOR
    ).order_by(
        User.name
    ).all()
    
    # Calculate availability threshold
    threshold = datetime.utcnow() - timedelta(
        minutes=settings.inspector_availability_threshold_minutes
    )
    
    # Build response with availability status
    result = []
    for inspector in inspectors:
        available = False
        if inspector.last_seen_at:
            available = inspector.last_seen_at >= threshold
        
        result.append(InspectorListItem(
            id=inspector.id,
            name=inspector.name,
            email=inspector.email,
            last_seen_at=inspector.last_seen_at,
            available=available
        ))
    
    return result
