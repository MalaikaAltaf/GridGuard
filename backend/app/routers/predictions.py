from fastapi import APIRouter, HTTPException
from typing import Any

from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.ml.inference import model_service

router = APIRouter()


@router.post("/evaluate", response_model=PredictionResponse)
def evaluate_prediction(request: PredictionRequest) -> Any:
    """
    Evaluate a consumer's usage to predict theft risk.

    Routes to PRECON (AMI) or SGCC (Conventional Monthly) branch.
    Response includes:
    - risk_score      : final hybrid score (ML + rule boost)
    - raw_ml_score    : raw RF .predict_proba() output
    - triggered_rules : list of deterministic rules that fired
    - if_anomaly_score: Isolation Forest outlier score (None if IF not trained)
    - if_is_anomaly   : whether IF flagged this consumer as an outlier
    """
    try:
        return model_service.predict(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="ML Model not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal prediction error: {str(e)}")


@router.get("/ml-status")
def ml_status() -> dict:
    """
    Returns the current state of all ML components:
    - Whether RF models are loaded
    - Calibrated thresholds in use
    - Isolation Forest training status
    """
    from app.ml.hybrid_scorer import SGCC_CALIBRATED_THRESHOLD, PRECON_CALIBRATED_THRESHOLD

    return {
        "rf_bundle_loaded": model_service.bundle_loaded,
        "thresholds": {
            "precon_threshold": model_service.precon_threshold,
            "sgcc_threshold_calibrated": model_service.sgcc_threshold,
            "sgcc_threshold_original_bundle": 0.50,
        },
        "isolation_forest": model_service.isolation_forest_status,
    }
