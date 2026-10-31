"""
Inference engine for Grid-Guard AI.
Integrates:
  1. Random Forest models (PRECON/AMI + SGCC/Monthly)
  2. Threshold calibration (SGCC: 0.50 → 0.20)
  3. Hybrid rule-based overlay (boosts score when deterministic rules fire)
  4. Isolation Forest anomaly detection (if DB has >= 34-month history)
"""
import os
import json
import joblib
import numpy as np
from typing import Optional
import logging

from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.ml.feature_engineering import build_sgcc_monthly_features, format_precon_ami_features
from app.ml.hybrid_scorer import (
    apply_sgcc_hybrid_rules,
    apply_precon_hybrid_rules,
    SGCC_CALIBRATED_THRESHOLD,
    PRECON_CALIBRATED_THRESHOLD,
)
from app.ml.isolation_forest import isolation_detector

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ML_ARTIFACT_DIR = os.path.join(BASE_DIR, "ml-artifact")
MODEL_PATH      = os.path.join(ML_ARTIFACT_DIR, "grid_guard_model.pkl")
SGCC_FEATURES_PATH = os.path.join(ML_ARTIFACT_DIR, "sgcc_monthly_feature_names.json")


class GridGuardModel:
    """
    Singleton inference engine.
    Loads the trained RF bundle and applies hybrid scoring + IF anomaly detection.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_models()
        return cls._instance

    # ── Startup ────────────────────────────────────────────────────────────────

    def load_models(self):
        try:
            logger.info(f"Loading ML bundle from {MODEL_PATH}...")
            self.bundle = joblib.load(MODEL_PATH)

            # PRECON branch
            self.precon_model     = self.bundle["precon_fa_rf"]
            self.precon_features  = self.bundle.get("precon_fa_features")
            # Use calibrated threshold if provided, else keep bundle value
            bundle_precon_thresh  = self.bundle["precon_threshold"]
            self.precon_threshold = (
                PRECON_CALIBRATED_THRESHOLD
                if PRECON_CALIBRATED_THRESHOLD is not None
                else bundle_precon_thresh
            )

            # SGCC branch — use calibrated threshold (0.20) instead of bundle (0.50)
            self.sgcc_model     = self.bundle["sgcc_monthly_rf"]
            self.sgcc_threshold = SGCC_CALIBRATED_THRESHOLD   # ← calibrated

            with open(SGCC_FEATURES_PATH, "r") as f:
                self.sgcc_feature_names = json.load(f)

            logger.info(
                f"ML bundle loaded. "
                f"PRECON threshold={self.precon_threshold}, "
                f"SGCC threshold={self.sgcc_threshold} (calibrated)"
            )
            self.bundle_loaded = True

        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            self.bundle = None
            self.bundle_loaded = False

    def init_isolation_forest(self, db_session) -> None:
        """
        Call this once after the DB is ready (e.g., from the FastAPI lifespan event).
        Checks if sufficient 34-month history exists; trains IF if so.
        """
        logger.info("Attempting to initialise Isolation Forest from DB...")
        success = isolation_detector.train_from_db(db_session)
        if success:
            logger.info(
                f"Isolation Forest ready: {isolation_detector.status}"
            )
        else:
            logger.warning(
                "Isolation Forest not trained (insufficient DB history). "
                "IF scores will be None in responses."
            )

    # ── Public predict ─────────────────────────────────────────────────────────

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        if not self.bundle_loaded:
            raise RuntimeError("ML Models are not loaded")

        if request.meter_type == "ami":
            return self._predict_precon(request)
        elif request.meter_type == "conventional_monthly_history":
            return self._predict_sgcc_monthly(request)
        else:
            raise ValueError(f"Unsupported meter_type: {request.meter_type}")

    # ── PRECON / AMI ───────────────────────────────────────────────────────────

    def _predict_precon(self, request: PredictionRequest) -> PredictionResponse:
        if not request.hourly_usage_kwh:
            raise ValueError("hourly_usage_kwh is required for AMI predictions")

        x = format_precon_ami_features(request.hourly_usage_kwh, self.precon_features)
        x = x.reshape(1, -1)
        x_input = x[:, self.precon_features] if self.precon_features is not None else x

        raw_ml_score = float(self.precon_model.predict_proba(x_input)[0, 1])

        # Hybrid overlay
        hybrid_score, _, decision, triggered_rules = apply_precon_hybrid_rules(
            ml_score=raw_ml_score,
            hourly_usage=request.hourly_usage_kwh,
            threshold=self.precon_threshold,
        )

        # IF detector not applicable for hourly AMI data (needs monthly history)
        return PredictionResponse(
            consumer_id=request.consumer_id,
            meter_type=request.meter_type,
            model="precon_fa_rf",
            model_version="1.0.0-ami-precon",
            risk_score=round(hybrid_score, 6),
            raw_ml_score=round(raw_ml_score, 6),
            decision=decision,
            disclaimer="Screening signal based on hourly anomaly detection. Human review required.",
            triggered_rules=triggered_rules if triggered_rules else None,
            if_anomaly_score=None,
            if_is_anomaly=None,
        )

    # ── SGCC / Monthly ─────────────────────────────────────────────────────────

    def _predict_sgcc_monthly(self, request: PredictionRequest) -> PredictionResponse:
        if not request.monthly_usage_history:
            raise ValueError("monthly_usage_history is required for conventional meter predictions")

        try:
            history = [
                item.dict() if hasattr(item, "dict") else item
                for item in request.monthly_usage_history
            ]

            features = build_sgcc_monthly_features(history, self.sgcc_feature_names)
            x = features.reshape(1, -1)
            raw_ml_score = float(self.sgcc_model.predict_proba(x)[0, 1])

            # Hybrid overlay (calibrated threshold applied inside)
            hybrid_score, _, decision, triggered_rules = apply_sgcc_hybrid_rules(
                ml_score=raw_ml_score,
                monthly_history=history,
                threshold=self.sgcc_threshold,
            )

            # Isolation Forest
            if_result = self._run_isolation_forest(history)
            if_anomaly_score = round(if_result[0], 6) if if_result else None
            if_is_anomaly    = if_result[1] if if_result else None

            # If IF flags it as an anomaly, bump decision to review_required
            if if_is_anomaly and decision == "low_risk":
                decision = "review_required"
                if triggered_rules is None:
                    triggered_rules = []
                triggered_rules.append(
                    "Isolation Forest flagged this consumption pattern as a statistical outlier"
                )

            return PredictionResponse(
                consumer_id=request.consumer_id,
                meter_type=request.meter_type,
                model="sgcc_monthly_rf",
                model_version="2.1.0-monthly-sgcc+hybrid",
                risk_score=round(hybrid_score, 6),
                raw_ml_score=round(raw_ml_score, 6),
                decision=decision,
                disclaimer="Screening signal combining RF model + rule overlay. Requires inspection.",
                triggered_rules=triggered_rules if triggered_rules else None,
                if_anomaly_score=if_anomaly_score,
                if_is_anomaly=if_is_anomaly,
            )

        except ValueError as e:
            return PredictionResponse(
                consumer_id=request.consumer_id,
                meter_type=request.meter_type,
                model="sgcc_monthly_rf",
                model_version="2.1.0-monthly-sgcc+hybrid",
                risk_score=0.0,
                raw_ml_score=0.0,
                decision="insufficient_history",
                disclaimer=str(e),
                triggered_rules=None,
                if_anomaly_score=None,
                if_is_anomaly=None,
            )

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _run_isolation_forest(self, history):
        """Run IF prediction; returns (score, is_anomaly) or None."""
        try:
            kwh_values = [h["usage_kwh"] for h in history]
            return isolation_detector.predict(kwh_values)
        except Exception as e:
            logger.warning(f"IsolationForest prediction failed: {e}")
            return None

    @property
    def isolation_forest_status(self) -> dict:
        return isolation_detector.status


# ── Singleton instance (loaded once at import) ─────────────────────────────────
model_service = GridGuardModel()
