from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class DatasetUploadResponse(BaseModel):
    dataset_id: str = Field(..., description="Unique randomized dataset identifier")
    filename: str = Field(..., description="Sanitized original file name")
    file_type: str = Field(..., description="File format ('csv' or 'xlsx')")
    file_size_bytes: int = Field(..., description="Uploaded file size in bytes")
    row_count: int = Field(..., description="Total number of data rows in the dataset")
    column_count: int = Field(..., description="Total number of columns in the dataset")
    columns: List[str] = Field(..., description="List of detected column headers")
    dtypes: Dict[str, str] = Field(
        ...,
        description="Inferred data types for each column (e.g., 'datetime', 'numeric', 'categorical', 'text')",
    )
    preview: List[Dict[str, Any]] = Field(
        ...,
        description="Limited preview sample containing the first few rows (never the full dataset)",
    )
    preview_rows_count: int = Field(
        ..., description="Number of rows included in the preview"
    )
    suggested_mapping: Optional[Dict[str, Optional[str]]] = Field(
        default=None,
        description="Auto-detected column mappings to canonical roles (date, demand, product_id, etc.)",
    )
    mapping_confidence: Optional[Dict[str, str]] = Field(
        default=None,
        description="Confidence scores ('high' | 'medium' | 'low') for each canonical suggestion",
    )
    ambiguity_warnings: List[str] = Field(
        default_factory=list,
        description="Warnings regarding ambiguous columns (e.g., revenue vs units, multiple dates)",
    )
    requires_confirmation: bool = Field(
        default=False,
        description="True if user confirmation or manual disambiguation is recommended before forecasting",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when dataset was registered",
    )
    expires_at: str = Field(
        ..., description="Timestamp when temporary dataset session expires"
    )
    session_id: Optional[str] = Field(
        default=None, description="Associated temporary session identifier"
    )


class DatasetMappingRequest(BaseModel):
    date_column: str = Field(..., description="Raw column name representing chronological timestamps")
    demand_column: str = Field(..., description="Raw column name representing target demand or sales volume")
    product_id_column: Optional[str] = Field(
        default=None, description="Optional raw column name identifying products or SKUs"
    )
    store_id_column: Optional[str] = Field(
        default=None, description="Optional raw column name identifying stores or locations"
    )
    price_column: Optional[str] = Field(
        default=None, description="Optional raw column name representing unit selling price"
    )
    promotion_column: Optional[str] = Field(
        default=None, description="Optional raw column name representing marketing promotions or events"
    )
    aggregation_frequency: Optional[str] = Field(
        default=None, description="Optional manual frequency override ('D', 'W', 'M', or 'auto')"
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_aliases_and_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Resolve canonical role aliases (e.g., date -> date_column, demand -> demand_column)
            if not data.get("date_column") and data.get("date"):
                data["date_column"] = data["date"]
            if not data.get("demand_column") and data.get("demand"):
                data["demand_column"] = data["demand"]
            if not data.get("product_id_column") and data.get("product_id"):
                data["product_id_column"] = data["product_id"]
            if not data.get("store_id_column") and data.get("store_id"):
                data["store_id_column"] = data["store_id"]
            if not data.get("price_column") and data.get("price"):
                data["price_column"] = data["price"]
            if not data.get("promotion_column") and data.get("promotion"):
                data["promotion_column"] = data["promotion"]
        return data


class DatasetMappingResponse(BaseModel):
    dataset_id: str = Field(..., description="Unique dataset identifier")
    is_valid: bool = Field(..., description="Whether mapped dataset meets quality criteria for forecasting")
    mapped_schema: Dict[str, Optional[str]] = Field(
        ..., description="Confirmed mappings between canonical roles and source column names"
    )
    data_quality: Dict[str, Any] = Field(
        ..., description="Quality diagnostics including date range, missing values, duplicates, and frequency"
    )
    summary: Dict[str, Any] = Field(
        ..., description="Normalized time-series metrics, volume summaries, and forecasting capabilities"
    )
    normalized_preview: List[Dict[str, Any]] = Field(
        ..., description="First 5 normalized records adhering to canonical schema"
    )


class ForecastRequest(BaseModel):
    model_type: str = Field(
        default="auto",
        description="Algorithm choice: 'auto', 'naive', 'seasonal_naive', 'random_forest', or 'xgboost'",
    )
    horizon: int = Field(
        default=14,
        ge=1,
        le=365,
        description="Number of future time periods to forecast",
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


class AnalyticsRequest(BaseModel):
    lead_time_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Supplier lead time in days for safety stock and ROP calculations",
    )
    service_level: float = Field(
        default=0.95,
        ge=0.50,
        le=0.999,
        description="Cycle service level target (e.g. 0.95 for 95%)",
    )
    current_inventory: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Optional current on-hand inventory level",
    )
    product_id: Optional[str] = Field(
        default=None,
        description="Optional product SKU filter for single-product analytics",
    )


class AnalyticsResponse(BaseModel):
    dataset_id: str
    product_id: Optional[str] = None
    trend: Dict[str, Any]
    product_rankings: Optional[List[Dict[str, Any]]] = None
    seasonality: Dict[str, Any]
    inventory_insights: Optional[Dict[str, Any]] = None
    correlations: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)


