from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import chat_rate_limiter
from app.db.models import Conversation, User
from app.db.session import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
    FeedbackRequest,
    FeedbackResponse,
    MessageItem,
)
from app.services.chat_service import execute_rag_chat, stream_rag_chat, submit_message_feedback

router = APIRouter(tags=["Chat & RAG"])


@router.post("/organizations/{org_id}/chat", response_model=ChatResponse)
async def chat_with_knowledge_base(
    org_id: UUID,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    chat_rate_limiter.check(f"chat:{current_user.id}")
    return await execute_rag_chat(
        db=db,
        organization_id=org_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.post("/organizations/{org_id}/chat/stream")
async def stream_chat_with_knowledge_base(
    org_id: UUID,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    chat_rate_limiter.check(f"chat:{current_user.id}")
    return StreamingResponse(
        stream_rag_chat(
            db=db,
            organization_id=org_id,
            user_id=current_user.id,
            payload=payload,
        ),
        media_type="text/event-stream",
    )


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    organization_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConversationSummary]:
    stmt = select(Conversation).where(Conversation.user_id == current_user.id)
    if organization_id is not None:
        stmt = stmt.where(Conversation.organization_id == organization_id)
    convs = db.execute(stmt.order_by(Conversation.created_at.desc())).scalars().all()
    return [
        ConversationSummary(
            id=c.id,
            organization_id=c.organization_id,
            title=c.title,
            created_at=c.created_at,
        )
        for c in convs
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationDetail:
    conv = db.execute(select(Conversation).where(Conversation.id == conversation_id)).scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation.")

    return ConversationDetail(
        id=conv.id,
        organization_id=conv.organization_id,
        title=conv.title,
        created_at=conv.created_at,
        messages=[
            MessageItem(
                id=m.id,
                role=m.role,
                content=m.content,
                citations=m.citations or [],
                model=m.model,
                token_usage=m.token_usage or {},
                latency_ms=m.latency_ms,
                created_at=m.created_at,
            )
            for m in conv.messages
        ],
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    conv = db.execute(select(Conversation).where(Conversation.id == conversation_id)).scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation.")
    db.delete(conv)
    db.commit()


@router.post("/messages/{message_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    message_id: UUID,
    payload: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    return submit_message_feedback(
        db,
        message_id=message_id,
        user_id=current_user.id,
        payload=payload,
    )
