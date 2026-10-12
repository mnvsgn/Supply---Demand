from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class ForecastPoint(dict):
    """Dictionary representing a single forecast point with .to_dict() compatibility."""
    def to_dict(self) -> Dict[str, Any]:
        return dict(self)


@dataclass
class ForecastResult:
    """Standardized output container for time-series forecast models."""
    forecast_series: pd.DataFrame  # Columns: ['date', 'predicted_demand', 'lower_bound', 'upper_bound']
    model_name: str
    model_type: str
    horizon: int
    frequency: str
    feature_importance: Optional[Dict[str, float]] = None
    metrics: Optional[Dict[str, Optional[float]]] = None
    model_comparison: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def forecast(self) -> List[Dict[str, Any]]:
        """List of forecast points for convenient property access."""
        return self.to_dict()["forecast"]

    def to_dict(self) -> Dict[str, Any]:
        """Converts result to JSON-serializable dictionary."""
        records = []
        for _, row in self.forecast_series.iterrows():
            date_val = row["date"]
            date_str = (
                date_val.strftime("%Y-%m-%d")
                if isinstance(date_val, (pd.Timestamp, pd.Period))
                else str(date_val)
            )
            records.append(ForecastPoint({
                "date": date_str,
                "predicted_demand": round(float(row["predicted_demand"]), 2),
                "lower_bound": round(float(row.get("lower_bound", row["predicted_demand"])), 2),
                "upper_bound": round(float(row.get("upper_bound", row["predicted_demand"])), 2),
            }))

        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "horizon": self.horizon,
            "frequency": self.frequency,
            "forecast": records,
            "feature_importance": self.feature_importance,
            "metrics": self.metrics,
            "model_comparison": self.model_comparison,
            "metadata": self.metadata,
            "warnings": self.warnings,
        }


# Type alias for backwards compatibility
ForecastExecutionResult = ForecastResult


class BaseForecaster(ABC):

    """Abstract base class establishing the forecasting model contract."""

    def __init__(self, model_name: str, model_type: str):
        self.model_name = model_name
        self.model_type = model_type
        self.is_fitted = False
        self.frequency = "D"
        self.last_date: Optional[pd.Timestamp] = None
        self.history_length: int = 0

    @abstractmethod
    def fit(self, df: pd.DataFrame, frequency: str = "D") -> "BaseForecaster":
        """
        Fits the forecasting model onto a continuous, chronologically sorted DataFrame.
        Expected minimum columns: ['date', 'demand'].
        """
        pass

    @abstractmethod
    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        exog_future: Optional[pd.DataFrame] = None,
    ) -> ForecastResult:
        """
        Generates out-of-sample demand projections for the given future horizon.
        """
        pass

    def _generate_future_dates(self, horizon: int) -> pd.DatetimeIndex:
        """
        Generates subsequent timestamp intervals following self.last_date based on frequency.
        """
        if self.last_date is None:
            raise ValueError("Model has not been fitted with historical timestamps.")

        # Map common aliases
        freq_alias = self.frequency
        if freq_alias.startswith("W"):
            freq_alias = "W"
        elif freq_alias.startswith("M"):
            freq_alias = "M"

        # Generate future dates strictly following last date
        future_dates = pd.date_range(
            start=self.last_date,
            periods=horizon + 1,
            freq=freq_alias,
        )[1:]

        return future_dates
