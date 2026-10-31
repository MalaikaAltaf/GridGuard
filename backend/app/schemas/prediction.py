from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class MonthlyUsage(BaseModel):
    month: str = Field(..., description="Month in YYYY-MM format", example="2024-01")
    usage_kwh: float = Field(..., description="Consumption in kWh", example=245.4)

class PredictionRequest(BaseModel):
    consumer_id: str = Field(..., description="Unique consumer identifier", example="C001")
    meter_type: Literal["ami", "conventional_monthly_history"] = Field(
        ..., description="Type of meter data being provided"
    )
    date: Optional[str] = Field(None, description="Date for the prediction, mostly for AMI", example="2026-09-21")
    hourly_usage_kwh: Optional[List[float]] = Field(
        None, description="24 hourly consumption values for AMI meters"
    )
    monthly_usage_history: Optional[List[MonthlyUsage]] = Field(
        None, description="Monthly billing history for conventional meters"
    )

class PredictionResponse(BaseModel):
    consumer_id: str
    meter_type: str
    model: str
    model_version: str

    # Scores
    risk_score: float = Field(..., description="Final combined hybrid score (0-1)")
    raw_ml_score: Optional[float] = Field(None, description="Raw RF model score before hybrid boost")

    # Decision
    decision: str = Field(..., description="review_required | low_risk | insufficient_history")
    disclaimer: str

    # Hybrid rule details
    triggered_rules: Optional[List[str]] = Field(
        default=None,
        description="Deterministic rules that fired and boosted the score"
    )

    # Isolation Forest
    if_anomaly_score: Optional[float] = Field(
        default=None,
        description="Isolation Forest anomaly score (0-1, higher = more anomalous). "
                    "None if IF model is not yet trained."
    )
    if_is_anomaly: Optional[bool] = Field(
        default=None,
        description="True if Isolation Forest classified this consumer as an outlier"
    )
