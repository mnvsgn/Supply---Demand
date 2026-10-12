"""
Pydantic schemas for intent representation and prompt analysis.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class IntentAnalysis(BaseModel):
    is_in_domain: bool = Field(..., description="Whether the query is within domain boundaries")
    intent: str = Field(..., description="Classified intent (e.g. forecast, evaluate_models, data_quality, etc.)")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted parameters (horizon, sku, lead_time)")
    formal_response: Optional[str] = Field(default=None, description="Formal response if out-of-scope")
