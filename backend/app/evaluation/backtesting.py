"""
Rolling-origin time-series cross-validation backtester.
Simulates production forecasting iteratively over expanding chronological windows.
"""

from dataclasses import dataclass
from typing import List
import pandas as pd


@dataclass
class BacktestFold:
    """Container for a single rolling-origin backtest fold."""
    fold_index: int
    train_df: pd.DataFrame
    val_df: pd.DataFrame
    cutoff_date: str
    val_start: str
    val_end: str


class RollingOriginBacktester:
    """
    Generates expanding-window rolling-origin evaluation folds.
    Simulates production deployment across historical forecast horizons.
    """

    def __init__(self, horizon: int, n_folds: int = 3, min_train_size: int = 10):
        if horizon < 1:
            raise ValueError(f"Forecast horizon must be >= 1 (got {horizon}).")
        if n_folds < 1:
            raise ValueError(f"Number of backtest folds must be >= 1 (got {n_folds}).")
        if min_train_size < 1:
            raise ValueError(f"min_train_size must be >= 1 (got {min_train_size}).")

        self.horizon = horizon
        self.requested_folds = n_folds
        self.min_train_size = min_train_size

    def generate_folds(self, df: pd.DataFrame) -> List[BacktestFold]:
        """
        Creates expanding chronological folds.
        Fold k trains on observations up to cutoff_k and evaluates on [cutoff_k + 1, cutoff_k + horizon].
        """
        if df.empty or len(df) < (self.min_train_size + self.horizon):
            raise ValueError(
                f"Insufficient historical observations ({len(df)}) for rolling backtest. "
                f"Required at least min_train_size ({self.min_train_size}) + horizon ({self.horizon}) = "
                f"{self.min_train_size + self.horizon} rows."
            )

        data = df.copy()
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values(by="date").reset_index(drop=True)
        total_n = len(data)

        # Available evaluation span
        eval_span = total_n - self.min_train_size
        max_possible_folds = max(1, eval_span // self.horizon)
        actual_folds = min(self.requested_folds, max_possible_folds)

        folds: List[BacktestFold] = []
        for i in range(actual_folds):
            cutoff_idx = total_n - ((actual_folds - i) * self.horizon)
            if cutoff_idx < self.min_train_size:
                continue

            train_slice = data.iloc[:cutoff_idx].copy().reset_index(drop=True)
            val_slice = data.iloc[cutoff_idx : cutoff_idx + self.horizon].copy().reset_index(drop=True)

            if len(val_slice) < self.horizon:
                continue

            folds.append(
                BacktestFold(
                    fold_index=i + 1,
                    train_df=train_slice,
                    val_df=val_slice,
                    cutoff_date=str(train_slice["date"].max().strftime("%Y-%m-%d")),
                    val_start=str(val_slice["date"].min().strftime("%Y-%m-%d")),
                    val_end=str(val_slice["date"].max().strftime("%Y-%m-%d")),
                )
            )

        if not folds:
            raise ValueError(
                f"Unable to generate valid backtest folds for horizon {self.horizon} with {total_n} observations."
            )

        return folds
