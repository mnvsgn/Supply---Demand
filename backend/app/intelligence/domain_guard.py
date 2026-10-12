"""
Domain guard module for the Supply and Demand Forecasting application.
Enforces domain boundary constraints and provides the formal out-of-scope response.
"""

import re

FORMAL_DOMAIN_RESPONSE = (
    "I am a specialized **Supply and Demand Forecasting Assistant**. "
    "My domain is strictly focused on supply-chain time-series analytics, historical dataset ingestion, "
    "canonical schema validation, and out-of-sample demand forecasting using statistical and machine learning "
    "models (Naive, Seasonal Naive, Random Forest, and XGBoost).\n\n"
    "I cannot assist with general-purpose programming, trivia, creative writing, or topics outside supply-chain forecasting.\n\n"
    "How can I help you analyze your historical demand dataset today?"
)

OFF_TOPIC_PATTERNS = [
    r'\b(poem|poetry|song|lyrics|story|novel|joke|riddle)\b',
    r'\b(weather in|recipe for|capital of|who is|who was|who won)\b',
    r'\b(write a python script to scrape|build a website|hack|crypto|bitcoin)\b',
    r'\b(write an essay|translate into french|tell me a bedtime)\b',
]

IN_DOMAIN_KEYWORDS = [
    'forecast', 'predict', 'demand', 'supply', 'sales', 'volume', 'horizon',
    'xgboost', 'random forest', 'naive', 'seasonal', 'wape', 'mae', 'rmse',
    'metric', 'dataset', 'csv', 'xlsx', 'data', 'mapping', 'column', 'columns',
    'schema', 'inventory', 'sku', 'product', 'store', 'date', 'frequency',
    'quality', 'gaps', 'duplicates', 'backtest', 'lag', 'trend', 'seasonality',
    'upload', 'evaluate', 'compare', 'model', 'interval', 'bound', 'history',
    'help', 'hello', 'hi', 'start', 'begin', 'how to', 'explain', 'rop', 'safety stock'
]


def is_in_domain(prompt: str) -> bool:
    """
    Evaluates whether a user prompt falls within the supply & demand domain.
    """
    if not prompt or not prompt.strip():
        return True

    p = prompt.lower().strip()

    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, p):
            return False

    has_in_domain = any(kw in p for kw in IN_DOMAIN_KEYWORDS)
    word_count = len(p.split())

    # If long prompt without any domain keywords, consider out of scope
    if word_count > 3 and not has_in_domain:
        return False

    return True


def get_formal_domain_response() -> str:
    """Returns the standardized formal domain response for out-of-scope queries."""
    return FORMAL_DOMAIN_RESPONSE
