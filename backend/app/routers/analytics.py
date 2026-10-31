"""
Analytics router - model performance metrics
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.case import Case, CaseStatus
from app.models.inspection import Inspection, InspectionOutcome
from app.schemas.analytics import ModelPerformanceResponse, PerformanceTrendPoint
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/model-performance", response_model=ModelPerformanceResponse)
def get_model_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get model performance metrics and trends.
    
    Calculates confirmed/false-positive/inconclusive rates from closed cases.
    Provides weekly trend data for the performance chart.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Model performance metrics with trend data
    """
    # Get all closed cases with their inspection outcomes
    closed_cases = db.query(
        Case.id,
        Case.status,
        Case.created_at,
        Inspection.outcome
    ).join(
        Inspection, Case.id == Inspection.case_id
    ).filter(
        Case.status.in_([
            CaseStatus.CLOSED_CONFIRMED,
            CaseStatus.CLOSED_FALSE_POSITIVE,
            CaseStatus.CLOSED_INCONCLUSIVE
        ])
    ).all()
    
    # Calculate overall metrics
    total_cases = len(closed_cases)
    
    if total_cases == 0:
        # Return empty state
        return ModelPerformanceResponse(
            total_cases=0,
            confirmed_count=0,
            false_positive_count=0,
            inconclusive_count=0,
            confirmed_rate=0.0,
            false_positive_rate=0.0,
            inconclusive_rate=0.0,
            trend=[]
        )
    
    # Count outcomes
    confirmed_count = sum(1 for c in closed_cases if c.outcome == InspectionOutcome.CONFIRMED)
    false_positive_count = sum(1 for c in closed_cases if c.outcome == InspectionOutcome.FALSE_POSITIVE)
    inconclusive_count = sum(1 for c in closed_cases if c.outcome == InspectionOutcome.INCONCLUSIVE)
    
    # Calculate rates
    confirmed_rate = (confirmed_count / total_cases) * 100
    false_positive_rate = (false_positive_count / total_cases) * 100
    inconclusive_rate = (inconclusive_count / total_cases) * 100
    
    # Calculate weekly trend for last 12 weeks
    trend_data = []
    end_date = datetime.utcnow().date()
    
    for week_offset in range(11, -1, -1):  # Last 12 weeks
        week_start = end_date - timedelta(weeks=week_offset+1)
        week_end = end_date - timedelta(weeks=week_offset)
        
        # Filter cases in this week
        week_cases = [
            c for c in closed_cases
            if week_start <= c.created_at.date() < week_end
        ]
        
        week_total = len(week_cases)
        
        if week_total > 0:
            week_confirmed = sum(1 for c in week_cases if c.outcome == InspectionOutcome.CONFIRMED)
            week_fp = sum(1 for c in week_cases if c.outcome == InspectionOutcome.FALSE_POSITIVE)
            week_inc = sum(1 for c in week_cases if c.outcome == InspectionOutcome.INCONCLUSIVE)
            
            trend_data.append(PerformanceTrendPoint(
                date=week_end.isoformat(),
                confirmed_rate=(week_confirmed / week_total) * 100,
                false_positive_rate=(week_fp / week_total) * 100,
                inconclusive_rate=(week_inc / week_total) * 100,
                total_cases=week_total
            ))
        else:
            # Week with no data
            trend_data.append(PerformanceTrendPoint(
                date=week_end.isoformat(),
                confirmed_rate=0.0,
                false_positive_rate=0.0,
                inconclusive_rate=0.0,
                total_cases=0
            ))
    
    return ModelPerformanceResponse(
        total_cases=total_cases,
        confirmed_count=confirmed_count,
        false_positive_count=false_positive_count,
        inconclusive_count=inconclusive_count,
        confirmed_rate=round(confirmed_rate, 2),
        false_positive_rate=round(false_positive_rate, 2),
        inconclusive_rate=round(inconclusive_rate, 2),
        trend=trend_data
    )
