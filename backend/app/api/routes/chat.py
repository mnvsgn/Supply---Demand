"""
Chat API route for conversational supply & demand queries.
"""

from typing import Optional
from fastapi import APIRouter, Header, Response, status
from app.schemas.chat import ChatPromptRequest, ChatResponse
from app.services.chat_service import chat_service
from app.services.session_manager import session_manager

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit chat prompt for conversational forecasting",
)
async def submit_chat_message(
    payload: ChatPromptRequest,
    response: Response,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> ChatResponse:
    session_id = payload.session_id or x_session_id
    if session_id:
        # Verify and touch session activity
        try:
            session_manager.get_session(session_id)
            response.headers["X-Session-ID"] = session_id
        except Exception:
            pass

    chat_res = await chat_service.handle_prompt(
        prompt=payload.prompt,
        dataset_id=payload.dataset_id,
        session_id=session_id,
    )

    # Record message in conversation history if session is active
    if session_id:
        try:
            session_manager.append_message(
                session_id=session_id,
                role="user",
                content=payload.prompt,
            )
            session_manager.append_message(
                session_id=session_id,
                role="assistant",
                content=chat_res.message,
                metadata={"message_type": chat_res.message_type},
            )
        except Exception:
            pass

    return chat_res
