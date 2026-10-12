from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from app.forecasting.base import BaseForecaster, ForecastResult


class NaiveForecaster(BaseForecaster):
    """
    Last-observation baseline forecaster.
    Projects the most recently observed demand value into all future periods.
    """

    def __init__(self):
        super().__init__(model_name="Naive (Last Observation)", model_type="naive")
        self.last_demand: Optional[float] = None
        self.historical_std: float = 0.0

    def fit(self, df: pd.DataFrame, frequency: str = "D") -> "NaiveForecaster":
        if df.empty or len(df) < 1:
            raise ValueError("Cannot fit NaiveForecaster on an empty dataset.")

        self.frequency = frequency
        self.last_date = pd.to_datetime(df["date"]).max()
        self.history_length = len(df)
        self.last_demand = float(df["demand"].iloc[-1])

        # Compute standard deviation of historical step changes for prediction intervals
        diffs = df["demand"].diff().dropna()
        self.historical_std = float(diffs.std()) if len(diffs) > 1 and not np.isnan(diffs.std()) else 1.0

        self.is_fitted = True
        return self

    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        exog_future: Optional[pd.DataFrame] = None,
    ) -> ForecastResult:
        if not self.is_fitted or self.last_demand is None:
            raise ValueError("Forecaster must be fitted before predict() is called.")
        if horizon < 1:
            raise ValueError("Forecast horizon must be at least 1 period.")

        future_dates = self._generate_future_dates(horizon)
        predictions = np.full(horizon, self.last_demand)

        # Standard error grows with sqrt(h) under a random-walk assumption
        z = 1.96 if confidence_level >= 0.95 else 1.645
        step_indices = np.arange(1, horizon + 1)
        interval_width = z * self.historical_std * np.sqrt(step_indices)

        lower_bounds = np.maximum(0.0, predictions - interval_width)
        upper_bounds = predictions + interval_width

        forecast_df = pd.DataFrame({
            "date": future_dates,
            "predicted_demand": predictions,
            "lower_bound": lower_bounds,
            "upper_bound": upper_bounds,
        })

        return ForecastResult(
            forecast_series=forecast_df,
            model_name=self.model_name,
            model_type=self.model_type,
            horizon=horizon,
            frequency=self.frequency,
            metadata={"last_observed_value": self.last_demand},
        )


class SeasonalNaiveForecaster(BaseForecaster):
    """
    Seasonal Naive forecaster.
    Projects the demand value from the identical season period in the preceding cycle.
    Falls back to Simple Naive with an explicit warning when seasonal history is insufficient.
    """

    def __init__(self, seasonal_period: Optional[int] = None):
        super().__init__(model_name="Seasonal Naive", model_type="seasonal_naive")
        self.seasonal_period = seasonal_period
        self.effective_period: int = 7
        self.history: Optional[np.ndarray] = None
        self.fallback_used: bool = False
        self.fallback_reason: Optional[str] = None
        self.historical_std: float = 0.0

    def fit(self, df: pd.DataFrame, frequency: str = "D") -> "SeasonalNaiveForecaster":
        if df.empty or len(df) < 1:
            raise ValueError("Cannot fit SeasonalNaiveForecaster on an empty dataset.")

        self.frequency = frequency
        self.last_date = pd.to_datetime(df["date"]).max()
        self.history_length = len(df)
        self.history = df["demand"].to_numpy(dtype=float)

        # Determine expected seasonal period length if not explicitly specified
        if self.seasonal_period is not None:
            self.effective_period = self.seasonal_period
        else:
            freq_upper = frequency.upper()
            if freq_upper.startswith("W"):
                # For weekly, standard annual cycle is 52. If history is short, check 4-week cycle
                self.effective_period = 52 if len(df) >= 104 else 4
            elif freq_upper.startswith("M"):
                self.effective_period = 12
            else:
                # Default daily weekly periodicity
                self.effective_period = 7

        # Check whether sufficient seasonal cycles exist (minimum 2 full cycles required)
        min_required_history = 2 * self.effective_period
        if self.history_length < min_required_history:
            self.fallback_used = True
            self.fallback_reason = (
                f"Seasonal baseline requires at least 2 full cycles of history "
                f"({min_required_history} observations for season length {self.effective_period}), "
                f"but only {self.history_length} observations were provided. "
                "Fell back to simple last-observation baseline."
            )

        # Estimate seasonal residual standard deviation
        if not self.fallback_used and self.history_length > self.effective_period:
            seasonal_diffs = self.history[self.effective_period:] - self.history[:-self.effective_period]
            self.historical_std = float(np.nanstd(seasonal_diffs)) if len(seasonal_diffs) > 1 else 1.0
        else:
            diffs = np.diff(self.history)
            self.historical_std = float(np.nanstd(diffs)) if len(diffs) > 1 else 1.0

        self.is_fitted = True
        return self

    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        exog_future: Optional[pd.DataFrame] = None,
    ) -> ForecastResult:
        if not self.is_fitted or self.history is None:
            raise ValueError("Forecaster must be fitted before predict() is called.")
        if horizon < 1:
            raise ValueError("Forecast horizon must be at least 1 period.")

        future_dates = self._generate_future_dates(horizon)
        predictions = np.zeros(horizon)
        warnings: List[str] = []

        if self.fallback_used:
            # Fall back to last observed value
            last_val = self.history[-1]
            predictions[:] = last_val
            warnings.append(self.fallback_reason or "Fell back to simple naive.")
        else:
            # Cycle through the most recent full seasonal cycle
            s = self.effective_period
            last_cycle = self.history[-s:]
            for h in range(horizon):
                predictions[h] = last_cycle[h % s]

        # Uncertainty intervals
        z = 1.96 if confidence_level >= 0.95 else 1.645
        step_indices = np.arange(1, horizon + 1)
        cycle_scale = np.ceil(step_indices / max(1, self.effective_period))
        interval_width = z * self.historical_std * np.sqrt(cycle_scale)

        lower_bounds = np.maximum(0.0, predictions - interval_width)
        upper_bounds = predictions + interval_width

        forecast_df = pd.DataFrame({
            "date": future_dates,
            "predicted_demand": predictions,
            "lower_bound": lower_bounds,
            "upper_bound": upper_bounds,
        })

        return ForecastResult(
            forecast_series=forecast_df,
            model_name=self.model_name,
            model_type=self.model_type,
            horizon=horizon,
            frequency=self.frequency,
            metadata={
                "seasonal_period": self.effective_period,
                "fallback_to_simple_naive": self.fallback_used,
            },
            warnings=warnings,
        )
