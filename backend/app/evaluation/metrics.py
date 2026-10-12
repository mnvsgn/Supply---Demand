"""
Time-series forecasting evaluation metrics.
Provides MAE, RMSE, and WAPE with safe zero-demand handling and input validation.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd


def _to_clean_1d_arrays(
    y_true: Union[np.ndarray, pd.Series, List[float]],
    y_pred: Union[np.ndarray, pd.Series, List[float]],
) -> tuple[np.ndarray, np.ndarray]:
    """
    Validates and converts y_true and y_pred into clean 1D float numpy arrays.
    Raises ValueError on empty, mismatched, or invalid inputs.
    """
    arr_true = np.asarray(y_true, dtype=float).ravel()
    arr_pred = np.asarray(y_pred, dtype=float).ravel()

    if arr_true.size == 0 or arr_pred.size == 0:
        raise ValueError("Cannot calculate metrics on empty actuals or predictions.")

    if arr_true.size != arr_pred.size:
        raise ValueError(
            f"Length mismatch: y_true has {arr_true.size} observations, "
            f"y_pred has {arr_pred.size} predictions."
        )

    if np.isnan(arr_true).any() or np.isnan(arr_pred).any():
        raise ValueError("Inputs contain NaN values. Clean missing data before calculating metrics.")

    if np.isinf(arr_true).any() or np.isinf(arr_pred).any():
        raise ValueError("Inputs contain Infinite values.")

    return arr_true, arr_pred


def calculate_mae(
    y_true: Union[np.ndarray, pd.Series, List[float]],
    y_pred: Union[np.ndarray, pd.Series, List[float]],
) -> float:
    """
    Mean Absolute Error:
    MAE = (1 / n) * sum(|y_true - y_pred|)
    """
    arr_true, arr_pred = _to_clean_1d_arrays(y_true, y_pred)
    return float(np.mean(np.abs(arr_true - arr_pred)))


def calculate_rmse(
    y_true: Union[np.ndarray, pd.Series, List[float]],
    y_pred: Union[np.ndarray, pd.Series, List[float]],
) -> float:
    """
    Root Mean Squared Error:
    RMSE = sqrt((1 / n) * sum((y_true - y_pred)^2))
    """
    arr_true, arr_pred = _to_clean_1d_arrays(y_true, y_pred)
    return float(np.sqrt(np.mean(np.square(arr_true - arr_pred))))


def calculate_wape(
    y_true: Union[np.ndarray, pd.Series, List[float]],
    y_pred: Union[np.ndarray, pd.Series, List[float]],
) -> Optional[float]:
    """
    Weighted Absolute Percentage Error (WAPE), expressed as a percentage:
    WAPE = (sum(|y_true - y_pred|) / sum(|y_true|)) * 100

    Safe Zero-Demand Handling:
    - If sum(|y_true|) == 0 and sum(|y_true - y_pred|) == 0: returns 0.0% (exact match on zero).
    - If sum(|y_true|) == 0 and sum(|y_true - y_pred|) > 0: returns None (mathematically undefined, avoids ZeroDivisionError).
    - Individual y_true[i] == 0 observations do NOT cause division-by-zero (unlike MAPE).
    """
    arr_true, arr_pred = _to_clean_1d_arrays(y_true, y_pred)
    sum_abs_errors = float(np.sum(np.abs(arr_true - arr_pred)))
    sum_actuals = float(np.sum(np.abs(arr_true)))

    if sum_actuals == 0.0:
        if sum_abs_errors == 0.0:
            return 0.0
        return None

    return float((sum_abs_errors / sum_actuals) * 100.0)


def calculate_evaluation_metrics(
    y_true: Union[np.ndarray, pd.Series, List[float]],
    y_pred: Union[np.ndarray, pd.Series, List[float]],
    round_digits: int = 4,
) -> Dict[str, Optional[float]]:
    """
    Computes all standard evaluation metrics (MAE, RMSE, WAPE) in a unified structure.
    """
    mae_val = calculate_mae(y_true, y_pred)
    rmse_val = calculate_rmse(y_true, y_pred)
    wape_val = calculate_wape(y_true, y_pred)

    return {
        "mae": round(mae_val, round_digits),
        "rmse": round(rmse_val, round_digits),
        "wape": round(wape_val, round_digits) if wape_val is not None else None,
    }
