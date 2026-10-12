"""
Unit and integration tests for the evaluation and model-selection layer.
Verifies metric calculations (MAE, RMSE, WAPE), safe zero-demand handling,
chronological splitting, zero-leakage rolling-origin backtesting,
and reproducible model selection.
"""

import io
import math
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.evaluation.metrics import (
    calculate_evaluation_metrics,
    calculate_mae,
    calculate_rmse,
    calculate_wape,
)
from app.evaluation.model_selector import ModelSelector
from app.evaluation.splitter import (
    RollingOriginBacktester,
    chronological_split,
)
from app.main import app
from app.services.forecast_service import forecast_service


# ---------------------------------------------------------------------------
# Metric Calculation Tests
# ---------------------------------------------------------------------------

def test_mae_rmse_wape_standard_calculations():
    """Verify standard formula calculations for MAE, RMSE, and WAPE."""
    y_true = [10.0, 20.0, 30.0, 40.0]
    y_pred = [12.0, 18.0, 33.0, 35.0]
    # Errors: |2|, |-2|, |3|, |-5| -> abs errors = [2, 2, 3, 5]
    # Sum abs errors = 12, mean abs error = 3.0
    # Squared errors = [4, 4, 9, 25] -> sum = 42, mean = 10.5, sqrt = 3.24037
    # Sum actuals = 100.0 -> WAPE = (12 / 100) * 100 = 12.0%

    mae = calculate_mae(y_true, y_pred)
    rmse = calculate_rmse(y_true, y_pred)
    wape = calculate_wape(y_true, y_pred)

    assert pytest.approx(mae, rel=1e-4) == 3.0
    assert pytest.approx(rmse, rel=1e-4) == math.sqrt(10.5)
    assert pytest.approx(wape, rel=1e-4) == 12.0


def test_metrics_safe_zero_demand_handling():
    """Verify safe handling of zero-demand actual observations without ZeroDivisionError."""
    # 1. Partial zero demand in series (common for retail slow-movers)
    y_true = [0.0, 10.0, 0.0, 20.0]
    y_pred = [2.0, 8.0, 1.0, 19.0]
    # Abs errors: [2, 2, 1, 1] -> sum = 6.0
    # Sum actuals = 30.0 -> WAPE = (6 / 30) * 100 = 20.0%
    wape = calculate_wape(y_true, y_pred)
    assert pytest.approx(wape, rel=1e-4) == 20.0

    # 2. All actual demands are zero, predictions are also zero (exact match on dormant series)
    all_zero_true = [0.0, 0.0, 0.0]
    all_zero_pred = [0.0, 0.0, 0.0]
    wape_zero = calculate_wape(all_zero_true, all_zero_pred)
    assert wape_zero == 0.0

    # 3. All actual demands are zero, predictions are non-zero (division by zero safely returns None)
    non_zero_pred = [1.0, 2.0, 0.0]
    wape_undefined = calculate_wape(all_zero_true, non_zero_pred)
    assert wape_undefined is None

    # Unified metric dictionary handles None gracefully
    metrics_dict = calculate_evaluation_metrics(all_zero_true, non_zero_pred)
    assert metrics_dict["wape"] is None
    assert metrics_dict["mae"] == 1.0


def test_metrics_invalid_inputs_rejected():
    """Verify that empty, mismatched, or NaN inputs are cleanly rejected."""
    with pytest.raises(ValueError, match="empty"):
        calculate_mae([], [])

    with pytest.raises(ValueError, match="Length mismatch"):
        calculate_rmse([1.0, 2.0], [1.0])

    with pytest.raises(ValueError, match="NaN"):
        calculate_wape([1.0, np.nan], [1.0, 2.0])


# ---------------------------------------------------------------------------
# Chronological Splitting & Leakage Prevention Tests
# ---------------------------------------------------------------------------

def test_chronological_split_strict_ordering():
    """Verify chronological split never shuffles and ensures train < val < test."""
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    df = pd.DataFrame({"date": dates, "demand": np.arange(30) + 10.0})

    split = chronological_split(df, val_size=7, test_size=5)

    assert len(split.train) == 18
    assert len(split.val) == 7
    assert len(split.test) == 5

    # Strict temporal sequencing: train ends before val begins, val ends before test begins
    assert pd.to_datetime(split.train["date"]).max() < pd.to_datetime(split.val["date"]).min()
    assert pd.to_datetime(split.val["date"]).max() < pd.to_datetime(split.test["date"]).min()

    # Dates match exact boundaries
    assert split.val_start == "2023-01-19"
    assert split.val_end == "2023-01-25"
    assert split.test_start == "2023-01-26"


def test_chronological_split_insufficient_history_rejection():
    """Verify that requesting splits larger than dataset length raises ValueError."""
    dates = pd.date_range("2023-01-01", periods=5, freq="D")
    df = pd.DataFrame({"date": dates, "demand": [1.0, 2.0, 3.0, 4.0, 5.0]})

    with pytest.raises(ValueError, match="leave 0 rows for training"):
        chronological_split(df, val_size=3, test_size=2)


def test_rolling_origin_backtesting_expanding_window():
    """Verify that RollingOriginBacktester produces advancing folds without future leakage."""
    dates = pd.date_range("2023-01-01", periods=40, freq="D")
    df = pd.DataFrame({"date": dates, "demand": np.arange(40) + 5.0})

    backtester = RollingOriginBacktester(horizon=7, n_folds=3, min_train_size=10)
    folds = backtester.generate_folds(df)

    assert len(folds) == 3

    # Fold 1 < Fold 2 < Fold 3 training set size (expanding window)
    assert len(folds[0].train_df) < len(folds[1].train_df) < len(folds[2].train_df)

    # In every fold, train end is strictly before validation start
    for f in folds:
        assert len(f.val_df) == 7
        assert pd.to_datetime(f.train_df["date"]).max() < pd.to_datetime(f.val_df["date"]).min()


# ---------------------------------------------------------------------------
# Model Selection Tests (Neither XGBoost nor RF always assumed to win)
# ---------------------------------------------------------------------------

def test_model_selection_naive_wins_on_flat_series():
    """
    On a perfectly constant series, Naive baseline predicts the exact constant with 0 error,
    proving that complex ML models are not hardcoded or assumed to always win.
    """
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    # Perfectly flat constant series
    df = pd.DataFrame({"date": dates, "demand": np.full(30, 50.0)})

    selector = ModelSelector(primary_metric="wape", random_state=42)
    result = selector.select_best_model(df=df, horizon=7)

    # Comparison table must contain all 4 models
    assert len(result.comparison_table) == 4
    model_types = [r.model_type for r in result.comparison_table]
    assert set(model_types) == {"naive", "seasonal_naive", "random_forest", "xgboost"}

    # Naive achieved perfect 0 error
    naive_rec = next(r for r in result.comparison_table if r.model_type == "naive")
    assert naive_rec.wape == 0.0
    assert naive_rec.mae == 0.0

    # Winning model must have rank 1 and is_selected=True
    assert result.selected_model_type in ("naive", "seasonal_naive")
    winner_rec = next(r for r in result.comparison_table if r.is_selected)
    assert winner_rec.rank == 1


def test_model_selection_seasonal_naive_wins_on_cyclical_pattern():
    """
    On a noiseless repeating weekly cycle, Seasonal Naive predicts the exact repeating cycle,
    outperforming simple naive and tree models that struggle with precise periodicity.
    """
    # 8 weeks of repeating weekly cycle: [10, 20, 15, 30, 50, 80, 25] repeated 8 times = 56 days
    weekly_pattern = [10.0, 20.0, 15.0, 30.0, 50.0, 80.0, 25.0]
    repeated = np.tile(weekly_pattern, 8)
    dates = pd.date_range("2023-01-01", periods=len(repeated), freq="D")
    df = pd.DataFrame({"date": dates, "demand": repeated})

    selector = ModelSelector(primary_metric="wape", random_state=42)
    result = selector.select_best_model(df=df, horizon=7)

    seasonal_rec = next(r for r in result.comparison_table if r.model_type == "seasonal_naive")
    naive_rec = next(r for r in result.comparison_table if r.model_type == "naive")

    # Seasonal naive should achieve essentially 0% error on clean repeating cycle
    assert seasonal_rec.wape == pytest.approx(0.0, abs=1e-3)
    # Simple naive projects a flat line of last day (25.0), suffering significant error
    assert naive_rec.wape > 20.0

    # Seasonal Naive must beat simple Naive
    assert seasonal_rec.rank < naive_rec.rank
    assert result.selected_model_type == "seasonal_naive"


def test_model_selection_ineligible_models_on_short_data():
    """
    When historical data is too short for ML feature engineering (< 10 train rows),
    Random Forest and XGBoost must be marked is_eligible=False with explicit reasons,
    and a baseline must be selected.
    """
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    # Total 10 rows: val_size=2 leaves 8 rows for training (< 10 required for RF/XGBoost)
    df = pd.DataFrame({"date": dates, "demand": np.arange(10) + 5.0})

    selector = ModelSelector(primary_metric="wape", random_state=42)
    result = selector.select_best_model(df=df, horizon=2)

    rf_rec = next(r for r in result.comparison_table if r.model_type == "random_forest")
    xgb_rec = next(r for r in result.comparison_table if r.model_type == "xgboost")

    assert rf_rec.is_eligible is False
    assert "Requires at least 10 training observations" in rf_rec.eligibility_reason
    assert xgb_rec.is_eligible is False
    assert rf_rec.is_selected is False
    assert xgb_rec.is_selected is False

    # Only eligible model can win
    assert result.selected_model_type in ("naive", "seasonal_naive")

    # Warning regarding short data emitted
    assert any("below recommended minimum" in w for w in result.warnings)


def test_model_selection_never_uses_test_set():
    """
    Verify that providing a test set does NOT influence model selection.
    Model selection is determined strictly on the validation partition.
    """
    dates = pd.date_range("2023-01-01", periods=50, freq="D")
    df = pd.DataFrame({"date": dates, "demand": np.arange(50) + 10.0})

    selector = ModelSelector(primary_metric="wape", random_state=42)

    # Run with test_size=5
    result_with_test = selector.select_best_model(df=df, horizon=7, test_size=5)

    # Run with test_size=0 on matching train+val slice
    matching_df = df.iloc[:45].copy().reset_index(drop=True)
    result_without_test = selector.select_best_model(df=matching_df, horizon=7, test_size=0)

    # Winning model and validation metrics must match exactly
    assert result_with_test.selected_model_type == result_without_test.selected_model_type
    assert result_with_test.validation_period == result_without_test.validation_period


def test_model_selection_refitting_step():
    """
    Verify Requirement 8: After model selection, the winning model is refit on the
    full historical series up to the most recent date before making future predictions.
    """
    dates = pd.date_range("2023-01-01", periods=40, freq="D")
    df = pd.DataFrame({"date": dates, "demand": np.arange(40) + 10.0})

    selector = ModelSelector(primary_metric="wape", random_state=42)
    result = selector.select_best_model(df=df, horizon=7)

    refitted_forecaster = result.refitted_model
    assert refitted_forecaster.is_fitted is True
    # Last fitted date must equal the latest date in the full dataset, NOT the training split cutoff!
    assert refitted_forecaster.last_date == dates.max()

    # Generating forecast produces future dates starting the day AFTER the dataset max date
    future_forecast = refitted_forecaster.predict(horizon=5)
    first_future_date = pd.Timestamp(future_forecast.forecast_series["date"].iloc[0])
    expected_start = pd.Timestamp(dates.max()) + pd.Timedelta(days=1)
    assert first_future_date == expected_start


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------

def test_api_auto_model_selection_forecast_endpoint():
    """Verify POST /api/v1/datasets/{dataset_id}/forecast with model_type='auto'."""
    client = TestClient(app)

    # 1. Upload sample dataset
    dates = pd.date_range("2023-01-01", periods=45, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "demand": [50.0 + 10.0 * np.sin(i / 3.0) for i in range(45)],
    })
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("auto_test.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    # 2. Confirm schema mapping
    map_res = client.post(
        f"/api/v1/datasets/{dataset_id}/mapping",
        json={"date_column": "date", "demand_column": "demand"},
    )
    assert map_res.status_code == 200

    # 3. Generate forecast with model_type='auto'
    forecast_res = client.post(
        f"/api/v1/datasets/{dataset_id}/forecast",
        json={
            "model_type": "auto",
            "horizon": 7,
            "target_level": "aggregate",
            "primary_metric": "wape",
        },
    )
    assert forecast_res.status_code == 200
    data = forecast_res.json()

    assert data["dataset_id"] == dataset_id
    assert data["model_type"] in ("naive", "seasonal_naive", "random_forest", "xgboost")
    assert len(data["forecast"]) == 7

    # Verification: comparison table and validation metrics are attached
    assert data["metrics"] is not None
    assert "mae" in data["metrics"]
    assert "rmse" in data["metrics"]
    assert "wape" in data["metrics"]

    assert data["model_comparison"] is not None
    assert len(data["model_comparison"]) == 4
    assert any(m["is_selected"] is True for m in data["model_comparison"])


def test_api_standalone_evaluate_endpoint():
    """Verify POST /api/v1/datasets/{dataset_id}/evaluate returns comparison table without forecasting."""
    client = TestClient(app)

    dates = pd.date_range("2023-01-01", periods=40, freq="D")
    df = pd.DataFrame({"date": dates, "demand": np.arange(40) + 15.0})
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("eval_test.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    client.post(
        f"/api/v1/datasets/{dataset_id}/mapping",
        json={"date_column": "date", "demand_column": "demand"},
    )

    eval_res = client.post(
        f"/api/v1/datasets/{dataset_id}/evaluate",
        json={
            "horizon": 7,
            "target_level": "aggregate",
            "primary_metric": "wape",
            "use_rolling_origin": False,
        },
    )
    assert eval_res.status_code == 200
    data = eval_res.json()

    assert data["dataset_id"] == dataset_id
    assert data["selected_model_type"] in ("naive", "seasonal_naive", "random_forest", "xgboost")
    assert len(data["comparison_table"]) == 4
    for record in data["comparison_table"]:
        assert "model_name" in record
        assert "is_eligible" in record
        assert "is_selected" in record
        assert "validation_start" in record
        assert "validation_end" in record
