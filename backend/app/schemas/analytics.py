"""
Analytics schemas - for model performance dashboard
"""
from pydantic import BaseModel
from typing import List


class PerformanceTrendPoint(BaseModel):
    """Single data point in performance trend"""
    date: str  # ISO date string
    confirmed_rate: float
    false_positive_rate: float
    inconclusive_rate: float
    total_cases: int


class ModelPerformanceResponse(BaseModel):
    """Model performance metrics and trends"""
    total_cases: int
    confirmed_count: int
    false_positive_count: int
    inconclusive_count: int
    confirmed_rate: float
    false_positive_rate: float
    inconclusive_rate: float
    trend: List[PerformanceTrendPoint]
