"""
Isolation Forest anomaly detector.

At startup, checks if the DB has enough consumers with >= 34 months of history.
- If YES: trains IsolationForest on those consumer vectors and uses it for scoring.
- If NO:  gracefully skips training and logs a warning. The predict() method
          returns None so callers can decide whether to use the result.

The model is trained once in memory (no persistence to disk) and refreshed
on application restart.
"""
import numpy as np
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Minimum consumers with 34-month history before we bother training
MIN_CONSUMERS_FOR_TRAINING = 10
MIN_MONTHS_REQUIRED = 34

# IsolationForest contamination — expected fraction of anomalies in training set
# We use a conservative value since training data may include some theft cases
IF_CONTAMINATION = 0.10


class IsolationForestDetector:
    """
    Anomaly detector trained on DB consumption history.
    Provides an independent anomaly signal on top of the RF models.
    """

    def __init__(self):
        self.model = None
        self.is_trained = False
        self.n_consumers_trained = 0

    def train_from_db(self, db_session) -> bool:
        """
        Query DB for consumers with >= 34 months of history and train.

        Args:
            db_session: SQLAlchemy session

        Returns:
            True if training succeeded, False if insufficient data
        """
        try:
            from app.models.consumption_history import ConsumptionHistory
            from app.models.consumer import Consumer
            from sqlalchemy import func

            logger.info("IsolationForest: querying DB for eligible consumers...")

            # Find consumers with >= 34 months of history
            subquery = (
                db_session.query(
                    ConsumptionHistory.consumer_id,
                    func.count(ConsumptionHistory.id).label("month_count"),
                )
                .group_by(ConsumptionHistory.consumer_id)
                .subquery()
            )

            eligible = (
                db_session.query(subquery.c.consumer_id)
                .filter(subquery.c.month_count >= MIN_MONTHS_REQUIRED)
                .all()
            )

            n_eligible = len(eligible)
            logger.info(
                f"IsolationForest: found {n_eligible} consumers "
                f"with >= {MIN_MONTHS_REQUIRED} months of history"
            )

            if n_eligible < MIN_CONSUMERS_FOR_TRAINING:
                logger.warning(
                    f"IsolationForest: need at least {MIN_CONSUMERS_FOR_TRAINING} "
                    f"eligible consumers, found {n_eligible}. Skipping training."
                )
                return False

            # Build feature matrix — latest 34 months per consumer
            vectors = []
            for (consumer_id,) in eligible:
                records = (
                    db_session.query(ConsumptionHistory.kwh)
                    .filter(ConsumptionHistory.consumer_id == consumer_id)
                    .order_by(ConsumptionHistory.period_start.asc())
                    .all()
                )
                kwh_values = [r.kwh for r in records]
                # Take the LATEST 34 months
                latest_34 = kwh_values[-MIN_MONTHS_REQUIRED:]
                if len(latest_34) == MIN_MONTHS_REQUIRED:
                    vectors.append(latest_34)

            if len(vectors) < MIN_CONSUMERS_FOR_TRAINING:
                logger.warning(
                    "IsolationForest: not enough clean 34-month vectors after filtering."
                )
                return False

            X = np.array(vectors, dtype=float)
            logger.info(
                f"IsolationForest: training on {X.shape[0]} consumers "
                f"with {X.shape[1]}-feature vectors..."
            )

            from sklearn.ensemble import IsolationForest
            self.model = IsolationForest(
                n_estimators=200,
                contamination=IF_CONTAMINATION,
                random_state=42,
                n_jobs=-1,
            )
            self.model.fit(X)
            self.is_trained = True
            self.n_consumers_trained = X.shape[0]

            logger.info(
                f"IsolationForest: trained successfully on "
                f"{self.n_consumers_trained} consumers."
            )
            return True

        except Exception as e:
            logger.error(f"IsolationForest training failed: {e}")
            return False

    def predict(self, monthly_kwh: List[float]) -> Optional[Tuple[float, bool]]:
        """
        Score a single consumer's 34-month history.

        Args:
            monthly_kwh: List of kWh values (any length >= 34)

        Returns:
            (anomaly_score_0_to_1, is_anomaly) or None if model not trained
            Higher score = MORE anomalous
        """
        if not self.is_trained or self.model is None:
            return None

        if len(monthly_kwh) < MIN_MONTHS_REQUIRED:
            return None

        latest_34 = np.array(monthly_kwh[-MIN_MONTHS_REQUIRED:], dtype=float).reshape(1, -1)

        # decision_function returns negative scores for anomalies
        # Convert to [0, 1] where 1 = most anomalous
        raw_score = self.model.decision_function(latest_34)[0]
        label = self.model.predict(latest_34)[0]   # -1 = anomaly, 1 = normal

        # Normalise to [0, 1]: lower decision_function = more anomalous
        # Typical range is roughly [-0.5, 0.5]; we clip and invert
        normalised = float(np.clip((0.5 - raw_score), 0.0, 1.0))
        is_anomaly = label == -1

        return normalised, is_anomaly

    @property
    def status(self) -> dict:
        return {
            "trained": self.is_trained,
            "consumers_used": self.n_consumers_trained,
            "min_months_required": MIN_MONTHS_REQUIRED,
            "contamination": IF_CONTAMINATION,
        }


# Singleton
isolation_detector = IsolationForestDetector()
