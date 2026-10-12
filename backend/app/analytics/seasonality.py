"""
Seasonality analysis module.
Computes day-of-week multipliers, peak/trough days, and weekend lift patterns.
"""

from typing import Any, Dict
import numpy as np
import pandas as pd


def analyze_seasonality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes day-of-week demand multipliers, peak/trough calendar periods,
    and empirical weekend lift.
    """
    if df.empty or "date" not in df.columns or "demand" not in df.columns:
        return {
            "has_seasonality": False,
            "pattern_summary": "Insufficient temporal observations to assess seasonality.",
            "day_of_week_indices": {},
            "peak_day": None,
            "trough_day": None,
        }

    work_df = df.copy()
    work_df["date"] = pd.to_datetime(work_df["date"], errors="coerce")
    work_df = work_df.dropna(subset=["date", "demand"])

    if len(work_df) < 14:
        return {
            "has_seasonality": False,
            "pattern_summary": "Series contains fewer than 14 observations; seasonal indices cannot be measured reliably.",
            "day_of_week_indices": {},
            "peak_day": None,
            "trough_day": None,
        }

    work_df["day_name"] = work_df["date"].dt.day_name()
    work_df["day_of_week"] = work_df["date"].dt.dayofweek

    day_stats = (
        work_df.groupby(["day_of_week", "day_name"])["demand"]
        .agg(["mean", "count"])
        .reset_index()
    )
    overall_mean = work_df["demand"].mean()

    if overall_mean <= 0 or len(day_stats) < 4:
        return {
            "has_seasonality": False,
            "pattern_summary": "Low demand variance or insufficient unique weekdays.",
            "day_of_week_indices": {},
            "peak_day": None,
            "trough_day": None,
        }

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    indices_dict = {}

    for day in day_order:
        row = day_stats[day_stats["day_name"] == day]
        if not row.empty:
            d_mean = float(row["mean"].values[0])
            idx_ratio = d_mean / overall_mean
            deviation = (idx_ratio - 1.0) * 100.0
            indices_dict[day] = {
                "index": round(idx_ratio, 2),
                "avg_demand": round(d_mean, 2),
                "deviation_pct": round(deviation, 1),
            }
        else:
            indices_dict[day] = {
                "index": 1.0,
                "avg_demand": round(overall_mean, 2),
                "deviation_pct": 0.0,
            }

    # Find peak and trough
    peak_day = max(indices_dict, key=lambda k: indices_dict[k]["index"])
    trough_day = min(indices_dict, key=lambda k: indices_dict[k]["index"])

    # Weekend lift (Sat/Sun vs Mon-Fri)
    weekday_means = [indices_dict[d]["avg_demand"] for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] if d in indices_dict]
    weekend_means = [indices_dict[d]["avg_demand"] for d in ["Saturday", "Sunday"] if d in indices_dict]

    weekend_lift = 0.0
    if weekday_means and weekend_means and np.mean(weekday_means) > 0:
        weekend_lift = ((np.mean(weekend_means) - np.mean(weekday_means)) / np.mean(weekday_means)) * 100.0

    return {
        "has_seasonality": True,
        "pattern_summary": f"Peak demand occurs on {peak_day} ({indices_dict[peak_day]['index']}x average), with lowest demand on {trough_day}.",
        "day_of_week_indices": indices_dict,
        "peak_day": peak_day,
        "trough_day": trough_day,
        "weekend_lift_pct": round(float(weekend_lift), 1),
    }
