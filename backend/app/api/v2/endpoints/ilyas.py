"""
PresenceOS - Ilyas v2 Endpoints

Conversational CM AI Agent — iMessage-style chat.
Structural copy of cm_chat_api.py with vision + Mem0 support.
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, get_brand
from app.services.ilyas.agent import IlyasAgent

logger = structlog.get_logger()
router = APIRouter()


# ── Request / Response Models ──


class IlyasChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = Field(
        default=None,
        description="Existing session ID. If null, creates a new session.",
    )
    image_url: str | None = Field(
        default=None,
        description="URL of a food photo to analyze with vision.",
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
    source: str = "ilyas"
    created_at: str
    updated_at: str


class IlyasChatResponse(BaseModel):
    session: SessionResponse
    message: MessageResponse
    vision_analysis: str | None = None


# ── Helper ──

def _session_response(s) -> SessionResponse:
    return SessionResponse(
        id=str(s.id),
        brand_id=str(s.brand_id),
        title=s.title,
        status=s.status,
        message_count=s.message_count,
        summary=s.summary,
        source=getattr(s, "source", "ilyas"),
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
    )


def _message_response(m) -> MessageResponse:
    return MessageResponse(
        id=str(m.id),
        session_id=str(m.session_id),
        role=m.role,
        content=m.content,
        proposals=m.proposals,
        tokens_used=m.tokens_used,
        created_at=m.created_at.isoformat(),
    )


# ── Endpoints ──


@router.post("/{brand_id}/chat")
async def chat(
    brand_id: UUID,
    body: IlyasChatRequest,
    current_user: FirebaseUser,
    db: DBSession,
) -> IlyasChatResponse:
    """Send a message to Ilyas and get a response."""
    brand = await get_brand(brand_id, current_user, db)
    agent = IlyasAgent(db)

    session_uuid = UUID(body.session_id) if body.session_id else None
    session = await agent.get_or_create_session(brand_id, session_uuid)

    assistant_msg = await agent.chat(
        brand=brand,
        session=session,
        user_message=body.message,
        user_id=str(current_user.id),
        image_url=body.image_url,
    )

    await db.refresh(session)

    return IlyasChatResponse(
        session=_session_response(session),
        message=_message_response(assistant_msg),
        vision_analysis=None,  # Vision analysis is embedded in message content
    )


@router.get("/{brand_id}/sessions")
async def list_sessions(
    brand_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """List Ilyas chat sessions for a brand."""
    await get_brand(brand_id, current_user, db)
    agent = IlyasAgent(db)
    sessions, total = await agent.list_sessions(brand_id, limit, offset)

    return {
        "sessions": [_session_response(s) for s in sessions],
        "total": total,
    }


@router.get("/{brand_id}/sessions/{session_id}/messages")
async def get_session_messages(
    brand_id: UUID,
    session_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
) -> dict:
    """Get all messages for an Ilyas session."""
    await get_brand(brand_id, current_user, db)
    agent = IlyasAgent(db)
    messages = await agent.get_session_messages(session_id, brand_id)

    return {"messages": [_message_response(m) for m in messages]}


@router.delete("/{brand_id}/sessions/{session_id}")
async def delete_session(
    brand_id: UUID,
    session_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
) -> dict:
    """Delete an Ilyas session and all its messages."""
    await get_brand(brand_id, current_user, db)
    agent = IlyasAgent(db)
    deleted = await agent.delete_session(session_id, brand_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return {"success": True}


@router.get("/{brand_id}/context")
async def get_context(
    brand_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
) -> dict:
    """Debug endpoint — return the context Ilyas would use."""
    brand = await get_brand(brand_id, current_user, db)
    agent = IlyasAgent(db)
    return await agent.get_context(brand, str(current_user.id))
