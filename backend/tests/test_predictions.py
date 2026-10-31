import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.schemas.prediction import PredictionResponse

client = TestClient(app)

@patch("app.routers.predictions.model_service")
def test_predict_ami_success(mock_model_service):
    # Setup mock response
    mock_model_service.predict.return_value = PredictionResponse(
        consumer_id="C001",
        meter_type="ami",
        model="precon_fa_rf",
        model_version="1.0.0",
        risk_score=0.85,
        decision="review_required",
        disclaimer="Test disclaimer"
    )

    # Make request
    payload = {
        "consumer_id": "C001",
        "meter_type": "ami",
        "hourly_usage_kwh": [1.0] * 24
    }
    
    response = client.post("/predictions/evaluate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["consumer_id"] == "C001"
    assert data["risk_score"] == 0.85
    assert data["decision"] == "review_required"
    
@patch("app.routers.predictions.model_service")
def test_predict_sgcc_success(mock_model_service):
    # Setup mock response
    mock_model_service.predict.return_value = PredictionResponse(
        consumer_id="C002",
        meter_type="conventional_monthly_history",
        model="sgcc_monthly_rf",
        model_version="2.1.0",
        risk_score=0.15,
        decision="low_risk",
        disclaimer="Test disclaimer"
    )

    # Make request
    payload = {
        "consumer_id": "C002",
        "meter_type": "conventional_monthly_history",
        "monthly_usage_history": [{"month": f"2024-{i:02d}", "usage_kwh": 200.0} for i in range(1, 13)]
    }
    
    response = client.post("/predictions/evaluate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["meter_type"] == "conventional_monthly_history"
    assert data["decision"] == "low_risk"
