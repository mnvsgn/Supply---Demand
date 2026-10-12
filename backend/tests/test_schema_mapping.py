import io
import pytest
from fastapi.testclient import TestClient
from app.data_processing.preprocessing import preprocessing_pipeline
from app.data_processing.schema_detector import schema_detector
from app.main import app
from app.services.dataset_registry import dataset_registry

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_registry():
    """Ensure a clean dataset registry for each test."""
    dataset_registry.clear()
    yield
    dataset_registry.clear()


# ==============================================================================
# Helper functions to build benchmark datasets
# ==============================================================================

def create_walmart_dataset() -> bytes:
    """Walmart retail benchmark: Store, Dept, Date, Weekly_Sales, IsHoliday."""
    csv_text = """Store,Dept,Date,Weekly_Sales,IsHoliday
1,1,2010-02-05,24924.50,0
1,1,2010-02-12,46039.49,1
1,1,2010-02-19,41595.55,0
1,1,2010-02-26,19403.54,0
1,1,2010-03-05,21827.90,0
1,2,2010-02-05,50605.27,0
1,2,2010-02-12,44682.74,1
1,2,2010-02-19,42085.58,0
1,2,2010-02-26,47297.29,0
1,2,2010-03-05,47128.89,0
"""
    return csv_text.strip().encode("utf-8")


def create_rossmann_dataset() -> bytes:
    """Rossmann store benchmark: Date, Store, DayOfWeek, Sales, Customers, Open, Promo, StateHoliday."""
    csv_text = """Date,Store,DayOfWeek,Sales,Customers,Open,Promo,StateHoliday
2015-07-31,1,5,5263,555,1,1,0
2015-07-30,1,4,5020,546,1,1,0
2015-07-29,1,3,4782,523,1,1,0
2015-07-28,1,2,5011,560,1,1,0
2015-07-27,1,1,6102,612,1,1,0
2015-07-26,1,7,0,0,0,0,0
2015-07-25,1,6,4364,500,1,0,0
"""
    return csv_text.strip().encode("utf-8")


def create_m5_dataset() -> bytes:
    """M5 forecasting benchmark: date, item_id, store_id, units_sold, sell_price, is_event."""
    csv_text = """date,item_id,store_id,units_sold,sell_price,is_event
2011-01-29,HOBBIES_1_001,CA_1,0,9.58,0
2011-01-30,HOBBIES_1_001,CA_1,0,9.58,0
2011-01-31,HOBBIES_1_001,CA_1,0,9.58,0
2011-02-01,HOBBIES_1_001,CA_1,0,9.58,0
2011-02-02,HOBBIES_1_001,CA_1,1,9.58,0
2011-02-03,HOBBIES_1_001,CA_1,2,9.58,0
2011-02-04,HOBBIES_1_001,CA_1,0,9.58,0
2011-02-05,HOBBIES_1_001,CA_1,1,9.58,1
2011-02-06,HOBBIES_1_001,CA_1,1,9.58,1
"""
    return csv_text.strip().encode("utf-8")


def create_ambiguous_revenue_dataset() -> bytes:
    """Dataset with both physical units sold and monetary sales revenue."""
    csv_text = """date,sku,units_sold,sales_revenue,unit_price
2023-01-01,SKU-100,50,999.50,19.99
2023-01-02,SKU-100,45,899.55,19.99
2023-01-03,SKU-100,60,1199.40,19.99
2023-01-04,SKU-100,70,1399.30,19.99
"""
    return csv_text.strip().encode("utf-8")


# ==============================================================================
# Unit & Integration Tests
# ==============================================================================

def test_walmart_schema_detection_and_mapping():
    """Verify detection, weekly frequency inference, and mapping confirmation on Walmart dataset."""
    files = {"file": ("walmart_sales.csv", create_walmart_dataset(), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201

    data = upload_res.json()
    dataset_id = data["dataset_id"]
    suggested = data["suggested_mapping"]

    # Verify detection accurately identified Walmart schema fields
    assert suggested["date"] == "Date"
    assert suggested["demand"] == "Weekly_Sales"
    assert suggested["store_id"] == "Store"
    assert suggested["product_id"] == "Dept"
    assert suggested["promotion"] == "IsHoliday"

    # Confirm the mapping via POST /datasets/{id}/mapping
    mapping_payload = {
        "date_column": "Date",
        "demand_column": "Weekly_Sales",
        "store_id_column": "Store",
        "product_id_column": "Dept",
        "promotion_column": "IsHoliday",
    }
    map_res = client.post(f"/api/v1/datasets/{dataset_id}/mapping", json=mapping_payload)
    assert map_res.status_code == 200

    map_data = map_res.json()
    assert map_data["is_valid"] is True
    assert map_data["mapped_schema"]["date"] == "Date"
    assert map_data["mapped_schema"]["demand"] == "Weekly_Sales"

    # Verify Weekly frequency was detected correctly without assuming daily
    quality = map_data["data_quality"]
    assert quality["detected_frequency"].startswith("W")
    assert quality["is_regular_frequency"] is True
    assert quality["negative_demand_count"] == 0

    # Verify summary capabilities
    summary = map_data["summary"]
    assert summary["support_aggregate_forecast"] is True
    assert summary["support_product_forecast"] is True
    assert summary["unique_products_count"] == 2
    assert summary["unique_stores_count"] == 1


def test_rossmann_schema_detection_and_mapping():
    """Verify Rossmann store schema detection and normalization."""
    files = {"file": ("rossmann.csv", create_rossmann_dataset(), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201

    data = upload_res.json()
    dataset_id = data["dataset_id"]
    suggested = data["suggested_mapping"]

    assert suggested["date"] == "Date"
    assert suggested["demand"] == "Sales"
    assert suggested["store_id"] == "Store"
    assert suggested["promotion"] == "Promo"

    mapping_payload = {
        "date_column": "Date",
        "demand_column": "Sales",
        "store_id_column": "Store",
        "promotion_column": "Promo",
    }
    map_res = client.post(f"/api/v1/datasets/{dataset_id}/mapping", json=mapping_payload)
    assert map_res.status_code == 200

    map_data = map_res.json()
    assert map_data["mapped_schema"]["demand"] == "Sales"
    assert map_data["data_quality"]["detected_frequency"] == "D"
    assert len(map_data["normalized_preview"]) > 0


def test_m5_schema_detection_and_mapping():
    """Verify M5 forecasting competition schema detection with all 6 canonical fields."""
    files = {"file": ("m5_data.csv", create_m5_dataset(), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201

    data = upload_res.json()
    dataset_id = data["dataset_id"]
    suggested = data["suggested_mapping"]

    assert suggested["date"] == "date"
    assert suggested["demand"] == "units_sold"
    assert suggested["product_id"] == "item_id"
    assert suggested["store_id"] == "store_id"
    assert suggested["price"] == "sell_price"
    assert suggested["promotion"] == "is_event"

    mapping_payload = {
        "date_column": "date",
        "demand_column": "units_sold",
        "product_id_column": "item_id",
        "store_id_column": "store_id",
        "price_column": "sell_price",
        "promotion_column": "is_event",
    }
    map_res = client.post(f"/api/v1/datasets/{dataset_id}/mapping", json=mapping_payload)
    assert map_res.status_code == 200

    map_data = map_res.json()
    assert map_data["mapped_schema"]["price"] == "sell_price"
    assert map_data["mapped_schema"]["promotion"] == "is_event"


def test_ambiguous_revenue_vs_units_sold_detection():
    """Verify that when both units and sales revenue exist, units is preferred and warnings are raised."""
    files = {"file": ("ambiguous.csv", create_ambiguous_revenue_dataset(), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201

    data = upload_res.json()
    # Should flag ambiguity warnings
    assert len(data["ambiguity_warnings"]) > 0
    assert any("ambiguity" in w.lower() for w in data["ambiguity_warnings"])
    assert data["requires_confirmation"] is True

    # Demand should default to units_sold rather than sales_revenue
    assert data["suggested_mapping"]["demand"] == "units_sold"


def test_missing_values_and_negative_demand_diagnostics():
    """Verify that missing values and negative returns are diagnosed without inventing data."""
    csv_text = """date,sku,units_sold
2023-01-01,SKU-A,100
2023-01-02,SKU-A,-5
2023-01-03,SKU-A,0
2023-01-04,,80
2023-01-05,SKU-A,
"""
    files = {"file": ("dirty.csv", csv_text.strip().encode("utf-8"), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    map_payload = {
        "date_column": "date",
        "demand_column": "units_sold",
        "product_id_column": "sku",
    }
    map_res = client.post(f"/api/v1/datasets/{dataset_id}/mapping", json=map_payload)
    assert map_res.status_code == 200

    quality = map_res.json()["data_quality"]
    assert quality["negative_demand_count"] == 1
    assert quality["zero_demand_count"] == 1
    assert quality["missing_values"]["units_sold"] == 1
    assert quality["missing_values"]["sku"] == 1
    assert any("negative" in w.lower() for w in quality["warnings"])


def test_duplicate_records_detection():
    """Verify that duplicate (date, product) timestamps are detected and warned."""
    csv_text = """date,sku,units_sold
2023-01-01,SKU-1,50
2023-01-01,SKU-1,20
2023-01-02,SKU-1,45
2023-01-03,SKU-1,60
"""
    files = {"file": ("duplicates.csv", csv_text.strip().encode("utf-8"), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    map_payload = {
        "date_column": "date",
        "demand_column": "units_sold",
        "product_id_column": "sku",
    }
    map_res = client.post(f"/api/v1/datasets/{dataset_id}/mapping", json=map_payload)
    assert map_res.status_code == 200

    quality = map_res.json()["data_quality"]
    assert quality["duplicate_rows_count"] > 0
    assert any("duplicate" in w.lower() for w in quality["warnings"])


def test_date_gap_detection():
    """Verify that missing dates in an otherwise daily series are detected."""
    # Jan 1, 2, 5 (missing Jan 3, 4 -> 2 gaps)
    csv_text = """date,units_sold
2023-01-01,50
2023-01-02,45
2023-01-05,60
"""
    files = {"file": ("gaps.csv", csv_text.strip().encode("utf-8"), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    map_payload = {
        "date_column": "date",
        "demand_column": "units_sold",
    }
    map_res = client.post(f"/api/v1/datasets/{dataset_id}/mapping", json=map_payload)
    assert map_res.status_code == 200

    quality = map_res.json()["data_quality"]
    assert quality["date_gaps_count"] == 2
    assert any("missing time interval" in w.lower() for w in quality["warnings"])


def test_invalid_mapping_rejected():
    """Verify validation errors when mapping non-existent columns or reusing columns."""
    csv_text = "date,units_sold\n2023-01-01,10\n2023-01-02,20\n"
    files = {"file": ("test.csv", csv_text.encode("utf-8"), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    # Column that doesn't exist
    bad_payload = {"date_column": "date", "demand_column": "non_existent_col"}
    res = client.post(f"/api/v1/datasets/{dataset_id}/mapping", json=bad_payload)
    assert res.status_code == 422
    assert res.json()["code"] == "COLUMN_NOT_FOUND"

    # Duplicate column mapping (mapping 'date' as both date and demand)
    dup_payload = {"date_column": "date", "demand_column": "date"}
    dup_res = client.post(f"/api/v1/datasets/{dataset_id}/mapping", json=dup_payload)
    assert dup_res.status_code == 422
    assert dup_res.json()["code"] == "DUPLICATE_COLUMN_MAPPING"


def test_preprocessing_aggregate_and_product_series():
    """Verify preprocessing pipeline extracts aggregate and product-level time series."""
    import pandas as pd

    df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-01", "2023-01-02", "2023-01-02"],
        "demand": [10.0, 20.0, 15.0, 25.0],
        "product_id": ["P1", "P2", "P1", "P2"],
    })

    normalized_df, summary = preprocessing_pipeline.normalize(df, inferred_freq="D")
    assert summary.total_demand == 70.0
    assert summary.unique_products_count == 2

    # Aggregate series (summed across products)
    agg_series = preprocessing_pipeline.get_aggregate_demand_series(normalized_df)
    assert len(agg_series) == 2
    assert agg_series.loc[agg_series["date"] == pd.Timestamp("2023-01-01"), "demand"].values[0] == 30.0
    assert agg_series.loc[agg_series["date"] == pd.Timestamp("2023-01-02"), "demand"].values[0] == 40.0

    # Product series for P1
    p1_series = preprocessing_pipeline.get_product_demand_series(normalized_df, "P1")
    assert len(p1_series) == 2
    assert p1_series.loc[p1_series["date"] == pd.Timestamp("2023-01-01"), "demand"].values[0] == 10.0
    assert p1_series.loc[p1_series["date"] == pd.Timestamp("2023-01-02"), "demand"].values[0] == 15.0


def test_dataset_mapping_alias_support():
    """Verify that mapping request accepts 'date' and 'demand' aliases seamlessly."""
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.csv", b"date,demand\n2023-01-01,10\n2023-01-02,20\n", "text/csv")},
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["dataset_id"]

    # Post using aliases 'date' and 'demand' rather than 'date_column' and 'demand_column'
    alias_payload = {"date": "date", "demand": "demand"}
    res = client.post(f"/api/v1/datasets/{dataset_id}/mapping", json=alias_payload)
    assert res.status_code == 200
    assert res.json()["is_valid"] is True
    assert res.json()["mapped_schema"]["date"] == "date"
    assert res.json()["mapped_schema"]["demand"] == "demand"
