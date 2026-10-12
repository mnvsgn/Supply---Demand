"""
Date and temporal series utilities for supply & demand analytics.
Provides date parsing, frequency alignment, and calendar sequence helpers.
"""

from typing import List, Optional, Tuple
import pandas as pd


def parse_dates_safely(series: pd.Series) -> pd.Series:
    """Parse pandas series to datetime safely with coercion."""
    return pd.to_datetime(series, errors="coerce")


def infer_series_frequency(dates: pd.Series) -> str:
    """
    Infer the time frequency of a sorted DatetimeIndex / Series.
    Returns 'D' (daily), 'W' (weekly), 'M' (monthly), or 'D' as default.
    """
    cleaned = pd.to_datetime(dates.dropna().unique())
    if len(cleaned) < 3:
        return "D"

    sorted_dates = pd.Series(cleaned).sort_values()
    diffs = sorted_dates.diff().dropna()
    median_days = diffs.dt.total_seconds().median() / 86400.0

    if 0.8 <= median_days <= 1.2:
        return "D"
    elif 6.0 <= median_days <= 8.0:
        return "W"
    elif 27.0 <= median_days <= 32.0:
        return "M"
    return "D"


def detect_date_gaps(dates: pd.Series, freq: Optional[str] = None) -> List[Tuple[str, str]]:
    """
    Detect missing date intervals in an observed time series.
    Returns list of (gap_start, gap_end) string tuples.
    """
    cleaned = pd.to_datetime(dates.dropna().unique())
    if len(cleaned) < 2:
        return []

    sorted_dates = pd.DatetimeIndex(cleaned).sort_values()
    inferred = freq or infer_series_frequency(pd.Series(sorted_dates))

    expected_range = pd.date_range(start=sorted_dates[0], end=sorted_dates[-1], freq=inferred)
    missing = expected_range.difference(sorted_dates)

    if len(missing) == 0:
        return []

    # Group consecutive missing dates into intervals
    gaps = []
    current_start = missing[0]
    prev_date = missing[0]

    for d in missing[1:]:
        if (d - prev_date).days > (7 if inferred == 'W' else 1):
            gaps.append((current_start.strftime("%Y-%m-%d"), prev_date.strftime("%Y-%m-%d")))
            current_start = d
        prev_date = d
    gaps.append((current_start.strftime("%Y-%m-%d"), prev_date.strftime("%Y-%m-%d")))
    return gaps
