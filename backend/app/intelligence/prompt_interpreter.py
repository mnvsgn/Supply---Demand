"""
Prompt interpreter module for extracting operational entities from natural language text.
Extracts horizon periods, target algorithms, SKU product IDs, lead-time parameters, and service levels.
"""

import re
from typing import Dict, Any, Optional


WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
    "sixty": 60,
    "ninety": 90,
}


def extract_horizon(prompt: str, default_horizon: int = 14) -> int:
    """
    Accurately extracts forecast horizons from user prompts:
    - "next day", "tomorrow", "1 day", "1d" -> 1
    - "next week", "1 week", "7d" -> 7
    - "next 2 weeks", "two weeks" -> 14
    - "next month", "1 month", "30d" -> 30
    - "next quarter" -> 90
    - "next year" -> 365
    - word numbers ("three days", "five days")
    - arbitrary numeric days ("next 3 days", "10 days", "horizon 5")
    """
    if not prompt or not isinstance(prompt, str):
        return default_horizon

    p = prompt.lower().strip()

    # 1. Tomorrow / Single day / Next day
    if re.search(r'\b(tomorrow|next\s+day|following\s+day|single\s+day|one\s+day|1\s*day)\b', p):
        return 1

    # 2. Single week / Next week
    if re.search(r'\b(next\s+week|coming\s+week|one\s+week|1\s*week)\b', p):
        return 7

    # 3. Single month / Next month
    if re.search(r'\b(next\s+month|coming\s+month|one\s+month|1\s*month)\b', p):
        return 30

    # 4. Next quarter
    if re.search(r'\b(next\s+quarter|coming\s+quarter|one\s+quarter|1\s*quarter)\b', p):
        return 90

    # 5. Next year
    if re.search(r'\b(next\s+year|coming\s+year|one\s+year|1\s*year)\b', p):
        return 365

    # 6. Numeric with explicit units (e.g. "30days", "30 days", "2 weeks", "3 months", "7d", "14d")
    num_match = re.search(r'(\d+)\s*[-]?\s*(days?|periods?|weeks?|months?|quarters?|years?|d\b|w\b|m\b)', p)
    if num_match:
        val = int(num_match.group(1))
        unit = num_match.group(2).lower()
        if unit.startswith('w'):
            return max(1, min(val * 7, 365))
        elif unit.startswith('m'):
            return max(1, min(val * 30, 365))
        elif unit.startswith('q'):
            return max(1, min(val * 90, 365))
        elif unit.startswith('y'):
            return max(1, min(val * 365, 365))
        else:
            return max(1, min(val, 365))

    # 7. Word numbers with units (e.g. "three days", "two weeks")
    word_pattern = '|'.join(WORD_NUMBERS.keys())
    word_match = re.search(rf'\b({word_pattern})\s*[-]?\s*(days?|periods?|weeks?|months?)', p)
    if word_match:
        val = WORD_NUMBERS[word_match.group(1)]
        unit = word_match.group(2).lower()
        if 'week' in unit:
            return max(1, min(val * 7, 365))
        elif 'month' in unit:
            return max(1, min(val * 30, 365))
        else:
            return max(1, min(val, 365))

    # 8. General explicit horizon phrasing (e.g. "horizon of 5", "predict 10")
    horizon_match = re.search(r'\b(?:horizon|for|periods?)\s*(?:of)?\s*(\d+)\b', p)
    if horizon_match:
        return max(1, min(int(horizon_match.group(1)), 365))

    return default_horizon


def interpret_prompt(prompt: str) -> Dict[str, Any]:
    """
    Extracts structured forecasting and analytics arguments from a user prompt.
    """
    p = prompt.lower().strip()
    entities: Dict[str, Any] = {}

    # 1. Horizon extraction
    entities["horizon"] = extract_horizon(p, default_horizon=14)

    # 2. Model type selection
    if "xgboost" in p:
        entities["model_type"] = "xgboost"
    elif "random forest" in p:
        entities["model_type"] = "random_forest"
    elif "seasonal naive" in p:
        entities["model_type"] = "seasonal_naive"
    elif "naive" in p:
        entities["model_type"] = "naive"
    else:
        entities["model_type"] = "auto"

    # 3. Product / SKU extraction (e.g., 'sku-1', 'product A', 'item #104')
    sku_match = re.search(r'(?:sku|product|item)\s*(?:id|#)?[:\s]*([a-zA-Z0-9_\-]+)', p)
    if sku_match:
        entities["product_id"] = sku_match.group(1).upper()
        entities["target_level"] = "product"
    else:
        entities["product_id"] = None
        entities["target_level"] = "aggregate"

    # 4. Lead time extraction for inventory (e.g. '7 days lead', 'lead time of 10')
    lead_match = re.search(r'(\d+)\s*(?:days?|periods?)?\s*lead', p) or re.search(r'lead\s*(?:time)?\s*(?:of)?\s*(\d+)', p)
    if lead_match:
        entities["lead_time_days"] = int(lead_match.group(1))
    else:
        entities["lead_time_days"] = None

    # 5. Service level extraction (e.g. '95%', '99% service level')
    service_match = re.search(r'(\d{2})%\s*(?:service|cycle)?', p)
    if service_match:
        entities["service_level"] = float(service_match.group(1)) / 100.0
    else:
        entities["service_level"] = 0.95

    return entities
