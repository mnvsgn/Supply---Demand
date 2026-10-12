"""
Session service for temporary session management.
Coordinates session creation, retrieval, ownership verification, and expiration.
Re-exports and wraps session_manager.
"""

from typing import Any, Dict, List, Optional
from app.services.session_manager import (
    BaseSessionStore,
    InMemorySessionStore,
    SessionRecord,
    ConversationMessage,
    session_manager,
)

__all__ = [
    "BaseSessionStore",
    "InMemorySessionStore",
    "SessionRecord",
    "ConversationMessage",
    "session_manager",
]
