from dataclasses import asdict
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Header, Response, UploadFile, status
from app.core.errors import NotFoundException, ValidationException
from app.data_processing.data_validator import data_validator
from app.data_processing.loader import _build_json_preview, parse_and_validate_dataset
from app.data_processing.preprocessing import preprocessing_pipeline
from app.data_processing.schema_detector import schema_detector
from app.data_processing.schema_mapper import schema_mapper
from app.data_processing.validator import (
    validate_file_content_signature,
    validate_file_metadata,
)
from app.schemas.dataset import (
    AnalyticsRequest,
    AnalyticsResponse,
    DatasetMappingRequest,
    DatasetMappingResponse,
    DatasetUploadResponse,
    ForecastRequest,
    ForecastResponse,
    ModelEvaluationRequest,
    ModelEvaluationResponse,
)
from app.analytics.insights import business_analytics
from app.services.dataset_registry import dataset_registry
from app.services.forecast_service import forecast_service
from app.services.session_manager import session_manager

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and validate a time-series dataset",
    description=(
        "Uploads a CSV or XLSX dataset, validates file signature, size, row/column counts, "
        "detects candidate column mappings and potential ambiguities, registers raw data "
        "in temporary session storage, and returns metadata with suggested mappings and a limited preview. "
        "Never returns the complete dataset."
    ),
)
async def upload_dataset(
    response: Response,
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> DatasetUploadResponse:
    content = await file.read()

    # Step 1: Validate filename, extension, and file size bounds
    safe_filename, extension = validate_file_metadata(
        filename=file.filename or "uploaded_dataset",
        file_size=len(content),
    )

    # Step 2: Validate magic bytes / file signature (anti-spoofing)
    validate_file_content_signature(content=content, extension=extension)

    # Step 3: Parse tabular structure, enforce row/column constraints, infer dtypes, build preview
    df, dtypes, preview = parse_and_validate_dataset(
        content=content, extension=extension
    )

    # Step 4: Intelligent Schema Detection & Ambiguity Analysis
    detection = schema_detector.detect(df, dtypes)

    # Step 5: Register dataset safely inside isolated session storage
    record = dataset_registry.register_dataset(
        original_filename=safe_filename,
        extension=extension,
        content=content,
        row_count=len(df),
        columns=list(df.columns),
        dtypes=dtypes,
        preview=preview,
        raw_df=df,
        suggested_mapping=detection.suggested_mapping,
        mapping_confidence=detection.confidence,
        ambiguity_warnings=detection.ambiguity_warnings,
        requires_confirmation=detection.requires_confirmation,
        session_id=x_session_id,
    )

    # Attach session token in response header
    if record.session_id:
        response.headers["X-Session-ID"] = record.session_id

    # Step 6: Return metadata, suggested mapping, ambiguity warnings, and limited preview only
    return DatasetUploadResponse(
        dataset_id=record.dataset_id,
        filename=record.original_filename,
        file_type=record.file_type,
        file_size_bytes=record.file_size_bytes,
        row_count=record.row_count,
        column_count=record.column_count,
        columns=record.columns,
        dtypes=record.dtypes,
        preview=record.preview,
        preview_rows_count=len(record.preview),
        suggested_mapping=record.suggested_mapping,
        mapping_confidence=record.mapping_confidence,
        ambiguity_warnings=record.ambiguity_warnings,
        requires_confirmation=record.requires_confirmation,
        created_at=record.created_at.isoformat(),
        expires_at=record.expires_at.isoformat(),
        session_id=record.session_id,
    )



@router.post(
    "/{dataset_id}/mapping",
    response_model=DatasetMappingResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm or update canonical schema mapping",
    description=(
        "Applies user-confirmed or adjusted column mappings to canonical roles (date, demand, product_id, "
        "store_id, price, promotion). Runs data quality diagnostics (duplicates, negative values, nulls, "
        "and time-interval frequency), creates a normalized analysis dataset while preserving raw data, "
        "and returns quality health metrics with normalized preview."
    ),
)
async def update_dataset_mapping(
    dataset_id: str,
    request: DatasetMappingRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> DatasetMappingResponse:
    if x_session_id:
        session_manager.verify_dataset_ownership(x_session_id, dataset_id)

    record = dataset_registry.get(dataset_id)
    if not record:
        raise NotFoundException(
            message=f"Dataset session '{dataset_id}' not found or has expired.",
            code="DATASET_NOT_FOUND",
        )

    # Retrieve raw source DataFrame
    raw_df = dataset_registry.get_raw_dataframe(dataset_id)

    # Form mapping dictionary
    submitted_mapping: Dict[str, Any] = {
        "date": request.date_column,
        "demand": request.demand_column,
        "product_id": request.product_id_column,
        "store_id": request.store_id_column,
        "price": request.price_column,
        "promotion": request.promotion_column,
    }

    # Step 1: Validate and apply mapping
    mapped_df, active_canonical_mapping = schema_mapper.apply_mapping(
        raw_df, submitted_mapping
    )

    # Step 2: Execute thorough data quality validation (date parseability, gaps, duplicates, negatives)
    quality_report = data_validator.validate(raw_df, submitted_mapping)

    # Step 3: Determine effective frequency
    freq = (
        request.aggregation_frequency
        if request.aggregation_frequency and request.aggregation_frequency != "auto"
        else quality_report.detected_frequency
    )

    # Step 4: Normalize data into canonical representations for analysis
    normalized_df, summary = preprocessing_pipeline.normalize(
        mapped_df=mapped_df,
        inferred_freq=freq,
    )

    # Step 5: Update session registry with normalized state and diagnostics
    quality_dict = asdict(quality_report)
    summary_dict = asdict(summary)

    dataset_registry.update_mapping(
        dataset_id=dataset_id,
        active_mapping=active_canonical_mapping,
        normalized_df=normalized_df,
        data_quality=quality_dict,
        normalization_summary=summary_dict,
    )

    # Step 6: Generate safe limited preview from normalized representation
    normalized_preview = _build_json_preview(normalized_df.head(5))

    return DatasetMappingResponse(
        dataset_id=dataset_id,
        is_valid=quality_report.is_valid,
        mapped_schema=active_canonical_mapping,
        data_quality=quality_dict,
        summary=summary_dict,
        normalized_preview=normalized_preview,
    )


@router.get(
    "/{dataset_id}/mapping",
    summary="Get current or suggested mapping for a dataset",
    description="Fetches suggested or active schema mappings along with quality metrics if mapped.",
)
async def get_dataset_mapping(
    dataset_id: str,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> Dict[str, Any]:
    if x_session_id:
        session_manager.verify_dataset_ownership(x_session_id, dataset_id)

    record = dataset_registry.get(dataset_id)
    if not record:
        raise NotFoundException(
            message=f"Dataset session '{dataset_id}' not found or has expired.",
            code="DATASET_NOT_FOUND",
        )

    return {
        "dataset_id": record.dataset_id,
        "is_mapped": record.active_mapping is not None,
        "active_mapping": record.active_mapping,
        "suggested_mapping": record.suggested_mapping,
        "mapping_confidence": record.mapping_confidence,
        "ambiguity_warnings": record.ambiguity_warnings,
        "requires_confirmation": record.requires_confirmation,
        "data_quality": record.data_quality,
        "summary": record.normalization_summary,
    }


@router.get(
    "/{dataset_id}",
    response_model=DatasetUploadResponse,
    summary="Get metadata and preview for a registered dataset",
    description="Fetches metadata and limited preview for an active, unexpired dataset session.",
)
async def get_dataset_metadata(
    dataset_id: str,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> DatasetUploadResponse:
    if x_session_id:
        session_manager.verify_dataset_ownership(x_session_id, dataset_id)

    record = dataset_registry.get(dataset_id)
    if not record:
        raise NotFoundException(
            message=f"Dataset session '{dataset_id}' not found or has expired.",
            code="DATASET_NOT_FOUND",
        )

    return DatasetUploadResponse(
        dataset_id=record.dataset_id,
        filename=record.original_filename,
        file_type=record.file_type,
        file_size_bytes=record.file_size_bytes,
        row_count=record.row_count,
        column_count=record.column_count,
        columns=record.columns,
        dtypes=record.dtypes,
        preview=record.preview,
        preview_rows_count=len(record.preview),
        suggested_mapping=record.suggested_mapping,
        mapping_confidence=record.mapping_confidence,
        ambiguity_warnings=record.ambiguity_warnings,
        requires_confirmation=record.requires_confirmation,
        created_at=record.created_at.isoformat(),
        expires_at=record.expires_at.isoformat(),
        session_id=record.session_id,
    )


@router.post(
    "/{dataset_id}/forecast",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate time-series demand forecast",
    description=(
        "Executes forecasting model ('auto', 'naive', 'seasonal_naive', 'random_forest', 'xgboost') "
        "across the designated future horizon with uncertainty bounds. "
        "When model_type is 'auto', runs chronological validation and model selection before generating forecast."
    ),
)
async def generate_dataset_forecast(
    dataset_id: str,
    request: ForecastRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> ForecastResponse:
    if x_session_id:
        session_manager.verify_dataset_ownership(x_session_id, dataset_id)

    result = forecast_service.generate_forecast(
        dataset_id=dataset_id,
        model_type=request.model_type,
        horizon=request.horizon,
        target_level=request.target_level,
        product_id=request.product_id,
        confidence_level=request.confidence_level,
        primary_metric=request.primary_metric,
        use_rolling_origin=request.use_rolling_origin,
        backtest_folds=request.backtest_folds,
    )

    res_dict = result.to_dict()
    return ForecastResponse(
        dataset_id=dataset_id,
        model_name=res_dict["model_name"],
        model_type=res_dict["model_type"],
        horizon=res_dict["horizon"],
        frequency=res_dict["frequency"],
        forecast=res_dict["forecast"],
        feature_importance=res_dict["feature_importance"],
        metrics=res_dict.get("metrics"),
        model_comparison=res_dict.get("model_comparison"),
        metadata=res_dict["metadata"],
        warnings=res_dict["warnings"],
    )


@router.post(
    "/{dataset_id}/evaluate",
    response_model=ModelEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate and compare candidate forecasting models",
    description=(
        "Executes chronological validation / rolling-origin backtesting comparing "
        "Naive, Seasonal Naive, Random Forest, and XGBoost on identical validation windows. "
        "Returns comparison table with MAE, RMSE, WAPE, and eligibility status without generating future projections."
    ),
)
async def evaluate_dataset_models(
    dataset_id: str,
    request: ModelEvaluationRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> ModelEvaluationResponse:
    if x_session_id:
        session_manager.verify_dataset_ownership(x_session_id, dataset_id)

    selection_res = forecast_service.evaluate_dataset(
        dataset_id=dataset_id,
        horizon=request.horizon,
        target_level=request.target_level,
        product_id=request.product_id,
        primary_metric=request.primary_metric,
        use_rolling_origin=request.use_rolling_origin,
        backtest_folds=request.backtest_folds,
    )

    return ModelEvaluationResponse(
        dataset_id=dataset_id,
        target_level=request.target_level,
        product_id=request.product_id,
        primary_metric=request.primary_metric,
        evaluation_mode=selection_res.evaluation_mode,
        selected_model_type=selection_res.selected_model_type,
        selected_model_name=selection_res.selected_model_name,
        comparison_table=[rec.to_dict() for rec in selection_res.comparison_table],
        validation_period=selection_res.validation_period,
        validation_metrics=selection_res.validation_metrics,
        warnings=selection_res.warnings,
    )


@router.post(
    "/{dataset_id}/analytics",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute grounded sales trends, rankings, seasonality, and inventory planning estimates",
    description=(
        "Calculates validated empirical metrics: trajectory slopes, Pareto product rankings, "
        "day-of-week seasonality multipliers, empirical correlations, and safety stock / reorder point estimates. "
        "Inventory planning metrics require lead-time parameters and are strictly labeled as estimates."
    ),
)
async def generate_dataset_analytics(
    dataset_id: str,
    request: AnalyticsRequest = AnalyticsRequest(),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> AnalyticsResponse:
    if x_session_id:
        session_manager.verify_dataset_ownership(x_session_id, dataset_id)

    record = dataset_registry.get(dataset_id)
    if not record:
        raise NotFoundException(
            message=f"Dataset session '{dataset_id}' not found or expired.",
            code="DATASET_NOT_FOUND",
        )
    if record.normalized_df is None:
        raise ValidationException(
            message=f"Dataset '{dataset_id}' must be mapped before generating business analytics.",
            code="UNMAPPED_DATASET",
        )

    df = record.normalized_df.copy()
    if request.product_id:
        if "product_id" in df.columns:
            df = df[df["product_id"] == request.product_id].copy()

    insights = business_analytics.generate_full_insights(
        df=df,
        lead_time_days=request.lead_time_days,
        service_level=request.service_level,
        current_inventory=request.current_inventory,
    )

    return AnalyticsResponse(
        dataset_id=dataset_id,
        product_id=request.product_id,
        trend=insights["trend"],
        product_rankings=insights["product_rankings"],
        seasonality=insights["seasonality"],
        inventory_insights=insights["inventory_insights"],
        correlations=insights["correlations"],
    )




