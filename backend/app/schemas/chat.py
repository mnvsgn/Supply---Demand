"""
Pydantic schemas for chat interactions and conversational API responses.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatPromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt or analytical request")
    dataset_id: Optional[str] = Field(default=None, description="Active dataset identifier in session")
    session_id: Optional[str] = Field(default=None, description="Client session identifier")


class ChatResponse(BaseModel):
    message: str = Field(..., description="Assistant response text")
    message_type: str = Field(
        default="text",
        description="'text' | 'forecast' | 'evaluation' | 'quality_warning' | 'clarification' | 'analytics' | 'error'",
    )
    data: Optional[Any] = Field(default=None, description="Structured payload matching message_type")
    intent: Optional[str] = Field(default=None, description="Detected query intent")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Response ISO timestamp",
    )
