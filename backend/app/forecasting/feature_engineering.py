from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


class TimeSeriesFeatureBuilder:
    """
    Extracts strictly historical time-series features (lags, rolling statistics, calendar indicators)
    guaranteeing zero future data leakage. Supports recursive multi-step forecasting.
    """

    def __init__(self, frequency: str = "D", max_lags: Optional[List[int]] = None):
        self.frequency = frequency
        self.lags = max_lags or self._determine_default_lags(frequency)
        self.rolling_windows = self._determine_rolling_windows(frequency)
        self.feature_names: List[str] = []

    def _determine_default_lags(self, freq: str) -> List[int]:
        f = freq.upper()
        if f.startswith("W"):
            return [1, 2, 4]
        elif f.startswith("M"):
            return [1, 2, 3]
        else:
            return [1, 2, 3, 7]

    def _determine_rolling_windows(self, freq: str) -> List[int]:
        f = freq.upper()
        if f.startswith("W"):
            return [2, 4]
        elif f.startswith("M"):
            return [2, 3]
        else:
            return [3, 7]

    def build_training_features(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """
        Builds X and y for supervised model training.
        Ensures all lag and rolling features are shifted by >= 1 step to prevent target leakage.
        """
        data = df.copy()
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values(by="date").reset_index(drop=True)

        feature_cols: List[str] = []

        # 1. Adapt lags to history length if series is short
        n_obs = len(data)
        usable_lags = [lag for lag in self.lags if lag < (n_obs // 2)]
        if not usable_lags:
            usable_lags = [1]
        self.lags = usable_lags

        # 2. Lag features (t-1, t-2, ...)
        for lag in self.lags:
            col_name = f"lag_{lag}"
            data[col_name] = data["demand"].shift(lag)
            feature_cols.append(col_name)

        # 3. Rolling window statistics (strictly shifted to exclude current value)
        for w in self.rolling_windows:
            if w < (n_obs // 2):
                col_mean = f"rolling_mean_{w}"
                col_std = f"rolling_std_{w}"
                data[col_mean] = data["demand"].shift(1).rolling(w).mean()
                data[col_std] = data["demand"].shift(1).rolling(w).std().fillna(0.0)
                feature_cols.extend([col_mean, col_std])

        # 4. Calendar Features
        calendar_features = self._build_calendar_features(data["date"])
        for col, values in calendar_features.items():
            data[col] = values
            feature_cols.append(col)

        # 5. Exogenous features if present
        if "price" in data.columns:
            data["exog_price"] = pd.to_numeric(data["price"], errors="coerce").bfill().ffill()
            feature_cols.append("exog_price")

        if "promotion" in data.columns:
            data["exog_promo"] = pd.to_numeric(data["promotion"], errors="coerce").fillna(0.0)
            feature_cols.append("exog_promo")

        # 6. Drop rows with NaNs introduced by initial lags
        valid_mask = data[feature_cols].notna().all(axis=1) & data["demand"].notna()
        clean_data = data[valid_mask].reset_index(drop=True)

        if len(clean_data) < 3:
            raise ValueError(
                f"Insufficient historical data to construct training features ({len(clean_data)} valid rows). "
                "More historical observations are required."
            )

        self.feature_names = feature_cols
        X_train = clean_data[feature_cols]
        y_train = clean_data["demand"]

        return X_train, y_train, feature_cols

    def build_step_feature_vector(
        self,
        history_demands: List[float],
        target_date: pd.Timestamp,
        exog_price: Optional[float] = None,
        exog_promo: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        Builds a single-row feature vector for forecasting step t+h during recursive forecasting.
        Uses the latest demands in history_demands (including prior recursive predictions).
        """
        row: Dict[str, float] = {}

        # 1. Lags
        for lag in self.lags:
            col_name = f"lag_{lag}"
            if len(history_demands) >= lag:
                row[col_name] = float(history_demands[-lag])
            else:
                row[col_name] = float(history_demands[0])

        # 2. Rolling windows
        for w in self.rolling_windows:
            col_mean = f"rolling_mean_{w}"
            col_std = f"rolling_std_{w}"
            if col_mean in self.feature_names:
                recent = history_demands[-w:] if len(history_demands) >= w else history_demands
                row[col_mean] = float(np.mean(recent))
                row[col_std] = float(np.std(recent)) if len(recent) > 1 else 0.0

        # 3. Calendar Features for target_date
        cal = self._build_single_calendar_features(target_date)
        for col, val in cal.items():
            if col in self.feature_names:
                row[col] = float(val)

        # 4. Exogenous features
        if "exog_price" in self.feature_names:
            row["exog_price"] = float(exog_price if exog_price is not None else 0.0)

        if "exog_promo" in self.feature_names:
            row["exog_promo"] = float(exog_promo if exog_promo is not None else 0.0)

        # Ensure exact column ordering matching training
        feature_df = pd.DataFrame([row])[self.feature_names]
        return feature_df

    def _build_calendar_features(self, dates: pd.Series) -> Dict[str, pd.Series]:
        return {
            "day_of_week": dates.dt.dayofweek,
            "day_of_month": dates.dt.day,
            "month": dates.dt.month,
            "is_weekend": (dates.dt.dayofweek >= 5).astype(int),
            "quarter": dates.dt.quarter,
        }

    def _build_single_calendar_features(self, date: pd.Timestamp) -> Dict[str, int]:
        return {
            "day_of_week": date.dayofweek,
            "day_of_month": date.day,
            "month": date.month,
            "is_weekend": 1 if date.dayofweek >= 5 else 0,
            "quarter": date.quarter,
        }
