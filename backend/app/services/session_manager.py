"""
Temporary session management and storage abstraction for the no-login application architecture.

Multi-Worker Deployment Notice & Architectural Limitations:
-----------------------------------------------------------
This in-memory session registry holds session state and memory pointers in local process RAM.
In production environments operating across multiple worker processes (e.g. Uvicorn/Gunicorn
with `workers > 1`) or distributed horizontal replicas (Kubernetes pods behind a load balancer):
1. State is not shared across processes without an external coordination layer. A user whose
   session was created on Worker 1 will receive a 404/expired error if their next HTTP request
   is routed to Worker 2, unless session affinity ('sticky sessions') is configured on the reverse proxy.
2. Process restarts, deployments, or worker recycling will evict all active in-memory sessions.
3. For enterprise or distributed scale, replace `InMemorySessionStore` with a shared backend
   implementing `BaseSessionStore` (e.g. RedisSessionStore for metadata and S3/MinIO for files)
   without modifying application forecasting or schema logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
import shutil
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.errors import NotFoundException, SessionExpiredException
from app.core.logging import logger


@dataclass
class ConversationMessage:
    """Represents a single query or response in the session chat history."""
    role: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SessionRecord:
    """Container for temporary session metadata and associated resources."""
    session_id: str
    created_at: datetime
    last_accessed_at: datetime
    expires_at: datetime
    storage_dir: Path
    dataset_ids: List[str] = field(default_factory=list)
    active_dataset_id: Optional[str] = None
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def touch(self, idle_timeout_minutes: int) -> None:
        """Refreshes last accessed time and extends expiration window."""
        now = datetime.now(timezone.utc)
        self.last_accessed_at = now
        self.expires_at = now + timedelta(minutes=idle_timeout_minutes)

    def to_dict(self) -> Dict[str, Any]:
        """Returns safe user-facing session metadata without raw data."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_expired": self.is_expired,
            "dataset_count": len(self.dataset_ids),
            "dataset_ids": list(self.dataset_ids),
            "active_dataset_id": self.active_dataset_id,
            "conversation_messages_count": len(self.conversation_history),
        }


class BaseSessionStore(ABC):
    """Abstract interface defining the session store contract for modular storage."""

    @abstractmethod
    def create_session(
        self, ttl_minutes: Optional[int] = None, idle_timeout_minutes: Optional[int] = None
    ) -> SessionRecord:
        pass

    @abstractmethod
    def get_session(self, session_id: str, touch: bool = True) -> Optional[SessionRecord]:
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        pass

    @abstractmethod
    def attach_dataset(self, session_id: str, dataset_id: str) -> None:
        pass

    @abstractmethod
    def verify_dataset_ownership(self, session_id: str, dataset_id: str) -> bool:
        pass


class InMemorySessionStore(BaseSessionStore):
    """
    Lightweight, thread-safe in-memory session registry with isolated filesystem directories.
    Enforces dataset isolation and unguessable 256-bit entropy session tokens.
    """

    def __init__(self, base_storage_dir: Optional[str] = None):
        self.base_storage_dir = Path(
            base_storage_dir or settings.SESSION_STORAGE_DIR
        ).resolve()
        self.base_storage_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, SessionRecord] = {}

    def _generate_unguessable_session_id(self) -> str:
        """
        Generates a cryptographically strong, URL-safe random session identifier (256 bits entropy).
        Unguessable and immune to brute-force enumerations.
        """
        return f"sess_{secrets.token_urlsafe(32)}"

    def create_session(
        self,
        ttl_minutes: Optional[int] = None,
        idle_timeout_minutes: Optional[int] = None,
    ) -> SessionRecord:
        """Creates and registers a new isolated session."""
        self.cleanup_expired()

        session_id = self._generate_unguessable_session_id()
        now = datetime.now(timezone.utc)
        ttl = ttl_minutes or settings.SESSION_EXPIRY_MINUTES
        expires_at = now + timedelta(minutes=ttl)

        # Isolated directory for this session's files and artifacts
        session_dir = (self.base_storage_dir / session_id).resolve()
        # Path traversal guard
        if not str(session_dir).startswith(str(self.base_storage_dir)):
            raise ValueError("Invalid storage path generated.")
        session_dir.mkdir(parents=True, exist_ok=True)

        record = SessionRecord(
            session_id=session_id,
            created_at=now,
            last_accessed_at=now,
            expires_at=expires_at,
            storage_dir=session_dir,
        )

        self._sessions[session_id] = record
        # Never log raw user data; log only session token prefix
        logger.info(f"Initialized new temporary session {session_id[:12]}*** (TTL: {ttl}m)")
        return record

    def get_session(self, session_id: str, touch: bool = True) -> Optional[SessionRecord]:
        """
        Retrieves active session if valid.
        If expired, deletes disk artifacts and evicts session.
        """
        record = self._sessions.get(session_id)
        if not record:
            return None

        now = datetime.now(timezone.utc)
        if now > record.expires_at:
            logger.info(f"Session {session_id[:12]}*** expired; purging associated resources.")
            self.delete_session(session_id)
            return None

        if touch:
            record.touch(settings.SESSION_IDLE_TIMEOUT_MINUTES)

        return record

    def delete_session(self, session_id: str) -> bool:
        """
        Terminates session, removes all owned datasets, and purges its storage directory.
        """
        record = self._sessions.pop(session_id, None)
        if not record:
            return False

        # 1. Purge datasets from DatasetRegistry
        from app.services.dataset_registry import dataset_registry
        for did in record.dataset_ids:
            try:
                dataset_registry.delete_dataset(did)
            except Exception as e:
                logger.error(f"Error purging dataset {did} during session deletion: {e}")

        # 2. Recursively delete isolated session folder on disk
        if record.storage_dir.exists():
            try:
                shutil.rmtree(record.storage_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Failed to delete session directory {record.storage_dir}: {e}")

        logger.info(f"Deleted session {session_id[:12]}*** and purged disk artifacts.")
        return True

    def cleanup_expired(self) -> int:
        """Scans and evicts all expired sessions and their disk directories."""
        now = datetime.now(timezone.utc)
        expired_ids = [
            sid for sid, rec in self._sessions.items() if now > rec.expires_at
        ]

        cleaned_count = 0
        for sid in expired_ids:
            if self.delete_session(sid):
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired session(s).")
        return cleaned_count

    def attach_dataset(self, session_id: str, dataset_id: str) -> None:
        """Associates an uploaded dataset with a session, setting it active if first."""
        session = self.get_session(session_id, touch=True)
        if not session:
            raise SessionExpiredException(
                f"Session '{session_id}' not found or expired.",
                code="SESSION_NOT_FOUND",
            )

        if dataset_id not in session.dataset_ids:
            session.dataset_ids.append(dataset_id)

        if session.active_dataset_id is None:
            session.active_dataset_id = dataset_id

        logger.info(
            f"Associated dataset {dataset_id} with session {session_id[:12]}*** "
            f"(Total: {len(session.dataset_ids)})"
        )

    def verify_dataset_ownership(self, session_id: str, dataset_id: str) -> bool:
        """
        Ensures strict session boundary isolation.
        Raises NotFoundException if the dataset does not belong to the requested session.
        Guarantees that User A cannot guess or change dataset_id to view User B's dataset.
        """
        session = self.get_session(session_id, touch=True)
        if not session:
            raise SessionExpiredException(
                f"Session '{session_id}' does not exist or has expired.",
                code="SESSION_EXPIRED",
            )

        if dataset_id not in session.dataset_ids:
            # We raise NotFoundException rather than 403 to prevent ID-enumeration side channels
            raise NotFoundException(
                message=f"Dataset '{dataset_id}' not found in active session.",
                code="DATASET_NOT_FOUND_IN_SESSION",
            )

        return True

    def append_conversation_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """Appends a message to the session's conversation history."""
        session = self.get_session(session_id, touch=True)
        if not session:
            raise SessionExpiredException(
                f"Session '{session_id}' not found or expired.",
                code="SESSION_NOT_FOUND",
            )

        msg = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        session.conversation_history.append(msg)
        return msg

    def get_conversation(self, session_id: str) -> List[ConversationMessage]:
        """Returns conversation messages for the session."""
        session = self.get_session(session_id, touch=True)
        if not session:
            raise SessionExpiredException(
                f"Session '{session_id}' not found or expired.",
                code="SESSION_NOT_FOUND",
            )
        return list(session.conversation_history)

    def set_active_dataset(self, session_id: str, dataset_id: str) -> None:
        """Sets the primary active dataset for operations in this session."""
        self.verify_dataset_ownership(session_id, dataset_id)
        session = self.get_session(session_id, touch=True)
        if session:
            session.active_dataset_id = dataset_id

    def clear_all(self) -> None:
        """Clears all sessions and deletes temporary disk folders (for testing)."""
        session_ids = list(self._sessions.keys())
        for sid in session_ids:
            self.delete_session(sid)
        self._sessions.clear()


# Global singleton manager instance
session_manager = InMemorySessionStore()
