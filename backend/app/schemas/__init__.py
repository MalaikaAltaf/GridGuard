"""
Schemas package - exports all Pydantic schemas for easy import
"""
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo
from app.schemas.consumer import (
    ConsumerBase,
    RiskQueueItem,
    RiskQueueResponse,
    ConsumptionDataPoint,
    ExplanationResponse,
    ConsumptionHistoryResponse,
)
from app.schemas.user import UserBase, InspectorListItem
from app.schemas.case import (
    CaseCreate,
    CaseBase,
    CaseListItem,
    CaseDetail,
    CaseResponse,
    CaseListResponse,
)
from app.schemas.inspection import (
    InspectionCreate,
    InspectionResponse,
    InspectionDetail,
)
from app.schemas.audit_log import AuditLogEntry, AuditLogResponse
from app.schemas.analytics import PerformanceTrendPoint, ModelPerformanceResponse

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "UserInfo",
    "ConsumerBase",
    "RiskQueueItem",
    "RiskQueueResponse",
    "ConsumptionDataPoint",
    "ExplanationResponse",
    "ConsumptionHistoryResponse",
    "UserBase",
    "InspectorListItem",
    "CaseCreate",
    "CaseBase",
    "CaseListItem",
    "CaseDetail",
    "CaseResponse",
    "CaseListResponse",
    "InspectionCreate",
    "InspectionResponse",
    "InspectionDetail",
    "AuditLogEntry",
    "AuditLogResponse",
    "PerformanceTrendPoint",
    "ModelPerformanceResponse",
]
