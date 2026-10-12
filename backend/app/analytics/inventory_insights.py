"""
Inventory insights and correlation analysis module.
Calculates grounded safety stock and reorder point estimates with explicit assumptions,
and computes empirical price/promotional correlations with causality disclaimers.
"""

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd


def analyze_inventory_insights(
    df: pd.DataFrame,
    lead_time_days: Optional[int] = None,
    service_level: float = 0.95,
    current_inventory: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes grounded Safety Stock and Reorder Point (ROP) estimates.
    Strictly requires lead-time parameter; does not fabricate planning estimates without it.
    """
    if lead_time_days is None or lead_time_days <= 0:
        return {
            "is_available": False,
            "reason": (
                "Safety stock and reorder point calculations require specifying a supplier lead time (in days). "
                "Provide lead time (e.g., 'lead time of 7 days') to compute grounded buffer estimates."
            ),
            "safety_stock_estimate": None,
            "reorder_point_estimate": None,
            "assumptions": None,
            "stock_status": None,
        }

    if df.empty or "demand" not in df.columns:
        return {
            "is_available": False,
            "reason": "Dataset contains insufficient demand records to calculate demand variance.",
            "safety_stock_estimate": None,
            "reorder_point_estimate": None,
            "assumptions": None,
            "stock_status": None,
        }

    demands = df["demand"].dropna().values
    if len(demands) < 7:
        return {
            "is_available": False,
            "reason": "At least 7 historical demand observations are required to estimate variance.",
            "safety_stock_estimate": None,
            "reorder_point_estimate": None,
            "assumptions": None,
            "stock_status": None,
        }

    daily_mean = float(np.mean(demands))
    daily_std = float(np.std(demands, ddof=1)) if len(demands) > 1 else 0.0

    # Z-scores for standard cycle service levels
    z_table = {
        0.80: 0.84,
        0.85: 1.04,
        0.90: 1.28,
        0.95: 1.65,
        0.98: 2.05,
        0.99: 2.33,
    }
    z_score = z_table.get(round(service_level, 2), 1.65)

    # Standard inventory formula: SS = Z * sigma_d * sqrt(L)
    safety_stock = z_score * daily_std * np.sqrt(lead_time_days)
    # Reorder point: ROP = (mean_d * L) + SS
    lead_time_demand = daily_mean * lead_time_days
    rop = lead_time_demand + safety_stock

    stock_status = "stock_adequate"
    if current_inventory is not None:
        if current_inventory <= rop:
            stock_status = "reorder_recommended"
        else:
            stock_status = "stock_adequate"

    assumptions = (
        f"Planning estimate calculated under normal distribution assumptions with "
        f"{int(service_level * 100)}% cycle service level (Z={z_score}), "
        f"deterministic {lead_time_days}-day lead time, and empirical daily standard deviation of {round(daily_std, 1)} units. "
        f"Real supply chains may experience stochastic supplier delays or supply disruptions not captured in historical demand."
    )

    return {
        "is_available": True,
        "lead_time_periods": lead_time_days,
        "service_level": service_level,
        "z_score": z_score,
        "expected_lead_time_demand": round(lead_time_demand, 1),
        "safety_stock_estimate": round(safety_stock, 1),
        "reorder_point_estimate": round(rop, 1),
        "daily_mean_demand": round(daily_mean, 2),
        "daily_std_demand": round(daily_std, 2),
        "current_inventory": current_inventory,
        "stock_status": stock_status,
        "assumptions": assumptions,
    }


def analyze_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes Pearson correlations between demand and auxiliary factors (promotions, price).
    Strictly includes empiricism and causality disclaimers.
    """
    correlations = {}

    if "demand" not in df.columns or len(df) < 5:
        return correlations

    # Promotional correlation
    if "promotion" in df.columns and df["promotion"].nunique() > 1:
        corr_val = float(df["demand"].corr(df["promotion"]))
        promo_mean = df[df["promotion"] == 1]["demand"].mean()
        non_promo_mean = df[df["promotion"] == 0]["demand"].mean()
        lift_pct = 0.0
        if non_promo_mean > 0 and not np.isnan(promo_mean):
            lift_pct = ((promo_mean - non_promo_mean) / non_promo_mean) * 100.0

        correlations["promotion"] = {
            "correlation": round(corr_val, 3) if not np.isnan(corr_val) else 0.0,
            "promotional_lift_pct": round(lift_pct, 1),
            "disclaimer": (
                "Does not prove promotional causality. "
                "Observed demand shifts may be co-influenced by seasonality, stock availability, or unobserved market factors."
            ),
        }

    # Price correlation
    if "price" in df.columns and df["price"].nunique() > 1:
        corr_val = float(df["demand"].corr(df["price"]))
        correlations["price"] = {
            "correlation": round(corr_val, 3) if not np.isnan(corr_val) else 0.0,
            "disclaimer": (
                "Price elasticity cannot be confirmed without controlled randomized pricing experiments or instrumental variables."
            ),
        }

    return correlations
