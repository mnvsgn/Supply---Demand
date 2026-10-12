"""
Response builder module for generating consistent, grounded assistant responses.
"""

from typing import Dict, Any, Optional


def build_forecast_response_text(
    model_name: str,
    horizon: int,
    points_count: int,
    product_id: Optional[str] = None,
) -> str:
    """Build narrative text accompanying forecast outputs."""
    target_str = f"for SKU **{product_id}**" if product_id else "for aggregate total demand"
    return (
        f"Demand projections generated {target_str} across the next **{points_count} periods**.\n"
        "Our predictive engine analyzed your historical demand patterns, seasonal cycles, and run-rates to generate this planning outlook.\n"
        "Review the projected trajectory, peak demand periods, and planning schedule below:"
    )


def build_evaluation_response_text(
    winning_model: str,
    metric_name: str = "WAPE",
) -> str:
    """Build narrative text accompanying model evaluation results."""
    return (
        "Forecasting methodology evaluation complete! We analyzed candidate approaches against your historical demand.\n"
        f"The recommended forecasting method is **{winning_model}**, providing the highest historical reliability and lowest planning variance. "
        "Review the comparison table below:"
    )


def build_data_quality_response_text(
    filename: str,
    total_records: int,
    frequency: str,
    gap_count: int = 0,
    negative_count: int = 0,
    duplicate_count: int = 0,
) -> str:
    """Build narrative summary for data health checks."""
    gaps_str = f"⚠️ {gap_count} gaps detected" if gap_count > 0 else "✅ None (continuous time grid)"
    neg_str = f"⚠️ {negative_count} negative rows" if negative_count > 0 else "✅ None"
    dup_str = f"⚠️ {duplicate_count} duplicate timestamps" if duplicate_count > 0 else "✅ None"

    return (
        f"### Dataset Quality & Diagnostics Report\n"
        f"• **Filename:** {filename}\n"
        f"• **Total Usable Records:** {total_records:,}\n"
        f"• **Detected Frequency:** {frequency}\n"
        f"• **Missing Date Intervals:** {gaps_str}\n"
        f"• **Negative Demand Observations:** {neg_str}\n"
        f"• **Duplicate Timestamps:** {dup_str}"
    )


def build_analytics_response_text() -> str:
    """Build narrative text accompanying business insights."""
    return (
        "Business analytics generated directly from validated historical observations. "
        "Review empirical sales trends, calendar seasonality, product rankings, and inventory sizing below:"
    )
