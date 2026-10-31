"""
Consumers router - risk queue, explanations, and consumption history
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from uuid import UUID
import math
from app.database import get_db
from app.models.user import User
from app.models.consumer import Consumer, MeterType
from app.models.risk_score import RiskScore, RiskBand
from app.models.consumption_history import ConsumptionHistory
from app.schemas.consumer import (
    RiskQueueResponse,
    RiskQueueItem,
    ExplanationResponse,
    ConsumptionHistoryResponse,
    ConsumptionDataPoint
)
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/risk-queue", response_model=RiskQueueResponse)
def get_risk_queue(
    feeder: Optional[str] = Query(None, description="Filter by feeder"),
    risk_band: Optional[str] = Query(None, description="Filter by risk band (high/medium/low)"),
    meter_type: Optional[str] = Query(None, description="Filter by meter type"),
    tariff_class: Optional[str] = Query(None, description="Filter by tariff class"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get ranked, filterable list of at-risk consumers.
    
    Returns consumers with risk scores, sorted by score DESC.
    Supports filtering by feeder, risk band, meter type, and tariff class.
    
    Args:
        feeder: Optional feeder filter
        risk_band: Optional risk band filter (high/medium/low)
        meter_type: Optional meter type filter
        tariff_class: Optional tariff class filter
        page: Page number (1-indexed)
        page_size: Items per page (max 100)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Paginated risk queue with consumer and risk score data
    """
    # Build query with joins
    query = db.query(
        Consumer.id,
        Consumer.external_ref,
        Consumer.address,
        Consumer.feeder,
        Consumer.tariff_class,
        Consumer.meter_type,
        Consumer.is_demo_data,
        RiskScore.score,
        RiskScore.risk_band,
        RiskScore.scored_at
    ).join(
        RiskScore, Consumer.id == RiskScore.consumer_id
    )
    
    # Apply filters
    if feeder:
        query = query.filter(Consumer.feeder == feeder)
    
    if risk_band:
        try:
            band_enum = RiskBand(risk_band.lower())
            query = query.filter(RiskScore.risk_band == band_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid risk_band value. Must be one of: high, medium, low"
            )
    
    if meter_type:
        try:
            meter_enum = MeterType(meter_type)
            query = query.filter(Consumer.meter_type == meter_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid meter_type value. Must be one of: Single Phase, Three Phase, CT-Metered"
            )
    
    if tariff_class:
        query = query.filter(Consumer.tariff_class == tariff_class)
    
    # Order by risk score descending (highest risk first)
    query = query.order_by(desc(RiskScore.score))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    # Convert to response schema
    risk_queue_items = [
        RiskQueueItem(
            id=item[0],
            external_ref=item[1],
            address=item[2],
            feeder=item[3],
            tariff_class=item[4],
            meter_type=item[5],
            is_demo_data=item[6],
            score=item[7],
            risk_band=item[8],
            scored_at=item[9]
        )
        for item in items
    ]
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return RiskQueueResponse(
        items=risk_queue_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{consumer_id}/explanation", response_model=ExplanationResponse)
def get_explanation(
    consumer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get plain-language SHAP explanation for a consumer's risk score.
    
    Returns both English and Urdu explanation text, plus raw SHAP data.
    
    Args:
        consumer_id: Consumer UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        ExplanationResponse with bilingual text and raw data
        
    Raises:
        HTTPException: 404 if consumer or risk score not found
    """
    # Get latest risk score for consumer
    risk_score = db.query(RiskScore).filter(
        RiskScore.consumer_id == consumer_id
    ).order_by(
        desc(RiskScore.scored_at)
    ).first()
    
    if not risk_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk score found for consumer {consumer_id}"
        )
    
    return ExplanationResponse(
        consumer_id=risk_score.consumer_id,
        score=risk_score.score,
        risk_band=risk_score.risk_band,
        explanation_text_en=risk_score.explanation_text_en,
        explanation_text_ur=risk_score.explanation_text_ur,
        explanation_raw=risk_score.explanation_raw,
        scored_at=risk_score.scored_at
    )


@router.get("/{consumer_id}/consumption-history", response_model=ConsumptionHistoryResponse)
def get_consumption_history(
    consumer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get monthly consumption trend data for a consumer.
    
    Returns up to 12 months of consumption history for trend chart display.
    
    Args:
        consumer_id: Consumer UUID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        ConsumptionHistoryResponse with trend series
        
    Raises:
        HTTPException: 404 if consumer not found
    """
    # Verify consumer exists
    consumer = db.query(Consumer).filter(Consumer.id == consumer_id).first()
    if not consumer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consumer {consumer_id} not found"
        )
    
    # Get consumption history ordered by period
    history = db.query(ConsumptionHistory).filter(
        ConsumptionHistory.consumer_id == consumer_id
    ).order_by(
        ConsumptionHistory.period_start
    ).all()
    
    # Convert to data points
    trend_series = [
        ConsumptionDataPoint(
            period_start=record.period_start.isoformat(),
            kwh=record.kwh
        )
        for record in history
    ]
    
    return ConsumptionHistoryResponse(
        consumer_id=consumer_id,
        trend_series=trend_series
    )
