"""
Pydantic schemas for forecasting operations, requests, responses, and evaluation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    model_type: str = Field(
        default="auto",
        description="Forecasting algorithm: 'auto' | 'naive' | 'seasonal_naive' | 'random_forest' | 'xgboost'",
    )
    horizon: int = Field(
        default=14,
        ge=1,
        le=365,
        description="Number of future out-of-sample periods to forecast",
    )
    target_level: str = Field(
        default="aggregate",
        description="'aggregate' for total demand or 'product' for single item",
    )
    product_id: Optional[str] = Field(
        default=None,
        description="Specific product/SKU identifier when target_level is 'product'",
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.50,
        le=0.99,
        description="Prediction interval confidence coverage (default 0.95)",
    )
    primary_metric: str = Field(
        default="wape",
        description="Primary metric for model evaluation/selection ('wape', 'mae', 'rmse')",
    )
    use_rolling_origin: bool = Field(
        default=False,
        description="Whether to use rolling-origin backtesting instead of single chronological split",
    )
    backtest_folds: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of backtest folds when use_rolling_origin is True",
    )


class ForecastResponse(BaseModel):
    dataset_id: str
    model_name: str
    model_type: str
    horizon: int
    frequency: str
    forecast: List[Dict[str, Any]]
    feature_importance: Optional[Dict[str, float]] = None
    metrics: Optional[Dict[str, Optional[float]]] = None
    model_comparison: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any]
    warnings: List[str]


class ModelEvaluationRequest(BaseModel):
    horizon: int = Field(
        default=14,
        ge=1,
        le=365,
        description="Forecast horizon used for evaluation window",
    )
    target_level: str = Field(
        default="aggregate",
        description="'aggregate' or 'product'",
    )
    product_id: Optional[str] = Field(
        default=None,
        description="Specific product/SKU identifier when target_level is 'product'",
    )
    primary_metric: str = Field(
        default="wape",
        description="Primary ranking metric: 'wape', 'mae', or 'rmse'",
    )
    use_rolling_origin: bool = Field(
        default=False,
        description="Enable multi-fold rolling-origin backtesting",
    )
    backtest_folds: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of backtesting folds",
    )


class ModelEvaluationResponse(BaseModel):
    dataset_id: str
    target_level: str
    product_id: Optional[str] = None
    primary_metric: str
    evaluation_mode: str
    selected_model_type: str
    selected_model_name: str
    comparison_table: List[Dict[str, Any]]
    validation_period: Dict[str, str]
    validation_metrics: Dict[str, Optional[float]]
    warnings: List[str]
