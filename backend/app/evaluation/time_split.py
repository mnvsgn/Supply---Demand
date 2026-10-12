"""
Chronological time-series splitting module.
Guarantees strict forward-temporal partitioning with zero target leakage.
"""

from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class ChronologicalSplit:
    """Container for chronologically partitioned datasets."""
    train: pd.DataFrame
    val: pd.DataFrame
    test: Optional[pd.DataFrame] = None

    @property
    def train_start(self) -> str:
        return str(pd.to_datetime(self.train["date"]).min().strftime("%Y-%m-%d"))

    @property
    def train_end(self) -> str:
        return str(pd.to_datetime(self.train["date"]).max().strftime("%Y-%m-%d"))

    @property
    def val_start(self) -> str:
        return str(pd.to_datetime(self.val["date"]).min().strftime("%Y-%m-%d"))

    @property
    def val_end(self) -> str:
        return str(pd.to_datetime(self.val["date"]).max().strftime("%Y-%m-%d"))

    @property
    def test_start(self) -> Optional[str]:
        if self.test is not None and not self.test.empty:
            return str(pd.to_datetime(self.test["date"]).min().strftime("%Y-%m-%d"))
        return None

    @property
    def test_end(self) -> Optional[str]:
        if self.test is not None and not self.test.empty:
            return str(pd.to_datetime(self.test["date"]).max().strftime("%Y-%m-%d"))
        return None


def chronological_split(
    df: pd.DataFrame,
    val_size: Optional[int] = None,
    test_size: Optional[int] = None,
    val_ratio: float = 0.15,
    test_ratio: float = 0.0,
) -> ChronologicalSplit:
    """
    Partitions a time-series DataFrame into strictly chronological Train / Validation / Test sets.
    Never shuffles. Guarantees train_end < val_start < test_start.
    """
    if df.empty or len(df) < 3:
        raise ValueError(
            f"Cannot perform chronological split on dataset with only {len(df)} rows. Minimum 3 required."
        )

    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values(by="date").reset_index(drop=True)
    n = len(data)

    # Determine split counts
    if test_size is not None:
        n_test = max(0, test_size)
    else:
        n_test = int(n * test_ratio) if test_ratio > 0.0 else 0

    if val_size is not None:
        n_val = max(1, val_size)
    else:
        n_val = max(1, int(n * val_ratio))

    n_train = n - n_val - n_test

    if n_train < 1:
        raise ValueError(
            f"Requested split sizes (val={n_val}, test={n_test}) leave {n_train} rows for training. "
            f"Total available rows: {n}."
        )

    train_part = data.iloc[:n_train].copy().reset_index(drop=True)
    val_part = data.iloc[n_train : n_train + n_val].copy().reset_index(drop=True)
    test_part = (
        data.iloc[n_train + n_val :].copy().reset_index(drop=True)
        if n_test > 0
        else None
    )

    # Strict temporal ordering assertion
    assert train_part["date"].max() < val_part["date"].min(), "Train/Val temporal leakage detected!"
    if test_part is not None and not test_part.empty:
        assert val_part["date"].max() < test_part["date"].min(), "Val/Test temporal leakage detected!"

    return ChronologicalSplit(train=train_part, val=val_part, test=test_part)
