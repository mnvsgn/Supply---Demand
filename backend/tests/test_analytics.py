"""
Unit tests for BusinessAnalyticsService and analytics API endpoint.
Tests trends, product rankings, seasonality, safety stock estimates, and API responses.
"""

import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

from app.analytics.insights import business_analytics
from app.main import app


@pytest.fixture
def sample_sales_df():
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    # Linear upward trend with weekend lift
    data = []
    for i, d in enumerate(dates):
        base = 50 + (i * 2)
        weekend_lift = 20 if d.dayofweek in (5, 6) else 0
        data.append({
            "date": d,
            "demand": base + weekend_lift,
            "product_id": "SKU-A" if i % 2 == 0 else "SKU-B",
            "promotion": 1 if i % 5 == 0 else 0,
            "price": 9.99,
        })
    return pd.DataFrame(data)


def test_sales_trend_calculation(sample_sales_df):
    trend = business_analytics.analyze_sales_trend(sample_sales_df)
    assert trend["direction"] == "upward"
    assert trend["slope"] > 0
    assert trend["growth_rate_pct"] > 0
    assert trend["total_periods"] == 30
    assert trend["total_volume"] > 0


def test_product_rankings_pareto(sample_sales_df):
    rankings = business_analytics.analyze_product_rankings(sample_sales_df)
    assert rankings is not None
    assert len(rankings) == 2
    assert rankings[0]["rank"] == 1
    assert rankings[1]["rank"] == 2
    # Sum of volume shares should be ~100%
    total_share = sum(r["volume_share_pct"] for r in rankings)
    assert abs(total_share - 100.0) < 0.5


def test_seasonality_indices(sample_sales_df):
    seasonality = business_analytics.analyze_seasonality(sample_sales_df)
    assert seasonality["has_seasonality"] is True
    assert seasonality["peak_day"] in ("Saturday", "Sunday")
    assert seasonality["weekend_lift_pct"] > 0
    assert "Monday" in seasonality["day_of_week_indices"]


def test_inventory_insights_missing_lead_time_handling(sample_sales_df):
    """Safety stock must not be computed without lead-time parameter."""
    res = business_analytics.analyze_inventory_insights(sample_sales_df, lead_time_days=None)
    assert res["is_available"] is False
    assert "require specifying a supplier lead time" in res["reason"]


def test_inventory_insights_with_parameters(sample_sales_df):
    res = business_analytics.analyze_inventory_insights(
        sample_sales_df,
        lead_time_days=7,
        service_level=0.95,
        current_inventory=500.0,
    )
    assert res["is_available"] is True
    assert res["lead_time_periods"] == 7
    assert res["safety_stock_estimate"] > 0
    assert res["reorder_point_estimate"] > res["safety_stock_estimate"]
    assert "Planning estimate calculated under" in res["assumptions"]
    assert res["stock_status"] in ("reorder_recommended", "stock_adequate")


def test_correlations_disclaimer(sample_sales_df):
    corrs = business_analytics.analyze_correlations(sample_sales_df)
    assert "promotion" in corrs
    assert "disclaimer" in corrs["promotion"]
    assert "Does not prove promotional causality" in corrs["promotion"]["disclaimer"]


def test_api_analytics_endpoint():
    client = TestClient(app)
    # Upload test dataset
    csv_content = (
        "date,demand,product_id\n"
        + "\n".join([f"2024-01-{i:02d},{100 + i},SKU-1" for i in range(1, 20)])
    )
    up_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test_analytics.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    assert up_res.status_code == 201
    dataset_id = up_res.json()["dataset_id"]

    # Map dataset
    map_res = client.post(
        f"/api/v1/datasets/{dataset_id}/mapping",
        json={"date_column": "date", "demand_column": "demand", "product_id_column": "product_id"},
    )
    assert map_res.status_code == 200

    # Call analytics endpoint
    res = client.post(
        f"/api/v1/datasets/{dataset_id}/analytics",
        json={"lead_time_days": 5, "service_level": 0.95},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["dataset_id"] == dataset_id
    assert "trend" in data
    assert data["inventory_insights"]["is_available"] is True
    assert data["inventory_insights"]["lead_time_periods"] == 5
