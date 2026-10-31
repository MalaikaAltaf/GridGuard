"""
Models package - exports all ORM models for easy import
"""
from app.models.user import User, UserRole
from app.models.consumer import Consumer, MeterType
from app.models.risk_score import RiskScore, RiskBand
from app.models.case import Case, CaseStatus
from app.models.inspection import Inspection, InspectionOutcome
from app.models.consumption_history import ConsumptionHistory
from app.models.audit_log import AuditLog

__all__ = [
    "User",
    "UserRole",
    "Consumer",
    "MeterType",
    "RiskScore",
    "RiskBand",
    "Case",
    "CaseStatus",
    "Inspection",
    "InspectionOutcome",
    "ConsumptionHistory",
    "AuditLog",
]
