"""
Pydantic schemas for admin dashboard, performance telemetry,
system telemetry, authentication, and forecast verification.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Administrator username")
    password: str = Field(..., min_length=1, description="Administrator password")


class AdminLoginResponse(BaseModel):
    token: str = Field(..., description="High-entropy admin session token")
    username: str
    token_type: str = "Bearer"
    expires_in_hours: int = 8


class ModelStatusItem(BaseModel):
    key: str
    name: str
    status: str
    last_evaluated: Optional[str] = None
    best_wape: Optional[float] = None
    best_mae: Optional[float] = None
    best_rmse: Optional[float] = None


class ActivityItem(BaseModel):
    activity_id: str
    type: str
    title: str
    description: str
    timestamp: str
    status: str
    metadata: Optional[Dict[str, Any]] = None


class DashboardResponse(BaseModel):
    total_training_runs: int
    total_evaluated_models: int
    total_forecasts_generated: int
    user_datasets_processed: int
    timestamps: Dict[str, Optional[str]]
    model_statuses: List[ModelStatusItem]
    recent_activity: List[ActivityItem]


class CandidateModelPerformance(BaseModel):
    key: str
    name: str
    status: str
    last_evaluated: Optional[str] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    wape: Optional[float] = None


class TrainingTestingPerformance(BaseModel):
    training_runs_count: int
    evaluated_series_count: int
    best_performing_model: str
    last_evaluation_time: Optional[str] = None
    candidate_models: List[CandidateModelPerformance]
    has_evaluations: bool


class OperationalForecastPerformance(BaseModel):
    datasets_processed: int
    forecasts_generated: int
    forecasts_evaluated: int
    mae: Optional[float] = None
    rmse: Optional[float] = None
    wape: Optional[float] = None
    last_forecast_timestamp: Optional[str] = None
    has_operational_evaluations: bool


class ModelComparisonRow(BaseModel):
    model_name: str
    wape_pct: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    status: str


class ModelComparisonSection(BaseModel):
    has_data: bool
    comparison_table: List[ModelComparisonRow]


class ModelPerformanceResponse(BaseModel):
    training_and_testing: TrainingTestingPerformance
    operational_forecasts: OperationalForecastPerformance
    model_comparison: ModelComparisonSection


class SystemInfoResponse(BaseModel):
    application: Dict[str, Any]
    environment_info: Dict[str, Any]
    library_versions: Dict[str, str]
    supported_capabilities: Dict[str, Any]
    session_configuration: Dict[str, Any]
    activity_timestamps: Dict[str, Optional[str]]
    system_time_utc: str


class ForecastVerifyRequest(BaseModel):
    actual_observations: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="Actual historical observations with date and demand to verify against predicted values",
    )
