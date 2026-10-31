"""
Shared pytest fixtures for Grid-Guard AI backend tests.

Uses the real Supabase test database (via session pooler).
All seeded rows are cleaned up after each test session.
"""
import sys
import os
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.consumer import Consumer, MeterType
from app.models.risk_score import RiskScore, RiskBand
from app.models.case import Case, CaseStatus
from app.models.inspection import Inspection, InspectionOutcome
from app.models.audit_log import AuditLog
from app.models.consumption_history import ConsumptionHistory
from app.auth.password import hash_password


# ── HTTP client ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient – reused for the whole session."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Database session ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def db():
    """Raw SQLAlchemy session used to set up / tear down seed data."""
    session = SessionLocal()
    yield session
    session.close()


# ── Unique tag to avoid clashing with seed data ───────────────────────────────

TEST_TAG = f"TEST_{uuid4().hex[:8]}"


# ── Users ─────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def officer_user(db: Session):
    user = User(
        name=f"Test Officer {TEST_TAG}",
        email=f"officer_{TEST_TAG}@example.com",
        password_hash=hash_password("testpass123"),
        role=UserRole.OFFICER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture(scope="session")
def inspector_user(db: Session):
    user = User(
        name=f"Test Inspector {TEST_TAG}",
        email=f"inspector_{TEST_TAG}@example.com",
        password_hash=hash_password("testpass123"),
        role=UserRole.INSPECTOR,
        last_seen_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture(scope="session")
def manager_user(db: Session):
    user = User(
        name=f"Test Manager {TEST_TAG}",
        email=f"manager_{TEST_TAG}@example.com",
        password_hash=hash_password("testpass123"),
        role=UserRole.CIRCLE_MANAGER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


# ── Auth helpers ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def officer_token(client, officer_user):
    """JWT for the test officer."""
    resp = client.post("/auth/login", json={
        "email": officer_user.email,
        "password": "testpass123",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


@pytest.fixture(scope="session")
def inspector_token(client, inspector_user):
    """JWT for the test inspector."""
    resp = client.post("/auth/login", json={
        "email": inspector_user.email,
        "password": "testpass123",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


@pytest.fixture(scope="session")
def manager_token(client, manager_user):
    """JWT for the test circle manager."""
    resp = client.post("/auth/login", json={
        "email": manager_user.email,
        "password": "testpass123",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


# ── Consumer + RiskScore ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_consumer(db: Session):
    consumer = Consumer(
        external_ref=f"MTR-{TEST_TAG}",
        address=f"1 Test Street {TEST_TAG}",
        feeder="F-TEST",
        tariff_class="Domestic",
        meter_type=MeterType.SINGLE_PHASE,
        latitude=31.5204,
        longitude=74.3587,
        is_demo_data=True,
    )
    db.add(consumer)
    db.commit()
    db.refresh(consumer)
    yield consumer
    db.delete(consumer)
    db.commit()


@pytest.fixture(scope="session")
def test_risk_score(db: Session, test_consumer):
    score = RiskScore(
        consumer_id=test_consumer.id,
        score=0.85,
        risk_band=RiskBand.HIGH,
        explanation_text_en="High risk: significant consumption drop detected.",
        explanation_text_ur="زیادہ خطرہ: کھپت میں نمایاں کمی۔",
        explanation_raw={"consumption_drop_pct": 65, "zero_billing_months": 2},
        scored_at=datetime.utcnow(),
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    yield score
    db.delete(score)
    db.commit()


@pytest.fixture(scope="session")
def test_consumption_history(db: Session, test_consumer):
    records = [
        ConsumptionHistory(
            consumer_id=test_consumer.id,
            period_start=(datetime.utcnow() - timedelta(days=30 * i)).replace(day=1).date(),
            kwh=round(300 * (0.3 if i < 3 else 1.0), 2),
        )
        for i in range(12)
    ]
    db.add_all(records)
    db.commit()
    yield records
    for r in records:
        db.delete(r)
    db.commit()


# ── Case ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_case(db: Session, test_consumer, test_risk_score, officer_user, inspector_user):
    case = Case(
        consumer_id=test_consumer.id,
        risk_score_id=test_risk_score.id,
        assigned_by=officer_user.id,
        assigned_to=inspector_user.id,
        status=CaseStatus.ASSIGNED,
        assignment_note="Test case for automated testing",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    yield case
    # Delete linked inspections + audit logs first
    db.query(Inspection).filter(Inspection.case_id == case.id).delete()
    db.query(AuditLog).filter(AuditLog.entity_id == case.id).delete()
    db.delete(case)
    db.commit()


# ── Auth header helpers ───────────────────────────────────────────────────────

def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
