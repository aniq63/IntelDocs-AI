from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import models
from services.rag.chain import RagChain
from utils.logger import logging

# Titles are truncated to this length when auto-generated from the
# first question in a session.
TITLE_MAX_LENGTH = 80


# ----------------------------------------
# Session lookup / creation
# ----------------------------------------

async def _get_or_create_session(
    db: AsyncSession,
    *,
    company_id: int,
    visibility: str,
    team_id: Optional[int] = None,
    session_id: Optional[int] = None,
    title_hint: Optional[str] = None,
) -> models.ChatSession:

    if session_id:
        return await get_owned_session(
            session_id,
            db,
            visibility=visibility,
            company_id=company_id,
            team_id=team_id,
        )

    title = (title_hint or "New conversation").strip()[:TITLE_MAX_LENGTH]

    session = models.ChatSession(
        company_id=company_id,
        team_id=team_id,
        visibility=visibility,
        title=title,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    logging.info(f"[chat] created new session id={session.id} visibility={visibility}")

    return session


async def get_owned_session(
    session_id: int,
    db: AsyncSession,
    *,
    visibility: str,
    company_id: int,
    team_id: Optional[int] = None,
) -> models.ChatSession:
    filters = [
        models.ChatSession.id == session_id,
        models.ChatSession.visibility == visibility,
        models.ChatSession.company_id == company_id,
    ]

    if team_id is not None:
        filters.append(models.ChatSession.team_id == team_id)

    result = await db.execute(select(models.ChatSession).where(*filters))
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    return session


async def list_sessions(
    db: AsyncSession,
    *,
    visibility: str,
    company_id: int,
    team_id: Optional[int] = None,
) -> List[models.ChatSession]:
    filters = [
        models.ChatSession.visibility == visibility,
        models.ChatSession.company_id == company_id,
    ]

    if team_id is not None:
        filters.append(models.ChatSession.team_id == team_id)

    result = await db.execute(
        select(models.ChatSession)
        .where(*filters)
        .order_by(models.ChatSession.updated_at.desc())
    )

    return list(result.scalars().all())


async def list_messages(
    session: models.ChatSession,
    db: AsyncSession,
) -> List[models.ChatMessage]:
    result = await db.execute(
        select(models.ChatMessage)
        .where(models.ChatMessage.session_id == session.id)
        .order_by(models.ChatMessage.created_at.asc())
    )

    return list(result.scalars().all())


async def delete_session(session: models.ChatSession, db: AsyncSession) -> None:
    await db.delete(session)  # cascades to chat_messages
    await db.commit()


# ----------------------------------------
# Ask + persist (the actual chat pipeline)
# ----------------------------------------

async def ask_and_store(
    db: AsyncSession,
    *,
    company_id: int,
    company_name: str,
    visibility: str,
    question: str,
    team_id: Optional[int] = None,
    team_name: Optional[str] = None,
    session_id: Optional[int] = None,
    top_k: int = 6,
    min_similarity: float = 0.15,
) -> dict:
    """
    Runs one chat turn: gets/creates the session, asks RagChain, and
    persists the question/answer pair. Returns a plain dict matching
    schemas.ChatAskResponse.
    """

    session = await _get_or_create_session(
        db,
        company_id=company_id,
        team_id=team_id,
        visibility=visibility,
        session_id=session_id,
        title_hint=question,
    )

    chain = RagChain(
        db=db,
        company_id=company_id,
        company_name=company_name,
        team_id=team_id,
        team_name=team_name,
        top_k=top_k,
        min_similarity=min_similarity,
    )

    answer = await chain.ask(question)

    message = models.ChatMessage(
        session_id=session.id,
        company_id=company_id,
        team_id=team_id,
        question=question,
        answer=answer,
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    logging.info(f"[chat] saved message id={message.id} session_id={session.id}")

    return {
        "session_id": session.id,
        "message_id": message.id,
        "question": question,
        "answer": answer,
    }