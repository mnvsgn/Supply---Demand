"""
Administrator API routes for Dashboard, Model Performance,
System Information, and operational forecast verification.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.admin.auth import (
    authenticate_admin,
    bearer_scheme,
    get_current_admin,
    revoke_admin_token,
)
from app.admin.repository import admin_repo
from app.admin.service import admin_service
from app.schemas.admin import (
    ActivityItem,
    AdminLoginRequest,
    AdminLoginResponse,
    DashboardResponse,
    ForecastVerifyRequest,
    ModelPerformanceResponse,
    SystemInfoResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post(
    "/login",
    response_model=AdminLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate administrator and issue session token",
)
async def admin_login(payload: AdminLoginRequest) -> AdminLoginResponse:
    """Verifies administrator username and password from environment variables."""
    token = authenticate_admin(payload.username, payload.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials. Please check username and password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AdminLoginResponse(
        token=token,
        username=payload.username,
        token_type="Bearer",
        expires_in_hours=8,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke active administrator session token",
)
async def admin_logout(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    _admin: Dict[str, str] = Depends(get_current_admin),
) -> Dict[str, str]:
    """Revokes the current admin token."""
    token = auth.credentials if auth else x_admin_token
    if token:
        revoke_admin_token(token)
    return {"message": "Administrator session logged out successfully."}


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve admin dashboard overview metrics and activity stream",
)
async def get_dashboard(
    _admin: Dict[str, str] = Depends(get_current_admin),
) -> DashboardResponse:
    """Returns total runs, processed datasets, algorithm states, and recent activity."""
    data = admin_service.get_dashboard_summary()
    return DashboardResponse(**data)


@router.get(
    "/performance",
    response_model=ModelPerformanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve training/testing performance, operational metrics, and model comparisons",
)
async def get_model_performance(
    _admin: Dict[str, str] = Depends(get_current_admin),
) -> ModelPerformanceResponse:
    """
    Returns 3 structured performance sections:
    A. Training & Testing Performance
    B. Operational Forecast Performance
    C. Model Comparison
    """
    data = admin_service.get_performance_summary()
    return ModelPerformanceResponse(**data)


@router.get(
    "/system-info",
    response_model=SystemInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve system telemetry, Python/ML library versions, and configuration",
)
async def get_system_information(
    _admin: Dict[str, str] = Depends(get_current_admin),
) -> SystemInfoResponse:
    """Returns actual runtime library versions, supported algorithms, and session configurations."""
    data = admin_service.get_system_info()
    return SystemInfoResponse(**data)


@router.get(
    "/activity",
    response_model=List[ActivityItem],
    status_code=status.HTTP_200_OK,
    summary="Retrieve recent activity audit log",
)
async def get_activity_log(
    limit: int = 50,
    _admin: Dict[str, str] = Depends(get_current_admin),
) -> List[ActivityItem]:
    """Returns chronological audit log of training, evaluations, uploads, and forecasts."""
    activities = admin_repo.get_activities(limit=min(limit, 100))
    return [ActivityItem(**a) for a in activities]


@router.post(
    "/forecasts/{event_id}/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify previously generated forecast against actual observations",
)
async def verify_forecast_predictions(
    event_id: str,
    payload: ForecastVerifyRequest,
    _admin: Dict[str, str] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    Calculates operational MAE, RMSE, and WAPE when ground-truth actual observations
    become available, avoiding treating unverified predictions as verified accuracy.
    """
    res = admin_service.verify_forecast_operational(
        event_id=event_id,
        actual_observations=payload.actual_observations,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast event '{event_id}' not found or no matching observation dates exist.",
        )
    return {"event_id": event_id, "verification_metrics": res}
