"""
Evaluation and model-selection layer for the forecasting engine.
Compares candidate models on strictly identical chronological validation windows,
ranks models based on empirical validation performance, and refits the selected model
on full historical observations before future forecasting.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Type
import numpy as np
import pandas as pd

from app.evaluation.metrics import calculate_evaluation_metrics
from app.evaluation.splitter import (
    BacktestFold,
    ChronologicalSplit,
    RollingOriginBacktester,
    chronological_split,
)
from app.forecasting.base import BaseForecaster
from app.forecasting.naive import NaiveForecaster, SeasonalNaiveForecaster
from app.forecasting.random_forest import RandomForestForecaster
from app.forecasting.xgboost_model import XGBoostForecaster


# Candidate model factories for comparison
CANDIDATE_MODEL_FACTORIES: Dict[str, Tuple[str, Type[BaseForecaster], int]] = {
    # model_key: (display_name, model_class, min_required_train_obs)
    "naive": ("Naive (Last Observation)", NaiveForecaster, 1),
    "seasonal_naive": ("Seasonal Naive", SeasonalNaiveForecaster, 2),
    "random_forest": ("Random Forest Regressor", RandomForestForecaster, 10),
    "xgboost": ("XGBoost Regressor", XGBoostForecaster, 10),
}


@dataclass
class ModelEvaluationRecord:
    """Evaluation metrics and eligibility status for a single candidate model."""
    model_name: str
    model_type: str
    is_eligible: bool
    eligibility_reason: Optional[str] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    wape: Optional[float] = None
    validation_start: Optional[str] = None
    validation_end: Optional[str] = None
    is_selected: bool = False
    rank: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModelSelectionResult:
    """Output container for the model selection workflow."""
    selected_model_type: str
    selected_model_name: str
    comparison_table: List[ModelEvaluationRecord]
    validation_metrics: Dict[str, Optional[float]]
    refitted_model: BaseForecaster
    validation_period: Dict[str, str]
    evaluation_mode: str
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_model_type": self.selected_model_type,
            "selected_model_name": self.selected_model_name,
            "comparison_table": [rec.to_dict() for rec in self.comparison_table],
            "validation_metrics": self.validation_metrics,
            "validation_period": self.validation_period,
            "evaluation_mode": self.evaluation_mode,
            "warnings": self.warnings,
        }


class ModelSelector:
    """
    Orchestrates candidate model evaluation and automated selection:
    1. Partitions data chronologically into train and validation sets (or rolling folds).
    2. Tests candidate eligibility based on historical data depth.
    3. Evaluates all eligible candidates on the identical validation targets.
    4. Ranks models strictly using validation metrics (never test set).
    5. Selects the highest-performing model.
    6. Refits the selected model on the entire permitted historical dataset.
    """

    def __init__(
        self,
        primary_metric: str = "wape",
        use_rolling_origin: bool = False,
        backtest_folds: int = 3,
        random_state: int = 42,
    ):
        norm_metric = primary_metric.lower().strip()
        if norm_metric not in ("wape", "mae", "rmse"):
            raise ValueError(f"Unsupported primary evaluation metric '{primary_metric}'. Choose 'wape', 'mae', or 'rmse'.")

        self.primary_metric = norm_metric
        self.use_rolling_origin = use_rolling_origin
        self.backtest_folds = backtest_folds
        self.random_state = random_state

    def select_best_model(
        self,
        df: pd.DataFrame,
        horizon: int = 14,
        frequency: str = "D",
        test_size: Optional[int] = None,
    ) -> ModelSelectionResult:
        """
        Executes model comparison and returns the refitted winning forecaster.
        """
        if df.empty or len(df) < 3:
            raise ValueError("Dataset has insufficient rows for time-series evaluation (minimum 3 required).")

        warnings: List[str] = []
        n_obs = len(df)

        # Warning for short historical records
        if n_obs < 20:
            warnings.append(
                f"Historical observations ({n_obs}) are below recommended minimum (20) for reliable model comparison. "
                "Validation sample is small; performance ranking may exhibit high variance."
            )

        # Execute evaluation either via rolling backtest or single chronological split
        if self.use_rolling_origin and n_obs >= (10 + horizon * 2):
            records, val_start, val_end = self._evaluate_rolling_origin(
                df=df,
                horizon=horizon,
                frequency=frequency,
                warnings=warnings,
            )
            eval_mode = "rolling_origin_backtest"
        else:
            if self.use_rolling_origin:
                warnings.append(
                    f"Dataset length ({n_obs}) is insufficient for {self.backtest_folds}-fold rolling-origin backtest. "
                    "Fell back to single chronological train/validation split."
                )
            records, val_start, val_end = self._evaluate_single_split(
                df=df,
                horizon=horizon,
                frequency=frequency,
                test_size=test_size,
                warnings=warnings,
            )
            eval_mode = "chronological_holdout"

        # Rank eligible models based on validation performance
        ranked_records, winning_model_type = self._rank_and_select(records)

        # Retrieve winning display name
        display_name, model_class, _ = CANDIDATE_MODEL_FACTORIES[winning_model_type]

        # Refit winning model on permitted full historical dataset (Requirement 8)
        # Ensure random_state reproducibility
        if winning_model_type in ("random_forest", "xgboost"):
            refitted_model = model_class(random_state=self.random_state)
        else:
            refitted_model = model_class()

        refitted_model.fit(df, frequency=frequency)

        # Extract winning model validation metrics
        winning_record = next(r for r in ranked_records if r.model_type == winning_model_type)
        val_metrics = {
            "mae": winning_record.mae,
            "rmse": winning_record.rmse,
            "wape": winning_record.wape,
        }

        return ModelSelectionResult(
            selected_model_type=winning_model_type,
            selected_model_name=display_name,
            comparison_table=ranked_records,
            validation_metrics=val_metrics,
            refitted_model=refitted_model,
            validation_period={"start": val_start, "end": val_end},
            evaluation_mode=eval_mode,
            warnings=warnings,
        )

    def _evaluate_single_split(
        self,
        df: pd.DataFrame,
        horizon: int,
        frequency: str,
        test_size: Optional[int],
        warnings: List[str],
    ) -> Tuple[List[ModelEvaluationRecord], str, str]:
        """Evaluates all candidate models on a single chronological validation window."""
        # Adjust validation size to horizon if feasible, otherwise scale down
        n_obs = len(df)
        val_size = min(horizon, max(1, n_obs // 4))

        split: ChronologicalSplit = chronological_split(
            df=df,
            val_size=val_size,
            test_size=test_size or 0,
        )

        train_df = split.train
        val_df = split.val
        val_demands = val_df["demand"].to_numpy(dtype=float)
        val_h = len(val_df)
        n_train = len(train_df)

        val_start = split.val_start
        val_end = split.val_end

        records: List[ModelEvaluationRecord] = []

        for model_key, (display_name, model_class, min_obs) in CANDIDATE_MODEL_FACTORIES.items():
            # 1. Eligibility Check
            if n_train < min_obs:
                records.append(
                    ModelEvaluationRecord(
                        model_name=display_name,
                        model_type=model_key,
                        is_eligible=False,
                        eligibility_reason=(
                            f"Requires at least {min_obs} training observations for feature engineering "
                            f"(only {n_train} available in training partition)."
                        ),
                        validation_start=val_start,
                        validation_end=val_end,
                    )
                )
                continue

            # 2. Instantiate and Fit strictly on training partition
            try:
                if model_key in ("random_forest", "xgboost"):
                    forecaster = model_class(random_state=self.random_state)
                else:
                    forecaster = model_class()

                forecaster.fit(train_df, frequency=frequency)
                forecast_res = forecaster.predict(horizon=val_h)

                # 3. Calculate metrics on validation window
                preds = forecast_res.forecast_series["predicted_demand"].to_numpy()
                metrics = calculate_evaluation_metrics(val_demands, preds)

                records.append(
                    ModelEvaluationRecord(
                        model_name=display_name,
                        model_type=model_key,
                        is_eligible=True,
                        eligibility_reason=None,
                        mae=metrics["mae"],
                        rmse=metrics["rmse"],
                        wape=metrics["wape"],
                        validation_start=val_start,
                        validation_end=val_end,
                    )
                )
            except Exception as e:
                records.append(
                    ModelEvaluationRecord(
                        model_name=display_name,
                        model_type=model_key,
                        is_eligible=False,
                        eligibility_reason=f"Model evaluation failed during training: {str(e)}",
                        validation_start=val_start,
                        validation_end=val_end,
                    )
                )

        return records, val_start, val_end

    def _evaluate_rolling_origin(
        self,
        df: pd.DataFrame,
        horizon: int,
        frequency: str,
        warnings: List[str],
    ) -> Tuple[List[ModelEvaluationRecord], str, str]:
        """Evaluates candidate models across multiple expanding rolling-origin folds."""
        backtester = RollingOriginBacktester(
            horizon=horizon,
            n_folds=self.backtest_folds,
            min_train_size=10,
        )
        folds = backtester.generate_folds(df)

        overall_val_start = folds[0].val_start
        overall_val_end = folds[-1].val_end

        records: List[ModelEvaluationRecord] = []

        for model_key, (display_name, model_class, min_obs) in CANDIDATE_MODEL_FACTORIES.items():
            fold_maes: List[float] = []
            fold_rmses: List[float] = []
            fold_wapes: List[float] = []
            is_model_eligible = True
            ineligibility_msg: Optional[str] = None

            for fold in folds:
                train_len = len(fold.train_df)
                if train_len < min_obs:
                    is_model_eligible = False
                    ineligibility_msg = f"Insufficient history in fold {fold.fold_index} (requires {min_obs}, got {train_len})."
                    break

                try:
                    if model_key in ("random_forest", "xgboost"):
                        forecaster = model_class(random_state=self.random_state)
                    else:
                        forecaster = model_class()

                    forecaster.fit(fold.train_df, frequency=frequency)
                    forecast_res = forecaster.predict(horizon=len(fold.val_df))

                    val_demands = fold.val_df["demand"].to_numpy(dtype=float)
                    preds = forecast_res.forecast_series["predicted_demand"].to_numpy()
                    metrics = calculate_evaluation_metrics(val_demands, preds)

                    fold_maes.append(metrics["mae"])
                    fold_rmses.append(metrics["rmse"])
                    if metrics["wape"] is not None:
                        fold_wapes.append(metrics["wape"])
                except Exception as e:
                    is_model_eligible = False
                    ineligibility_msg = f"Error in fold {fold.fold_index}: {str(e)}"
                    break

            if not is_model_eligible:
                records.append(
                    ModelEvaluationRecord(
                        model_name=display_name,
                        model_type=model_key,
                        is_eligible=False,
                        eligibility_reason=ineligibility_msg,
                        validation_start=overall_val_start,
                        validation_end=overall_val_end,
                    )
                )
            else:
                avg_mae = round(float(np.mean(fold_maes)), 4) if fold_maes else None
                avg_rmse = round(float(np.mean(fold_rmses)), 4) if fold_rmses else None
                avg_wape = round(float(np.mean(fold_wapes)), 4) if fold_wapes else None

                records.append(
                    ModelEvaluationRecord(
                        model_name=display_name,
                        model_type=model_key,
                        is_eligible=True,
                        eligibility_reason=None,
                        mae=avg_mae,
                        rmse=avg_rmse,
                        wape=avg_wape,
                        validation_start=overall_val_start,
                        validation_end=overall_val_end,
                    )
                )

        return records, overall_val_start, overall_val_end

    def _rank_and_select(
        self, records: List[ModelEvaluationRecord]
    ) -> Tuple[List[ModelEvaluationRecord], str]:
        """
        Ranks eligible models strictly on validation metrics.
        Never touches test sets.
        Selects model with lowest validation error.
        """
        eligible = [r for r in records if r.is_eligible]

        if not eligible:
            # Fallback to simple naive if no model was eligible
            naive_rec = next((r for r in records if r.model_type == "naive"), None)
            if naive_rec:
                naive_rec.is_eligible = True
                naive_rec.is_selected = True
                naive_rec.rank = 1
                return records, "naive"
            raise RuntimeError("No candidate models are eligible and fallback failed.")

        def sort_key(rec: ModelEvaluationRecord) -> Tuple[float, float]:
            # Primary metric sorting
            val: Optional[float]
            if self.primary_metric == "wape":
                val = rec.wape if rec.wape is not None else rec.mae
            elif self.primary_metric == "mae":
                val = rec.mae
            else:
                val = rec.rmse

            primary_val = val if (val is not None and not np.isnan(val)) else float("inf")
            tie_breaker = rec.rmse if (rec.rmse is not None and not np.isnan(rec.rmse)) else float("inf")
            return (primary_val, tie_breaker)

        # Sort eligible models ascending by error
        sorted_eligible = sorted(eligible, key=sort_key)

        # Assign ranks
        for rank_idx, rec in enumerate(sorted_eligible):
            rec.rank = rank_idx + 1

        # Winning model is rank 1
        winner = sorted_eligible[0]
        winner.is_selected = True

        return records, winner.model_type
