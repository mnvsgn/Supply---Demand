"""
Pydantic schemas for temporary session management and conversation tracking.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SessionCreateResponse(BaseModel):
    session_id: str = Field(..., description="Unguessable cryptographically random session identifier")
    created_at: str = Field(..., description="Session initialization timestamp (ISO 8601 UTC)")
    expires_at: str = Field(..., description="Session expiration timestamp (ISO 8601 UTC)")
    ttl_minutes: int = Field(..., description="Total time-to-live in minutes")
    idle_timeout_minutes: int = Field(..., description="Idle timeout in minutes")


class SessionDetailResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    created_at: str = Field(..., description="Session creation timestamp")
    last_accessed_at: str = Field(..., description="Most recent activity timestamp")
    expires_at: str = Field(..., description="Current expiration timestamp")
    is_expired: bool = Field(..., description="Whether the session has expired")
    dataset_count: int = Field(..., description="Number of datasets registered in this session")
    dataset_ids: List[str] = Field(default_factory=list, description="IDs of datasets owned by this session")
    active_dataset_id: Optional[str] = Field(default=None, description="Active dataset identifier")
    conversation_messages_count: int = Field(..., description="Total messages in session conversation history")


class SessionDeleteResponse(BaseModel):
    session_id: str = Field(..., description="ID of deleted session")
    deleted: bool = Field(True, description="Deletion confirmation status")
    purged_datasets_count: int = Field(0, description="Count of datasets and disk files purged")
    message: str = Field(..., description="Status summary message")


class ConversationMessageRequest(BaseModel):
    role: str = Field(..., description="Message author role ('user', 'assistant', or 'system')")
    content: str = Field(..., description="Message text or query")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata (e.g. intent, parameters)")


class ConversationMessageResponse(BaseModel):
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
