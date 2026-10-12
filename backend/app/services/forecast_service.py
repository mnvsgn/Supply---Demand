from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from app.core.errors import NotFoundException, ValidationException
from app.core.logging import logger
from app.data_processing.preprocessing import preprocessing_pipeline
from app.forecasting.base import (
    BaseForecaster,
    ForecastExecutionResult,
    ForecastPoint,
    ForecastResult,
)
from app.forecasting.naive import NaiveForecaster, SeasonalNaiveForecaster
from app.forecasting.random_forest import RandomForestForecaster
from app.forecasting.xgboost_model import XGBoostForecaster
from app.evaluation.model_selector import ModelSelectionResult, ModelSelector
from app.services.dataset_registry import dataset_registry

# Supported forecasting model types
SUPPORTED_MODELS = {
    "auto": None,  # Automated comparison and selection
    "naive": NaiveForecaster,
    "seasonal_naive": SeasonalNaiveForecaster,
    "random_forest": RandomForestForecaster,
    "xgboost": XGBoostForecaster,
}


class ForecastService:
    """
    Coordinates end-to-end forecasting workflows:
    - Validates target series and forecast horizons.
    - Aligns time series to regular temporal grids handling missing dates explicitly.
    - Fits selected forecasters and generates structured multi-step projections.
    - Supports automated model evaluation and selection with zero test leakage.
    """

    def generate_forecast(
        self,
        dataset_id: Optional[str] = None,
        normalized_df: Optional[pd.DataFrame] = None,
        model_type: str = "auto",
        horizon: int = 14,
        target_level: str = "aggregate",
        product_id: Optional[str] = None,
        frequency: Optional[str] = None,
        confidence_level: float = 0.95,
        primary_metric: str = "wape",
        use_rolling_origin: bool = False,
        backtest_folds: int = 3,
    ) -> ForecastResult:
        # 1. Validate Horizon Bounds
        if horizon < 1:
            raise ValidationException(
                message=f"Forecast horizon must be a positive integer >= 1 (got {horizon}).",
                code="INVALID_HORIZON",
            )
        if horizon > 365:
            raise ValidationException(
                message=f"Forecast horizon ({horizon}) exceeds the maximum allowed limit of 365 periods.",
                code="HORIZON_TOO_LARGE",
            )

        # 2. Validate Model Type
        model_key = model_type.lower().strip()
        if model_key not in SUPPORTED_MODELS:
            raise ValidationException(
                message=f"Unsupported model type '{model_type}'. Supported models: {list(SUPPORTED_MODELS.keys())}.",
                code="UNSUPPORTED_MODEL",
            )

        # 3. Retrieve Normalized Data
        df: pd.DataFrame
        inferred_freq: str = frequency or "D"

        if normalized_df is not None:
            df = normalized_df.copy()
        elif dataset_id is not None:
            record = dataset_registry.get(dataset_id)
            if not record:
                raise NotFoundException(
                    message=f"Dataset session '{dataset_id}' not found or expired.",
                    code="DATASET_NOT_FOUND",
                )
            if record.normalized_df is None:
                raise ValidationException(
                    message=f"Dataset '{dataset_id}' has not been mapped yet. Please confirm schema mapping first.",
                    code="UNMAPPED_DATASET",
                )
            df = record.normalized_df.copy()
            if not frequency and record.data_quality:
                inferred_freq = record.data_quality.get("detected_frequency", "D")
        else:
            raise ValidationException(
                message="Either dataset_id or normalized_df must be provided to run forecasting.",
                code="MISSING_DATASET_INPUT",
            )

        # 4. Extract Target Series (Aggregate or Product-Specific)
        target_series = self._extract_target_series(
            df=df,
            target_level=target_level,
            product_id=product_id,
        )

        # 5. Clean, Sort, and Align to Continuous Regular Temporal Grid
        effective_freq = self._normalize_frequency_alias(inferred_freq)
        aligned_series = self._align_to_regular_grid(target_series, effective_freq)
        n_obs = len(aligned_series)

        # Record training start telemetry
        run_id = None
        try:
            from app.admin.service import admin_service
            run_id = admin_service.record_training_started(
                model_type=model_key,
                dataset_id=dataset_id,
                horizon=horizon,
                parameters={"target_level": target_level, "confidence_level": confidence_level},
            )
        except Exception:
            pass

        # 6. Branch: Automated Model Selection vs Specific Explicit Model
        if model_key == "auto":
            selector = ModelSelector(
                primary_metric=primary_metric,
                use_rolling_origin=use_rolling_origin,
                backtest_folds=backtest_folds,
            )
            selection_res = selector.select_best_model(
                df=aligned_series,
                horizon=horizon,
                frequency=effective_freq,
            )

            # Refitted winning forecaster generates the out-of-sample projection
            winning_forecaster = selection_res.refitted_model
            result = winning_forecaster.predict(horizon=horizon, confidence_level=confidence_level)

            # Attach comparison and validation metrics
            result.metrics = selection_res.validation_metrics
            result.model_comparison = [rec.to_dict() for rec in selection_res.comparison_table]
            result.warnings = list(dict.fromkeys(result.warnings + selection_res.warnings))
            result.metadata.update({
                "auto_selected": True,
                "selection_metric": primary_metric,
                "evaluation_mode": selection_res.evaluation_mode,
                "validation_period": selection_res.validation_period,
            })
            # Attach recent historical points (up to 45 points) for frontend charts
            result.metadata["recent_history"] = [
                {
                    "date": r["date"].strftime("%Y-%m-%d") if isinstance(r["date"], pd.Timestamp) else str(r["date"]),
                    "demand": round(float(r["demand"]), 2),
                }
                for _, r in aligned_series.tail(45).iterrows()
            ]

            # Update admin telemetry for automated run
            try:
                from app.admin.service import admin_service
                if run_id:
                    admin_service.record_training_completed(
                        run_id=run_id,
                        model_type=result.model_type,
                        metrics=result.metrics,
                    )
                admin_service.record_evaluation_completed(
                    dataset_id=dataset_id,
                    horizon=horizon,
                    primary_metric=primary_metric,
                    candidate_models=[rec.model_name for rec in selection_res.comparison_table],
                    comparison_table=[rec.to_dict() for rec in selection_res.comparison_table],
                    winning_model=selection_res.selected_model_name,
                    metrics=selection_res.validation_metrics,
                )
                forecast_dict = result.to_dict()
                forecast_points = forecast_dict.get("forecast", [])
                admin_service.record_forecast_generated(
                    dataset_id=dataset_id,
                    model_name=result.model_name,
                    horizon=horizon,
                    target_level=target_level,
                    product_id=product_id,
                    points_count=len(forecast_points),
                    forecast_points=forecast_points,
                )
            except Exception as ex:
                logger.warning(f"Admin telemetry recording failed: {ex}")

            return result

        # Check Historical Length Thresholds for specific model
        min_required = 10 if model_key in ("random_forest", "xgboost") else (5 if model_key == "seasonal_naive" else 3)
        if n_obs < min_required:
            raise ValidationException(
                message=(
                    f"Insufficient historical data points ({n_obs}) to train '{model_type}'. "
                    f"A minimum of {min_required} consecutive observations is required."
                ),
                code="INSUFFICIENT_HISTORY",
                detail={"observations_found": n_obs, "minimum_required": min_required},
            )

        # Instantiate and Fit Explicit Model
        model_class = SUPPORTED_MODELS[model_key]
        forecaster: BaseForecaster = model_class()

        try:
            forecaster.fit(aligned_series, frequency=effective_freq)
            result = forecaster.predict(horizon=horizon, confidence_level=confidence_level)
            result.metadata["recent_history"] = [
                {
                    "date": r["date"].strftime("%Y-%m-%d") if isinstance(r["date"], pd.Timestamp) else str(r["date"]),
                    "demand": round(float(r["demand"]), 2),
                }
                for _, r in aligned_series.tail(45).iterrows()
            ]

            # Update admin telemetry for explicit model run
            try:
                from app.admin.service import admin_service
                if run_id:
                    admin_service.record_training_completed(
                        run_id=run_id,
                        model_type=result.model_type,
                        metrics=result.metrics,
                    )
                forecast_dict = result.to_dict()
                forecast_points = forecast_dict.get("forecast", [])
                admin_service.record_forecast_generated(
                    dataset_id=dataset_id,
                    model_name=result.model_name,
                    horizon=horizon,
                    target_level=target_level,
                    product_id=product_id,
                    points_count=len(forecast_points),
                    forecast_points=forecast_points,
                )
            except Exception as ex:
                logger.warning(f"Admin telemetry recording failed: {ex}")

            return result
        except Exception as e:
            try:
                from app.admin.service import admin_service
                if run_id:
                    admin_service.record_training_failed(run_id=run_id, error=str(e))
            except Exception:
                pass
            raise ValidationException(
                message=f"Failed to fit model {model_type}: {str(e)}",
                code="FORECAST_TRAINING_FAILED",
            )

    def evaluate_dataset(
        self,
        dataset_id: Optional[str] = None,
        normalized_df: Optional[pd.DataFrame] = None,
        horizon: int = 14,
        target_level: str = "aggregate",
        product_id: Optional[str] = None,
        frequency: Optional[str] = None,
        primary_metric: str = "wape",
        use_rolling_origin: bool = False,
        backtest_folds: int = 3,
    ) -> ModelSelectionResult:
        """
        Runs model evaluation and returns the candidate comparison table and diagnostics.
        """
        # Validate Horizon Bounds
        if horizon < 1:
            raise ValidationException(
                message=f"Forecast horizon must be a positive integer >= 1 (got {horizon}).",
                code="INVALID_HORIZON",
            )

        # Retrieve Normalized Data
        df: pd.DataFrame
        inferred_freq: str = frequency or "D"

        if normalized_df is not None:
            df = normalized_df.copy()
        elif dataset_id is not None:
            record = dataset_registry.get(dataset_id)
            if not record:
                raise NotFoundException(
                    message=f"Dataset session '{dataset_id}' not found or expired.",
                    code="DATASET_NOT_FOUND",
                )
            if record.normalized_df is None:
                raise ValidationException(
                    message=f"Dataset '{dataset_id}' has not been mapped yet. Please confirm schema mapping first.",
                    code="UNMAPPED_DATASET",
                )
            df = record.normalized_df.copy()
            if not frequency and record.data_quality:
                inferred_freq = record.data_quality.get("detected_frequency", "D")
        else:
            raise ValidationException(
                message="Either dataset_id or normalized_df must be provided to run evaluation.",
                code="MISSING_DATASET_INPUT",
            )

        # Extract and Align Target Series
        target_series = self._extract_target_series(
            df=df,
            target_level=target_level,
            product_id=product_id,
        )
        effective_freq = self._normalize_frequency_alias(inferred_freq)
        aligned_series = self._align_to_regular_grid(target_series, effective_freq)

        # Execute Model Selector
        selector = ModelSelector(
            primary_metric=primary_metric,
            use_rolling_origin=use_rolling_origin,
            backtest_folds=backtest_folds,
        )

        res = selector.select_best_model(
            df=aligned_series,
            horizon=horizon,
            frequency=effective_freq,
        )

        try:
            from app.admin.service import admin_service
            admin_service.record_evaluation_completed(
                dataset_id=dataset_id,
                horizon=horizon,
                primary_metric=primary_metric,
                candidate_models=[rec.model_name for rec in res.comparison_table],
                comparison_table=[rec.to_dict() for rec in res.comparison_table],
                winning_model=res.selected_model_name,
                metrics=res.validation_metrics,
            )
        except Exception:
            pass

        return res


    def _extract_target_series(
        self,
        df: pd.DataFrame,
        target_level: str,
        product_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Extracts appropriate demand time-series based on user level."""
        if target_level == "product":
            if not product_id:
                raise ValidationException(
                    message="Parameter 'product_id' is required when target_level is set to 'product'.",
                    code="MISSING_PRODUCT_ID",
                )
            try:
                return preprocessing_pipeline.get_product_demand_series(df, product_id)
            except ValueError as ve:
                raise ValidationException(
                    message=str(ve),
                    code="PRODUCT_SERIES_ERROR",
                )
        else:
            # Aggregate total demand
            return preprocessing_pipeline.get_aggregate_demand_series(df)

    def _normalize_frequency_alias(self, freq: str) -> str:
        """Standardizes frequency strings to pandas date_range compatible aliases."""
        f = freq.strip()
        if f.startswith("W"):
            return "W"
        elif f.startswith("M"):
            return "M"
        elif f.startswith("Q"):
            return "Q"
        elif f.startswith("Y"):
            return "Y"
        elif f.startswith("h"):
            return "h"
        return "D"

    def _align_to_regular_grid(self, df: pd.DataFrame, freq: str) -> pd.DataFrame:
        """
        Ensures strict chronological sorting and fills missing unrecorded dates
        explicitly with 0 demand (never fabricating synthetic numbers).
        """
        data = df.copy()
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values(by="date").drop_duplicates(subset=["date"]).reset_index(drop=True)

        if len(data) < 2:
            return data

        start_date = data["date"].min()
        end_date = data["date"].max()

        try:
            full_index = pd.date_range(start=start_date, end=end_date, freq=freq)
            aligned = data.set_index("date").reindex(full_index)
            # Missing dates in demand series represent zero sales periods
            aligned["demand"] = aligned["demand"].fillna(0.0)
            aligned = aligned.reset_index().rename(columns={"index": "date"})
            return aligned
        except Exception:
            # In case of irregular intervals, preserve original data sorted
            data["demand"] = data["demand"].fillna(0.0)
            return data

    # Convenience aliases for interface compatibility
    forecast = generate_forecast
    evaluate_models = evaluate_dataset



# Global singleton
forecast_service = ForecastService()
