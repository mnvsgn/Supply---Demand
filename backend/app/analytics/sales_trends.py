"""
Sales trends and product rankings analysis module.
Computes empirical slopes, half-split growth rates, coefficient of variation,
and Pareto product distribution.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def analyze_sales_trend(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes historical demand trajectory, statistical dispersion, and trend direction.
    """
    if df.empty or "demand" not in df.columns:
        return {
            "direction": "insufficient_data",
            "slope": 0.0,
            "growth_rate_pct": 0.0,
            "mean_demand": 0.0,
            "std_demand": 0.0,
            "total_volume": 0.0,
            "total_periods": 0,
        }

    demands = df["demand"].dropna().values
    n = len(demands)
    if n < 3:
        return {
            "direction": "insufficient_data",
            "slope": 0.0,
            "growth_rate_pct": 0.0,
            "mean_demand": float(np.mean(demands)) if n > 0 else 0.0,
            "std_demand": 0.0,
            "total_volume": float(np.sum(demands)) if n > 0 else 0.0,
            "total_periods": n,
        }

    mean_val = float(np.mean(demands))
    std_val = float(np.std(demands, ddof=1)) if n > 1 else 0.0
    total_vol = float(np.sum(demands))

    # Linear trend calculation via least squares
    x = np.arange(n)
    slope, _ = np.polyfit(x, demands, 1)

    # Growth rate comparing first half to second half
    half = n // 2
    first_half_mean = float(np.mean(demands[:half])) if half > 0 else mean_val
    second_half_mean = float(np.mean(demands[half:])) if half > 0 else mean_val

    growth_pct = 0.0
    if first_half_mean > 0:
        growth_pct = ((second_half_mean - first_half_mean) / first_half_mean) * 100.0

    # Direction categorization
    cv = (std_val / mean_val) if mean_val > 0 else 0.0
    if slope > 0.05 or growth_pct > 5.0:
        direction = "upward"
    elif slope < -0.05 or growth_pct < -5.0:
        direction = "downward"
    else:
        direction = "stable"

    return {
        "direction": direction,
        "slope": round(float(slope), 3),
        "growth_rate_pct": round(float(growth_pct), 1),
        "mean_demand": round(mean_val, 2),
        "std_demand": round(std_val, 2),
        "coefficient_of_variation": round(float(cv), 3),
        "total_volume": round(total_vol, 2),
        "total_periods": int(n),
    }


def analyze_product_rankings(df: pd.DataFrame, top_n: int = 10) -> Optional[List[Dict[str, Any]]]:
    """
    Ranks products by total historical volume and computes Pareto cumulative contribution.
    """
    if df.empty or "product_id" not in df.columns or "demand" not in df.columns:
        return None

    grouped = (
        df.groupby("product_id")["demand"]
        .agg(["sum", "mean", "count"])
        .reset_index()
    )
    if grouped.empty:
        return None

    total_sales = grouped["sum"].sum()
    if total_sales <= 0:
        return None

    grouped = grouped.sort_values(by="sum", ascending=False).reset_index(drop=True)
    grouped["volume_share_pct"] = (grouped["sum"] / total_sales) * 100.0
    grouped["cumulative_share_pct"] = grouped["volume_share_pct"].cumsum()

    rankings = []
    for idx, row in grouped.head(top_n).iterrows():
        rankings.append({
            "rank": int(idx + 1),
            "product_id": str(row["product_id"]),
            "total_volume": round(float(row["sum"]), 2),
            "avg_demand": round(float(row["mean"]), 2),
            "volume_share_pct": round(float(row["volume_share_pct"]), 1),
            "cumulative_share_pct": round(float(row["cumulative_share_pct"]), 1),
            "total_records": int(row["count"]),
        })

    return rankings
