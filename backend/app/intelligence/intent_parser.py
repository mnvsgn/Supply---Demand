"""
Intent parser for understanding conversational analytics requests.
Classifies prompts into forecasting, evaluation, data health, trends, seasonality, or inventory sizing.
"""

from typing import Dict, Any


def parse_intent(prompt: str) -> Dict[str, Any]:
    """
    Parses conversational prompt into intent categories and confidence scores.
    """
    p = prompt.lower().strip()

    # 1. Forecasting Intent
    if any(k in p for k in ["forecast", "predict", "projection", "future sales", "future demand"]):
        return {
            "intent": "forecast",
            "confidence": 0.95,
            "requires_dataset": True,
        }

    # 2. Comparative Model Evaluation
    if any(k in p for k in ["compare", "evaluate", "benchmark", "wape", "rmse", "mae", "best model"]):
        return {
            "intent": "evaluate_models",
            "confidence": 0.92,
            "requires_dataset": True,
        }

    # 3. Data Health & Diagnostics
    if any(k in p for k in ["quality", "missing", "gap", "gaps", "duplicates", "diagnostics", "health"]):
        return {
            "intent": "data_quality",
            "confidence": 0.90,
            "requires_dataset": True,
        }

    # 4. Inventory Sizing / Safety Stock
    if any(k in p for k in ["safety stock", "reorder point", "rop", "buffer stock", "lead time"]):
        return {
            "intent": "inventory_insights",
            "confidence": 0.93,
            "requires_dataset": True,
        }

    # 5. Trends & Seasonality
    if any(k in p for k in ["trend", "seasonality", "seasonal", "weekday", "ranking", "pareto"]):
        return {
            "intent": "business_analytics",
            "confidence": 0.88,
            "requires_dataset": True,
        }

    # 6. General Greeting or Help
    if any(k in p for k in ["hello", "hi", "help", "how to", "start"]):
        return {
            "intent": "guidance",
            "confidence": 0.85,
            "requires_dataset": False,
        }

    return {
        "intent": "general_query",
        "confidence": 0.50,
        "requires_dataset": False,
    }
