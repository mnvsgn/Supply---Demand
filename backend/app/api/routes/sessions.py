"""
API routes for temporary session management, lifecycle control, and conversation tracking.
"""

from typing import List, Optional
from fastapi import APIRouter, Header, Response, status

from app.core.config import settings
from app.core.errors import NotFoundException, SessionExpiredException
from app.schemas.session import (
    ConversationMessageRequest,
    ConversationMessageResponse,
    SessionCreateResponse,
    SessionDeleteResponse,
    SessionDetailResponse,
)
from app.services.session_manager import session_manager

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post(
    "",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize an unguessable temporary session",
    description=(
        "Generates a cryptographically strong, 256-bit entropy session token. "
        "Creates an isolated workspace directory on disk for uploaded datasets and artifacts."
    ),
)
async def create_session(response: Response) -> SessionCreateResponse:
    record = session_manager.create_session()
    response.headers["X-Session-ID"] = record.session_id

    return SessionCreateResponse(
        session_id=record.session_id,
        created_at=record.created_at.isoformat(),
        expires_at=record.expires_at.isoformat(),
        ttl_minutes=settings.SESSION_EXPIRY_MINUTES,
        idle_timeout_minutes=settings.SESSION_IDLE_TIMEOUT_MINUTES,
    )


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve session metadata and status",
    description="Returns session timestamps, dataset count, active dataset ID, and conversation count.",
)
async def get_session(session_id: str) -> SessionDetailResponse:
    record = session_manager.get_session(session_id, touch=True)
    if not record:
        raise SessionExpiredException(
            message=f"Session '{session_id}' has expired or does not exist.",
            code="SESSION_NOT_FOUND",
        )

    return SessionDetailResponse(
        session_id=record.session_id,
        created_at=record.created_at.isoformat(),
        last_accessed_at=record.last_accessed_at.isoformat(),
        expires_at=record.expires_at.isoformat(),
        is_expired=record.is_expired,
        dataset_count=len(record.dataset_ids),
        dataset_ids=list(record.dataset_ids),
        active_dataset_id=record.active_dataset_id,
        conversation_messages_count=len(record.conversation_history),
    )


@router.delete(
    "/{session_id}",
    response_model=SessionDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Explicitly terminate and purge a session",
    description="Evicts the session from memory, purges all associated datasets, and deletes disk files.",
)
async def delete_session(session_id: str) -> SessionDeleteResponse:
    record = session_manager.get_session(session_id, touch=False)
    if not record:
        raise NotFoundException(
            message=f"Session '{session_id}' not found or already deleted.",
            code="SESSION_NOT_FOUND",
        )

    purged_count = len(record.dataset_ids)
    success = session_manager.delete_session(session_id)

    return SessionDeleteResponse(
        session_id=session_id,
        deleted=success,
        purged_datasets_count=purged_count,
        message=f"Session '{session_id}' terminated. Purged {purged_count} dataset(s) and storage artifacts.",
    )


@router.get(
    "/{session_id}/conversation",
    response_model=List[ConversationMessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve session conversation history",
)
async def get_session_conversation(session_id: str) -> List[ConversationMessageResponse]:
    record = session_manager.get_session(session_id, touch=True)
    if not record:
        raise SessionExpiredException(
            message=f"Session '{session_id}' has expired or does not exist.",
            code="SESSION_NOT_FOUND",
        )

    messages = session_manager.get_conversation(session_id)
    return [
        ConversationMessageResponse(
            role=m.role,
            content=m.content,
            timestamp=m.timestamp.isoformat(),
            metadata=m.metadata,
        )
        for m in messages
    ]


@router.post(
    "/{session_id}/conversation",
    response_model=ConversationMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Append message to session conversation history",
)
async def append_session_conversation_message(
    session_id: str,
    request: ConversationMessageRequest,
) -> ConversationMessageResponse:
    record = session_manager.get_session(session_id, touch=True)
    if not record:
        raise SessionExpiredException(
            message=f"Session '{session_id}' has expired or does not exist.",
            code="SESSION_NOT_FOUND",
        )

    msg = session_manager.append_conversation_message(
        session_id=session_id,
        role=request.role,
        content=request.content,
        metadata=request.metadata,
    )

    return ConversationMessageResponse(
        role=msg.role,
        content=msg.content,
        timestamp=msg.timestamp.isoformat(),
        metadata=msg.metadata,
    )
