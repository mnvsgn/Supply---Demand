"""
Tests for domain validation, intent parsing, and natural language prompt entity extraction.
"""

from app.intelligence.prompt_interpreter import interpret_prompt, extract_horizon


def test_extract_horizon_natural_language():
    """Verify natural language horizon extraction for days, weeks, months, and keywords."""
    # 1-day keywords
    assert extract_horizon("now on this predict next day") == 1
    assert extract_horizon("forecast tomorrow") == 1
    assert extract_horizon("predict 1 day") == 1
    assert extract_horizon("predict one day") == 1
    assert extract_horizon("predict 1d") == 1
    assert extract_horizon("single day demand outlook") == 1

    # Multi-day and word numbers
    assert extract_horizon("predict next 3 days") == 3
    assert extract_horizon("predict three days") == 3
    assert extract_horizon("forecast 5 days") == 5
    assert extract_horizon("predict next 14 days") == 14
    assert extract_horizon("forecast next 30days") == 30

    # Weeks and months
    assert extract_horizon("predict next week") == 7
    assert extract_horizon("forecast next 2 weeks") == 14
    assert extract_horizon("forecast next month") == 30
    assert extract_horizon("forecast 7d") == 7

    # Default fallback
    assert extract_horizon("analyze this dataset") == 14
    assert extract_horizon("") == 14


def test_interpret_prompt_entities():
    """Verify interpret_prompt returns structured entities."""
    res1 = interpret_prompt("now on this predict next day")
    assert res1["horizon"] == 1
    assert res1["model_type"] == "auto"

    res2 = interpret_prompt("forecast next 3 days using xgboost for sku SKU-101")
    assert res2["horizon"] == 3
    assert res2["model_type"] == "xgboost"
    assert res2["product_id"] == "SKU-101"
    assert res2["target_level"] == "product"
