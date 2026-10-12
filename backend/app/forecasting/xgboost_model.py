from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from app.forecasting.base import BaseForecaster, ForecastResult
from app.forecasting.feature_engineering import TimeSeriesFeatureBuilder


class XGBoostForecaster(BaseForecaster):
    """
    Gradient boosted decision trees forecaster using XGBoost.
    Leverages identical lag, rolling, and calendar feature structures as Random Forest
    with recursive multi-step forecasting and reproducible seeds.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 5,
        learning_rate: float = 0.08,
        random_state: int = 42,
    ):
        super().__init__(model_name="XGBoost Regressor", model_type="xgboost")
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state

        self.model = XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
            n_jobs=1,
            objective="reg:squarederror",
            verbosity=0,
        )
        self.feature_builder: Optional[TimeSeriesFeatureBuilder] = None
        self.training_history: Optional[pd.DataFrame] = None
        self.residual_std: float = 1.0
        self.feature_importances: Dict[str, float] = {}

    def fit(self, df: pd.DataFrame, frequency: str = "D") -> "XGBoostForecaster":
        if df.empty or len(df) < 5:
            raise ValueError(
                f"XGBoostForecaster requires at least 5 observations, found {len(df)}."
            )

        self.frequency = frequency
        self.last_date = pd.to_datetime(df["date"]).max()
        self.history_length = len(df)
        self.training_history = df.copy()

        # Build feature matrix
        self.feature_builder = TimeSeriesFeatureBuilder(frequency=frequency)
        X_train, y_train, feature_names = self.feature_builder.build_training_features(df)

        # Fit XGBoost model
        self.model.fit(X_train, y_train)

        # Estimate residual uncertainty for prediction intervals
        in_sample_preds = self.model.predict(X_train)
        residuals = y_train.to_numpy() - in_sample_preds
        self.residual_std = float(np.std(residuals)) if len(residuals) > 1 else 1.0

        # Store feature importances
        importances = self.model.feature_importances_
        self.feature_importances = {
            name: round(float(imp), 4)
            for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
        }

        self.is_fitted = True
        return self

    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        exog_future: Optional[pd.DataFrame] = None,
    ) -> ForecastResult:
        if not self.is_fitted or self.feature_builder is None or self.training_history is None:
            raise ValueError("Forecaster must be fitted before predict() is called.")
        if horizon < 1:
            raise ValueError("Forecast horizon must be at least 1 period.")

        future_dates = self._generate_future_dates(horizon)

        # Recursive multi-step forecasting loop
        history_demands = list(self.training_history["demand"].dropna().values)
        predictions: List[float] = []

        for h, date in enumerate(future_dates):
            price_val = None
            promo_val = None
            if exog_future is not None and not exog_future.empty and h < len(exog_future):
                if "price" in exog_future.columns:
                    price_val = float(exog_future["price"].iloc[h])
                if "promotion" in exog_future.columns:
                    promo_val = float(exog_future["promotion"].iloc[h])

            # Build step feature vector using updated recursive history
            X_step = self.feature_builder.build_step_feature_vector(
                history_demands=history_demands,
                target_date=date,
                exog_price=price_val,
                exog_promo=promo_val,
            )

            # Predict next step
            y_pred = float(self.model.predict(X_step)[0])
            y_pred = max(0.0, y_pred)

            predictions.append(y_pred)
            history_demands.append(y_pred)

        preds_arr = np.array(predictions)

        # Prediction intervals (uncertainty compounds with recursive horizon)
        z = 1.96 if confidence_level >= 0.95 else 1.645
        step_indices = np.arange(1, horizon + 1)
        compound_std = self.residual_std * np.sqrt(1.0 + 0.05 * (step_indices - 1))
        interval_width = z * compound_std

        lower_bounds = np.maximum(0.0, preds_arr - interval_width)
        upper_bounds = preds_arr + interval_width

        forecast_df = pd.DataFrame({
            "date": future_dates,
            "predicted_demand": preds_arr,
            "lower_bound": lower_bounds,
            "upper_bound": upper_bounds,
        })

        return ForecastResult(
            forecast_series=forecast_df,
            model_name=self.model_name,
            model_type=self.model_type,
            horizon=horizon,
            frequency=self.frequency,
            feature_importance=self.feature_importances,
            metadata={
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "learning_rate": self.learning_rate,
            },
        )
