"""
Prompt interpreter module for extracting operational entities from natural language text.
Extracts horizon periods, target algorithms, SKU product IDs, lead-time parameters, and service levels.
"""

import re
from typing import Dict, Any, Optional


def interpret_prompt(prompt: str) -> Dict[str, Any]:
    """
    Extracts structured forecasting and analytics arguments from a user prompt.
    """
    p = prompt.lower().strip()
    entities: Dict[str, Any] = {}

    # 1. Horizon extraction (e.g., '14 days', '30 periods', '4 weeks', '2 months')
    horizon_match = re.search(r'(\d+)\s*(days?|periods?|weeks?|months?)', p)
    if horizon_match:
        val = int(horizon_match.group(1))
        unit = horizon_match.group(2)
        if "week" in unit:
            entities["horizon"] = val * 7
        elif "month" in unit:
            entities["horizon"] = val * 30
        else:
            entities["horizon"] = val
    else:
        entities["horizon"] = 14

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
