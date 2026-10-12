from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class DataQualityReport:
    is_valid: bool
    row_count: int
    date_range: Dict[str, Optional[str]]
    detected_frequency: str
    is_regular_frequency: bool
    missing_values: Dict[str, int]
    missing_percentages: Dict[str, float]
    duplicate_rows_count: int
    negative_demand_count: int
    zero_demand_count: int
    date_gaps_count: int
    warnings: List[str] = field(default_factory=list)


class DataValidator:
    """
    Validates data quality on mapped datasets:
    - Safely verifies date parseability and detects time frequency without assuming daily intervals.
    - Inspects duplicate entity timestamps, nulls, negative demand, and date gaps.
    - Returns structured diagnostic quality metrics and warnings without inventing data.
    """

    def validate(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, Optional[str]],
    ) -> DataQualityReport:
        warnings: List[str] = []
        is_valid = True

        date_col = mapping.get("date")
        demand_col = mapping.get("demand")
        product_col = mapping.get("product_id")
        store_col = mapping.get("store_id")

        if not date_col or date_col not in df.columns:
            raise ValueError(f"Required date column '{date_col}' not found in dataset.")
        if not demand_col or demand_col not in df.columns:
            raise ValueError(f"Required demand column '{demand_col}' not found in dataset.")

        total_rows = len(df)

        # 1. Date Parseability & Range
        parsed_dates = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
        invalid_dates_count = int(parsed_dates.isna().sum())

        if invalid_dates_count > 0:
            pct = (invalid_dates_count / total_rows) * 100
            warnings.append(
                f"Date column '{date_col}' contains {invalid_dates_count} unparseable or null timestamp(s) ({pct:.1f}%)."
            )
            if invalid_dates_count == total_rows:
                is_valid = False

        valid_dates = parsed_dates.dropna()
        if not valid_dates.empty:
            start_date = valid_dates.min().strftime("%Y-%m-%d")
            end_date = valid_dates.max().strftime("%Y-%m-%d")
            total_calendar_days = (valid_dates.max() - valid_dates.min()).days + 1
        else:
            start_date, end_date = None, None
            total_calendar_days = 0

        date_range = {
            "start": start_date,
            "end": end_date,
            "total_calendar_days": total_calendar_days,
        }

        # 2. Demand Numeric Health
        numeric_demand = pd.to_numeric(df[demand_col], errors="coerce")
        null_demand_count = int(numeric_demand.isna().sum())
        negative_demand_count = int((numeric_demand < 0).sum())
        zero_demand_count = int((numeric_demand == 0).sum())

        if null_demand_count > 0:
            pct = (null_demand_count / total_rows) * 100
            warnings.append(
                f"Target demand column '{demand_col}' contains {null_demand_count} missing or non-numeric value(s) ({pct:.1f}%)."
            )

        if negative_demand_count > 0:
            warnings.append(
                f"Target demand column '{demand_col}' contains {negative_demand_count} negative value(s). "
                "These may represent returns, refunds, or inventory adjustments."
            )

        # 3. Missing Values Across All Mapped Columns
        missing_values: Dict[str, int] = {}
        missing_percentages: Dict[str, float] = {}

        for role, col_name in mapping.items():
            if col_name and col_name in df.columns:
                null_cnt = int(df[col_name].isna().sum())
                missing_values[col_name] = null_cnt
                missing_percentages[col_name] = round((null_cnt / total_rows) * 100, 2)
                if null_cnt > 0 and role not in ("date", "demand"):
                    warnings.append(
                        f"Optional column '{col_name}' ({role}) contains {null_cnt} missing value(s) ({missing_percentages[col_name]}%)."
                    )

        # 4. Duplicate Records Check
        composite_keys = [c for c in [date_col, product_col, store_col] if c and c in df.columns]
        duplicate_rows_count = 0
        if composite_keys:
            duplicate_mask = df.duplicated(subset=composite_keys, keep=False)
            duplicate_rows_count = int(duplicate_mask.sum())
            if duplicate_rows_count > 0:
                warnings.append(
                    f"Found {duplicate_rows_count} duplicate records for key combination {composite_keys}. "
                    "Aggregation (e.g. summing demand per time interval) is recommended before model training."
                )

        # 5. Frequency & Date Continuity (Never assume daily!)
        freq_str, is_regular, date_gaps_count = self._inspect_time_frequency(valid_dates)
        if date_gaps_count > 0 and is_regular:
            warnings.append(
                f"Detected {date_gaps_count} missing time interval(s) based on inferred frequency '{freq_str}'."
            )
        elif not is_regular and len(valid_dates) > 5:
            warnings.append(
                f"Time intervals between records appear irregular (inferred: '{freq_str}'). "
                "Time-series resampling or regular bucket aggregation may be necessary."
            )

        return DataQualityReport(
            is_valid=is_valid,
            row_count=total_rows,
            date_range=date_range,
            detected_frequency=freq_str,
            is_regular_frequency=is_regular,
            missing_values=missing_values,
            missing_percentages=missing_percentages,
            duplicate_rows_count=duplicate_rows_count,
            negative_demand_count=negative_demand_count,
            zero_demand_count=zero_demand_count,
            date_gaps_count=date_gaps_count,
            warnings=warnings,
        )

    def _inspect_time_frequency(
        self, valid_dates: pd.Series
    ) -> Tuple[str, bool, int]:
        """
        Infers the sampling frequency (daily, weekly, monthly, etc.) without assuming daily.
        Uses dominant transition steps to calculate missing interval gaps even when series contains skips.
        """
        if valid_dates.empty or len(valid_dates) < 3:
            return "insufficient_history", False, 0

        unique_sorted = pd.Series(valid_dates.unique()).sort_values().reset_index(drop=True)
        if len(unique_sorted) < 2:
            return "insufficient_history", False, 0

        # Attempt standard pandas frequency inference
        inferred = pd.infer_freq(unique_sorted)
        if inferred:
            try:
                full_grid = pd.date_range(unique_sorted.iloc[0], unique_sorted.iloc[-1], freq=inferred)
                gaps = max(0, len(full_grid) - len(unique_sorted))
                return inferred, True, gaps
            except Exception:
                pass

        # Compute differences in days
        deltas = unique_sorted.diff().dropna().dt.total_seconds() / 86400.0
        if deltas.empty:
            return "insufficient_history", False, 0

        # Use dominant step (mode) and median
        mode_series = deltas.mode()
        dominant_step = float(mode_series.iloc[0]) if not mode_series.empty else float(deltas.median())
        median_delta = float(deltas.median())

        # Select candidate base frequency
        candidate_step = dominant_step if abs(dominant_step - round(dominant_step)) < 0.25 else median_delta

        if 0.85 <= candidate_step <= 1.15:
            freq = "D"
            is_regular = True
        elif 6.5 <= candidate_step <= 7.5:
            freq = "W"
            is_regular = True
        elif 27.0 <= candidate_step <= 32.0:
            freq = "M"
            is_regular = True
        elif 88.0 <= candidate_step <= 93.0:
            freq = "Q"
            is_regular = True
        elif 360.0 <= candidate_step <= 370.0:
            freq = "Y"
            is_regular = True
        elif 0.035 <= candidate_step <= 0.045:
            freq = "h"
            is_regular = True
        else:
            freq = f"irregular (~{candidate_step:.1f}d)"
            is_regular = False

        # Compute missing interval gaps against expected regular grid
        gaps = 0
        if is_regular and freq in ("D", "W", "M", "Q", "Y", "h"):
            try:
                full_grid = pd.date_range(unique_sorted.iloc[0], unique_sorted.iloc[-1], freq=freq)
                gaps = max(0, len(full_grid) - len(unique_sorted))
            except Exception:
                gaps = 0

        return freq, is_regular, gaps


# Global singleton
data_validator = DataValidator()
