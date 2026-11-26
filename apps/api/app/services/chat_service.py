from __future__ import annotations

import json
import time
from typing import AsyncGenerator
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Conversation, Document, DocumentChunk, Feedback, Message
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    CitationItem,
    FeedbackRequest,
    FeedbackResponse,
    RetrievalMeta,
    TokenUsageMeta,
)
from app.services.audit_service import record_audit_event
from app.services.permission_service import accessible_documents_subquery, get_membership_or_403
from packages.rag.embeddings.bge import get_embedder
from packages.rag.generation.citations import CitationValidator
from packages.rag.generation.prompts import build_rag_prompt
from packages.rag.generation.providers import get_llm_provider
from packages.rag.retrieval.pipeline import HybridRetrievalPipeline
from packages.rag.retrieval.reranker import get_reranker


def _build_retrieval_pipeline() -> HybridRetrievalPipeline:
    embedder = get_embedder(
        provider=settings.EMBEDDING_PROVIDER,
        model_name=settings.EMBEDDING_MODEL,
        dimension=settings.EMBEDDING_DIMENSION,
    )
    reranker = get_reranker(
        provider=settings.RERANKER_PROVIDER,
        model_name=settings.RERANKER_MODEL,
    )
    return HybridRetrievalPipeline(embedder=embedder, reranker=reranker, rrf_k=60)


def _get_or_create_conversation(
    db: Session,
    *,
    organization_id: UUID,
    user_id: UUID,
    conversation_id: UUID | None,
    first_question: str,
) -> Conversation:
    if conversation_id is not None:
        conv = db.execute(select(Conversation).where(Conversation.id == conversation_id)).scalar_one_or_none()
        if conv is None or conv.organization_id != organization_id or conv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conversation not found or belongs to another user/organisation.",
            )
        return conv

    title = first_question.strip()[:72] + ("..." if len(first_question.strip()) > 72 else "")
    conv = Conversation(
        organization_id=organization_id,
        user_id=user_id,
        title=title or "New conversation",
    )
    db.add(conv)
    db.flush()
    return conv


async def execute_rag_chat(
    *,
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    payload: ChatRequest,
) -> ChatResponse:
    t0 = time.perf_counter()
    membership = get_membership_or_403(db, organization_id, user_id)

    conv = _get_or_create_conversation(
        db,
        organization_id=organization_id,
        user_id=user_id,
        conversation_id=payload.conversation_id,
        first_question=payload.question,
    )

    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=payload.question.strip(),
        citations=[],
        token_usage={},
    )
    db.add(user_msg)
    db.flush()

    allowed_subq = accessible_documents_subquery(organization_id, user_id, membership.role)
    pipeline = _build_retrieval_pipeline()
    retrieval_outcome = pipeline.retrieve(
        db=db,
        chunk_model=DocumentChunk,
        document_model=Document,
        allowed_doc_ids_subquery=allowed_subq,
        organization_id=organization_id,
        query=payload.question.strip(),
        document_ids=payload.filters.document_ids or None,
        candidate_limit=20,
        top_k=payload.top_k,
        mode=payload.retrieval_mode,
    )

    sys_prompt, user_prompt = build_rag_prompt(payload.question.strip(), retrieval_outcome.chunks)
    llm = get_llm_provider(
        provider=settings.LLM_PROVIDER,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
    )
    llm_response = await llm.generate(sys_prompt, user_prompt)

    validator = CitationValidator()
    clean_answer, validated_citations = validator.validate(llm_response.content, retrieval_outcome.chunks)
    citations_dicts = [c.to_dict() for c in validated_citations]
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=clean_answer,
        citations=citations_dicts,
        model=llm_response.model,
        token_usage={
            "input_tokens": llm_response.input_tokens,
            "output_tokens": llm_response.output_tokens,
        },
        latency_ms=latency_ms,
    )
    db.add(assistant_msg)
    record_audit_event(
        db,
        organization_id=organization_id,
        actor_id=user_id,
        action="chat.query",
        resource_id=conv.id,
        metadata={
            "retrieval_mode": payload.retrieval_mode,
            "candidates": retrieval_outcome.candidate_count,
            "citations": len(citations_dicts),
            "latency_ms": latency_ms,
        },
    )
    db.commit()
    db.refresh(assistant_msg)

    return ChatResponse(
        conversation_id=conv.id,
        message_id=assistant_msg.id,
        answer=clean_answer,
        citations=[CitationItem(**c) for c in citations_dicts],
        retrieval=RetrievalMeta(
            candidate_count=retrieval_outcome.candidate_count,
            reranked_count=retrieval_outcome.reranked_count,
            mode=retrieval_outcome.mode,
        ),
        usage=TokenUsageMeta(
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
        ),
        latency_ms=latency_ms,
    )


async def stream_rag_chat(
    *,
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    payload: ChatRequest,
) -> AsyncGenerator[str, None]:
    """Server-Sent Events (SSE) streaming RAG generator."""
    t0 = time.perf_counter()
    membership = get_membership_or_403(db, organization_id, user_id)

    conv = _get_or_create_conversation(
        db,
        organization_id=organization_id,
        user_id=user_id,
        conversation_id=payload.conversation_id,
        first_question=payload.question,
    )
    db.add(Message(conversation_id=conv.id, role="user", content=payload.question.strip(), citations=[], token_usage={}))
    db.flush()

    allowed_subq = accessible_documents_subquery(organization_id, user_id, membership.role)
    pipeline = _build_retrieval_pipeline()
    retrieval_outcome = pipeline.retrieve(
        db=db,
        chunk_model=DocumentChunk,
        document_model=Document,
        allowed_doc_ids_subquery=allowed_subq,
        organization_id=organization_id,
        query=payload.question.strip(),
        document_ids=payload.filters.document_ids or None,
        candidate_limit=20,
        top_k=payload.top_k,
        mode=payload.retrieval_mode,
    )

    sys_prompt, user_prompt = build_rag_prompt(payload.question.strip(), retrieval_outcome.chunks)
    llm = get_llm_provider(
        provider=settings.LLM_PROVIDER,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
    )

    raw_chunks: list[str] = []
    async for delta in llm.stream(sys_prompt, user_prompt):
        raw_chunks.append(delta)
        yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"

    full_raw = "".join(raw_chunks)
    validator = CitationValidator()
    clean_answer, validated_citations = validator.validate(full_raw, retrieval_outcome.chunks)
    citations_dicts = [c.to_dict() for c in validated_citations]
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    in_tok = llm.count_tokens(sys_prompt + user_prompt)
    out_tok = llm.count_tokens(clean_answer)

    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=clean_answer,
        citations=citations_dicts,
        model=getattr(llm, "model", "stream-model"),
        token_usage={"input_tokens": in_tok, "output_tokens": out_tok},
        latency_ms=latency_ms,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    done_payload = {
        "type": "done",
        "conversation_id": str(conv.id),
        "message_id": str(assistant_msg.id),
        "answer": clean_answer,
        "citations": citations_dicts,
        "latency_ms": latency_ms,
    }
    yield f"data: {json.dumps(done_payload)}\n\n"


def submit_message_feedback(
    db: Session,
    *,
    message_id: UUID,
    user_id: UUID,
    payload: FeedbackRequest,
) -> FeedbackResponse:
    msg = db.execute(select(Message).where(Message.id == message_id)).scalar_one_or_none()
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

    conv = db.execute(select(Conversation).where(Conversation.id == msg.conversation_id)).scalar_one()
    get_membership_or_403(db, conv.organization_id, user_id)

    fb = Feedback(
        message_id=msg.id,
        user_id=user_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return FeedbackResponse(
        id=fb.id,
        message_id=fb.message_id,
        rating=fb.rating,
        comment=fb.comment,
        created_at=fb.created_at,
    )
