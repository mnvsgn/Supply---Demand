"""
Forecasts API routes for model training, projection, and comparative backtesting.
"""

from typing import Optional
from fastapi import APIRouter, Header, Query, Response, status
from app.core.errors import NotFoundException
from app.schemas.dataset import (
    ForecastRequest,
    ForecastResponse,
    ModelEvaluationRequest,
    ModelEvaluationResponse,
)
from app.services.dataset_registry import dataset_registry
from app.services.forecast_service import forecast_service

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.post(
    "",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate multi-step demand forecast for a registered dataset",
)
async def generate_forecast_standalone(
    payload: ForecastRequest,
    response: Response,
    dataset_id: str = Query(..., description="Target dataset identifier"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> ForecastResponse:
    record = dataset_registry.get_dataset(dataset_id, session_id=x_session_id)
    if not record:
        raise NotFoundException(f"Dataset '{dataset_id}' not found or session has expired.")

    result = forecast_service.generate_forecast(
        dataset_id=dataset_id,
        model_type=payload.model_type,
        horizon=payload.horizon,
        target_level=payload.target_level,
        product_id=payload.product_id,
        confidence_level=payload.confidence_level,
        primary_metric=payload.primary_metric,
        use_rolling_origin=payload.use_rolling_origin,
        backtest_folds=payload.backtest_folds,
    )

    if record.session_id:
        response.headers["X-Session-ID"] = record.session_id

    res_dict = result.to_dict()
    return ForecastResponse(
        dataset_id=dataset_id,
        model_name=res_dict["model_name"],
        model_type=res_dict["model_type"],
        horizon=res_dict["horizon"],
        frequency=res_dict["frequency"],
        forecast=res_dict["forecast"],
        feature_importance=res_dict.get("feature_importance"),
        metrics=res_dict.get("metrics"),
        model_comparison=res_dict.get("model_comparison"),
        metadata=res_dict.get("metadata", {}),
        warnings=res_dict.get("warnings", []),
    )


@router.post(
    "/evaluate",
    response_model=ModelEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run comparative backtesting across forecasting algorithms",
)
async def evaluate_models_standalone(
    payload: ModelEvaluationRequest,
    response: Response,
    dataset_id: str = Query(..., description="Target dataset identifier"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> ModelEvaluationResponse:
    record = dataset_registry.get_dataset(dataset_id, session_id=x_session_id)
    if not record:
        raise NotFoundException(f"Dataset '{dataset_id}' not found or session has expired.")

    result = forecast_service.evaluate_dataset(
        dataset_id=dataset_id,
        horizon=payload.horizon,
        target_level=payload.target_level,
        product_id=payload.product_id,
        primary_metric=payload.primary_metric,
        use_rolling_origin=payload.use_rolling_origin,
        backtest_folds=payload.backtest_folds,
    )

    if record.session_id:
        response.headers["X-Session-ID"] = record.session_id

    res_dict = result.to_dict()
    return ModelEvaluationResponse(
        dataset_id=dataset_id,
        target_level=payload.target_level,
        product_id=payload.product_id,
        primary_metric=payload.primary_metric,
        evaluation_mode=res_dict.get("evaluation_mode", "chronological_split"),
        selected_model_type=res_dict["selected_model_type"],
        selected_model_name=res_dict["selected_model_name"],
        comparison_table=res_dict["comparison_table"],
        validation_period=res_dict["validation_period"],
        validation_metrics=res_dict["validation_metrics"],
        warnings=res_dict.get("warnings", []),
    )
