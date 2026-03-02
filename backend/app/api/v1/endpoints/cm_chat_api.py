"""
PresenceOS - CM Chat API Endpoints

Conversational Community Manager AI — iMessage-style chat interface.
Prefix: /cm-chat (to avoid conflict with existing /cm community interactions).
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import selectinload

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.services.cm_chat_service import CMChatService

logger = structlog.get_logger()
router = APIRouter()


# ── Request / Response Models ────────────────────────────────────────────────


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(
        default=None,
        description="Existing session ID. If null, creates a new session.",
    )


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    proposals: list[dict] | None = None
    tokens_used: int
    created_at: str


class SessionResponse(BaseModel):
    id: str
    brand_id: str
    title: str
    status: str
    message_count: int
    summary: str | None = None
    created_at: str
    updated_at: str


class SendMessageResponse(BaseModel):
    session: SessionResponse
    message: MessageResponse


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/{brand_id}/send")
async def send_message(
    brand_id: UUID,
    body: SendMessageRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> SendMessageResponse:
    """Send a message to the CM Chat AI and get a response."""
    brand = await get_brand(brand_id, current_user, db)

    service = CMChatService(db)

    session_uuid = UUID(body.session_id) if body.session_id else None
    session = await service.get_or_create_session(brand_id, session_uuid)
    assistant_msg = await service.send_message(brand, session, body.message)

    await db.refresh(session)

    return SendMessageResponse(
        session=SessionResponse(
            id=str(session.id),
            brand_id=str(session.brand_id),
            title=session.title,
            status=session.status,
            message_count=session.message_count,
            summary=session.summary,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        ),
        message=MessageResponse(
            id=str(assistant_msg.id),
            session_id=str(assistant_msg.session_id),
            role=assistant_msg.role,
            content=assistant_msg.content,
            proposals=assistant_msg.proposals,
            tokens_used=assistant_msg.tokens_used,
            created_at=assistant_msg.created_at.isoformat(),
        ),
    )


@router.get("/{brand_id}/sessions")
async def list_sessions(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """List CM Chat sessions for a brand."""
    await get_brand(brand_id, current_user, db)

    service = CMChatService(db)
    sessions, total = await service.list_sessions(brand_id, limit, offset)

    return {
        "sessions": [
            SessionResponse(
                id=str(s.id),
                brand_id=str(s.brand_id),
                title=s.title,
                status=s.status,
                message_count=s.message_count,
                summary=s.summary,
                created_at=s.created_at.isoformat(),
                updated_at=s.updated_at.isoformat(),
            )
            for s in sessions
        ],
        "total": total,
    }


@router.get("/{brand_id}/sessions/{session_id}/messages")
async def get_session_messages(
    brand_id: UUID,
    session_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Get all messages for a specific session."""
    await get_brand(brand_id, current_user, db)

    service = CMChatService(db)
    messages = await service.get_session_messages(session_id, brand_id)

    return {
        "messages": [
            MessageResponse(
                id=str(m.id),
                session_id=str(m.session_id),
                role=m.role,
                content=m.content,
                proposals=m.proposals,
                tokens_used=m.tokens_used,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ]
    }


@router.delete("/{brand_id}/sessions/{session_id}")
async def delete_session(
    brand_id: UUID,
    session_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Delete a CM Chat session and all its messages."""
    await get_brand(brand_id, current_user, db)

    service = CMChatService(db)
    deleted = await service.delete_session(session_id, brand_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return {"success": True}
