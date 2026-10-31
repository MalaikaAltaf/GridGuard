"""
ML Scoring Wrapper - generates risk scores with SHAP explanations

NOTE: This is a placeholder implementation that generates mock predictions.
Replace with actual ML model (joblib, xgboost, shap) when ML libraries are installed.
"""
from typing import Dict, Tuple
from uuid import UUID
import random
from app.config import settings
from app.models.risk_score import RiskBand


class MLScorer:
    """
    ML Scorer wrapper - loads model and generates predictions with explanations
    
    In production, this would:
    1. Load trained model from model.pkl using joblib
    2. Use SHAP TreeExplainer for feature importance
    3. Generate bilingual explanations from SHAP values
    """
    
    def __init__(self):
        """Initialize the scorer (would load model.pkl here in production)"""
        # Placeholder: In production, uncomment:
        # import joblib
        # self.model = joblib.load(settings.model_path)
        # self.explainer = shap.TreeExplainer(self.model)
        
        # Template explanations mapped to simulated top features
        self.explanation_templates = {
            "consumption_drop": {
                "en": "Consumption dropped by {value}% in the last 3 months compared to historical average.",
                "ur": "پچھلے 3 مہینوں میں بجلی کے استعمال میں {value} فیصد کمی واقع ہوئی ہے۔"
            },
            "irregular_pattern": {
                "en": "Consumption pattern shows irregular fluctuations inconsistent with tariff class behavior.",
                "ur": "بجلی کے استعمال میں غیر معمولی اتار چڑھاؤ نظر آ رہا ہے جو ٹیرف کلاس سے مطابقت نہیں رکھتا۔"
            },
            "zero_consumption": {
                "en": "Multiple billing cycles with near-zero consumption despite active connection.",
                "ur": "فعال کنکشن کے باوجود متعدد بلنگ سائیکلز میں صفر یا کم استعمال درج ہے۔"
            },
            "peak_hour_anomaly": {
                "en": "Peak hour consumption is {value}% lower than expected for this meter type.",
                "ur": "چوٹی کے اوقات میں استعمال اس میٹر قسم کی توقع سے {value} فیصد کم ہے۔"
            },
            "neighbor_comparison": {
                "en": "Consumption is {value}% below neighborhood average for similar premises.",
                "ur": "یہ استعمال اسی علاقے کے مشابہ صارفین سے {value} فیصد کم ہے۔"
            }
        }
    
    def score(self, consumer_id: UUID, features: Dict[str, float]) -> Dict:
        """
        Generate risk score and explanation for a consumer.
        
        Args:
            consumer_id: Consumer UUID
            features: Dictionary of feature values from consumption data
            
        Returns:
            Dictionary with score, risk_band, explanation_text_en, explanation_text_ur, explanation_raw
        """
        # PLACEHOLDER: Generate mock prediction
        # In production, this would call self.model.predict_proba(X)
        score = self._generate_mock_score(features)
        
        risk_band = self._get_risk_band(score)
        
        # Generate explanations
        explanation_text_en, explanation_text_ur, explanation_raw = self._generate_explanations(
            features, score
        )
        
        return {
            "consumer_id": str(consumer_id),
            "score": score,
            "risk_band": risk_band.value,
            "explanation_text_en": explanation_text_en,
            "explanation_text_ur": explanation_text_ur,
            "explanation_raw": explanation_raw
        }
    
    def _generate_mock_score(self, features: Dict[str, float]) -> float:
        """
        Generate a realistic mock risk score.
        
        In production, this would be:
        X = np.array([[features[f] for f in self.feature_names]])
        score = float(self.model.predict_proba(X)[0][1])
        """
        # Simulate score based on feature values
        base_score = 0.5
        
        if "consumption_drop_pct" in features:
            # Higher drop = higher risk
            drop = features["consumption_drop_pct"]
            if drop > 50:
                base_score += 0.3
            elif drop > 30:
                base_score += 0.2
        
        if "zero_billing_months" in features:
            # More zero months = higher risk
            zero_months = features["zero_billing_months"]
            base_score += (zero_months * 0.05)
        
        # Add some randomness
        score = base_score + random.uniform(-0.1, 0.1)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))
    
    def _get_risk_band(self, score: float) -> RiskBand:
        """
        Classify score into risk band based on configured thresholds.
        
        Args:
            score: Risk probability score (0-1)
            
        Returns:
            RiskBand enum value
        """
        if score >= settings.risk_band_high_threshold:
            return RiskBand.HIGH
        elif score >= settings.risk_band_medium_threshold:
            return RiskBand.MEDIUM
        else:
            return RiskBand.LOW
    
    def _generate_explanations(
        self, 
        features: Dict[str, float], 
        score: float
    ) -> Tuple[str, str, Dict]:
        """
        Generate bilingual explanations from features.
        
        In production, this would:
        1. Calculate SHAP values: shap_values = self.explainer.shap_values(X)[0]
        2. Find top contributing feature by absolute SHAP value
        3. Look up template for that feature
        4. Return both EN and UR strings from template
        
        Args:
            features: Feature dictionary
            score: Computed risk score
            
        Returns:
            Tuple of (english_text, urdu_text, raw_dict)
        """
        # Simulate SHAP-like feature importance
        feature_importance = {}
        
        if "consumption_drop_pct" in features:
            feature_importance["consumption_drop"] = features["consumption_drop_pct"] / 100.0
        
        if "zero_billing_months" in features:
            feature_importance["zero_consumption"] = features["zero_billing_months"] * 0.1
        
        if "peak_hour_ratio" in features:
            feature_importance["peak_hour_anomaly"] = abs(0.7 - features["peak_hour_ratio"])
        
        # Default feature if none provided
        if not feature_importance:
            feature_importance["irregular_pattern"] = 0.3
        
        # Find top feature
        top_feature = max(feature_importance.items(), key=lambda x: x[1])[0]
        
        # Get template
        template = self.explanation_templates.get(
            top_feature,
            self.explanation_templates["irregular_pattern"]
        )
        
        # Generate text with value substitution
        value = int(features.get("consumption_drop_pct", 45))
        explanation_en = template["en"].format(value=value)
        explanation_ur = template["ur"].format(value=value)
        
        # Raw explanation (simulates SHAP output)
        explanation_raw = {
            "top_feature": top_feature,
            "feature_contributions": feature_importance,
            "threshold_high": settings.risk_band_high_threshold,
            "threshold_medium": settings.risk_band_medium_threshold
        }
        
        return explanation_en, explanation_ur, explanation_raw


# Singleton instance - loaded once at module import
scorer = MLScorer()
