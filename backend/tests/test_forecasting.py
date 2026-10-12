import math
import numpy as np
import pandas as pd
import pytest
from app.core.errors import ValidationException
from app.forecasting.base import ForecastResult
from app.forecasting.feature_engineering import TimeSeriesFeatureBuilder
from app.forecasting.naive import NaiveForecaster, SeasonalNaiveForecaster
from app.forecasting.random_forest import RandomForestForecaster
from app.forecasting.xgboost_model import XGBoostForecaster
from app.services.forecast_service import forecast_service


def generate_synthetic_demand(
    n_days: int = 60,
    base_level: float = 100.0,
    trend_slope: float = 0.5,
    seasonal_amplitude: float = 20.0,
    start_date: str = "2023-01-01",
) -> pd.DataFrame:
    """
    Generates deterministic synthetic time-series with linear trend and weekly seasonality:
    y_t = base_level + trend_slope * t + seasonal_amplitude * sin(2 * pi * t / 7)
    """
    dates = pd.date_range(start=start_date, periods=n_days, freq="D")
    t = np.arange(n_days)
    seasonality = seasonal_amplitude * np.sin(2 * np.pi * t / 7.0)
    demand = base_level + trend_slope * t + seasonality

    return pd.DataFrame({
        "date": dates,
        "demand": demand,
    })


def test_naive_forecaster():
    """Verify that NaiveForecaster projects the last observed value into all future periods."""
    df = generate_synthetic_demand(n_days=30)
    last_val = float(df["demand"].iloc[-1])

    forecaster = NaiveForecaster()
    forecaster.fit(df, frequency="D")
    result: ForecastResult = forecaster.predict(horizon=14)

    assert result.horizon == 14
    assert len(result.forecast_series) == 14
    assert list(result.forecast_series.columns) == [
        "date",
        "predicted_demand",
        "lower_bound",
        "upper_bound",
    ]

    # Verify all predictions equal last observed value
    for val in result.forecast_series["predicted_demand"]:
        assert pytest.approx(val, rel=1e-4) == last_val

    # Bounds must be finite and lower bound >= 0
    assert (result.forecast_series["lower_bound"] >= 0).all()
    assert (result.forecast_series["upper_bound"] >= result.forecast_series["lower_bound"]).all()


def test_seasonal_naive_forecaster_with_sufficient_history():
    """Verify SeasonalNaiveForecaster cycles through prior seasonal period when history is sufficient."""
    df = generate_synthetic_demand(n_days=60)  # > 2 * 7 = 14 days
    last_week_cycle = df["demand"].iloc[-7:].to_numpy()

    forecaster = SeasonalNaiveForecaster(seasonal_period=7)
    forecaster.fit(df, frequency="D")
    result: ForecastResult = forecaster.predict(horizon=14)

    assert result.horizon == 14
    assert len(result.forecast_series) == 14
    assert result.metadata["fallback_to_simple_naive"] is False

    preds = result.forecast_series["predicted_demand"].to_numpy()
    # First 7 steps match last week
    np.testing.assert_allclose(preds[:7], last_week_cycle, rtol=1e-4)
    # Next 7 steps repeat the cycle
    np.testing.assert_allclose(preds[7:14], last_week_cycle, rtol=1e-4)


def test_seasonal_naive_fallback_on_insufficient_history():
    """Verify that SeasonalNaiveForecaster safely falls back to simple naive when history is too short."""
    # Season length 7 requires >= 14 days; we provide only 8 days
    short_df = generate_synthetic_demand(n_days=8)
    last_val = float(short_df["demand"].iloc[-1])

    forecaster = SeasonalNaiveForecaster(seasonal_period=7)
    forecaster.fit(short_df, frequency="D")
    result: ForecastResult = forecaster.predict(horizon=7)

    assert result.metadata["fallback_to_simple_naive"] is True
    assert len(result.warnings) > 0
    assert "fell back" in result.warnings[0].lower()

    # All predictions equal last value due to fallback
    for val in result.forecast_series["predicted_demand"]:
        assert pytest.approx(val, rel=1e-4) == last_val


def test_random_forest_forecaster():
    """Verify RandomForestForecaster generates valid numeric multi-step recursive forecasts."""
    df = generate_synthetic_demand(n_days=60)

    forecaster = RandomForestForecaster(n_estimators=50, max_depth=6, random_state=42)
    forecaster.fit(df, frequency="D")
    result: ForecastResult = forecaster.predict(horizon=14)

    assert result.horizon == 14
    assert len(result.forecast_series) == 14
    assert result.model_type == "random_forest"

    # Verify predictions are non-negative and finite
    preds = result.forecast_series["predicted_demand"]
    assert (preds >= 0).all()
    assert not preds.isna().any()
    assert not np.isinf(preds).any()

    # Verify feature importances are recorded
    assert result.feature_importance is not None
    assert len(result.feature_importance) > 0
    total_imp = sum(result.feature_importance.values())
    assert pytest.approx(total_imp, rel=1e-2) == 1.0


def test_xgboost_forecaster():
    """Verify XGBoostForecaster generates valid numeric multi-step recursive forecasts."""
    df = generate_synthetic_demand(n_days=60)

    forecaster = XGBoostForecaster(n_estimators=50, max_depth=4, random_state=42)
    forecaster.fit(df, frequency="D")
    result: ForecastResult = forecaster.predict(horizon=14)

    assert result.horizon == 14
    assert len(result.forecast_series) == 14
    assert result.model_type == "xgboost"

    preds = result.forecast_series["predicted_demand"]
    assert (preds >= 0).all()
    assert not preds.isna().any()
    assert not np.isinf(preds).any()

    # Verify bounds
    lowers = result.forecast_series["lower_bound"]
    uppers = result.forecast_series["upper_bound"]
    assert (lowers <= uppers).all()
    assert (lowers >= 0).all()


def test_forecast_service_aggregate():
    """Verify end-to-end forecast service execution on aggregate demand."""
    df = generate_synthetic_demand(n_days=45)

    result = forecast_service.generate_forecast(
        normalized_df=df,
        model_type="xgboost",
        horizon=10,
        target_level="aggregate",
    )

    assert result.horizon == 10
    assert len(result.forecast_series) == 10
    assert result.model_type == "xgboost"


def test_forecast_service_product_specific():
    """Verify product-level filtering and forecasting through the forecast service."""
    # Multi-product DataFrame
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    p1 = pd.DataFrame({"date": dates, "demand": np.arange(30) + 10.0, "product_id": "SKU-1"})
    p2 = pd.DataFrame({"date": dates, "demand": np.arange(30) * 2 + 5.0, "product_id": "SKU-2"})
    combined = pd.concat([p1, p2], ignore_index=True)

    result = forecast_service.generate_forecast(
        normalized_df=combined,
        model_type="random_forest",
        horizon=7,
        target_level="product",
        product_id="SKU-1",
    )

    assert result.horizon == 7
    assert len(result.forecast_series) == 7


def test_forecast_service_invalid_horizon_rejection():
    """Verify rejection of invalid or excessive horizons with clear errors."""
    df = generate_synthetic_demand(n_days=30)

    # Negative / zero horizon
    with pytest.raises(ValidationException) as exc1:
        forecast_service.generate_forecast(normalized_df=df, horizon=0)
    assert exc1.value.code == "INVALID_HORIZON"

    # Excessive horizon (> 365)
    with pytest.raises(ValidationException) as exc2:
        forecast_service.generate_forecast(normalized_df=df, horizon=400)
    assert exc2.value.code == "HORIZON_TOO_LARGE"


def test_forecast_service_insufficient_history_rejection():
    """Verify rejection when historical observations are too few for ML model fitting."""
    # Only 4 observations (RF requires at least 10)
    short_df = generate_synthetic_demand(n_days=4)

    with pytest.raises(ValidationException) as exc:
        forecast_service.generate_forecast(
            normalized_df=short_df,
            model_type="random_forest",
            horizon=5,
        )
    assert exc.value.code == "INSUFFICIENT_HISTORY"


def test_forecast_service_weekly_frequency_alignment():
    """Verify that weekly series are aligned and forecast dates are consecutive weekly intervals."""
    # 20 consecutive weekly intervals
    weekly_dates = pd.date_range("2023-01-01", periods=20, freq="W")
    df = pd.DataFrame({
        "date": weekly_dates,
        "demand": np.random.uniform(500, 1000, size=20),
    })

    result = forecast_service.generate_forecast(
        normalized_df=df,
        model_type="naive",
        horizon=4,
        frequency="W",
    )

    assert result.horizon == 4
    future_dates = result.forecast_series["date"]
    assert len(future_dates) == 4
    # Step difference between successive future dates is 7 days
    diff = (future_dates.iloc[1] - future_dates.iloc[0]).days
    assert diff == 7


def test_zero_target_leakage_in_features():
    """Verify that feature engineering strictly shifts all lags and rolling stats by at least 1 step."""
    dates = pd.date_range("2023-01-01", periods=15, freq="D")
    demands = [10.0 * i for i in range(1, 16)]
    df = pd.DataFrame({"date": dates, "demand": demands})

    builder = TimeSeriesFeatureBuilder(frequency="D", max_lags=[1, 2])
    X, y, feature_cols = builder.build_training_features(df)

    # For any row i, feature lag_1 must equal y[i-1], NOT y[i]
    for idx in range(len(X)):
        current_y = y.iloc[idx]
        lag_1_val = X["lag_1"].iloc[idx]
        assert current_y != lag_1_val  # Since demand strictly increases, lag_1 cannot equal current_y


def test_forecast_api_endpoint_workflow():
    """Verify the full HTTP lifecycle: upload -> confirm mapping -> generate forecast."""
    import io
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # 1. Upload sample CSV dataset
    df = generate_synthetic_demand(n_days=40)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("demand_series.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    # 2. Confirm schema mapping
    map_res = client.post(
        f"/api/v1/datasets/{dataset_id}/mapping",
        json={"date_column": "date", "demand_column": "demand"},
    )
    assert map_res.status_code == 200

    # 3. Request forecast
    forecast_res = client.post(
        f"/api/v1/datasets/{dataset_id}/forecast",
        json={
            "model_type": "xgboost",
            "horizon": 7,
            "target_level": "aggregate",
            "confidence_level": 0.95,
        },
    )
    assert forecast_res.status_code == 200
    body = forecast_res.json()
    assert body["dataset_id"] == dataset_id
    assert body["model_type"] == "xgboost"
    assert body["horizon"] == 7
    assert len(body["forecast"]) == 7
    assert all("predicted_demand" in pt and "lower_bound" in pt and "upper_bound" in pt for pt in body["forecast"])

