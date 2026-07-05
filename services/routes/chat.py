from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import models, schemas
from utils.authentication import get_current_company, get_verified_team

from services.pipeline import chat_service_pipeline as chat_service

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# ----------------------------------------
# Company Chat
# ----------------------------------------

@router.post("/company/ask", response_model=schemas.ChatAskResponse)
async def ask_company(
    payload: schemas.ChatAskRequest,
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.ask_and_store(
        db,
        company_id=current_company.id,
        company_name=current_company.name,
        visibility="company",
        question=payload.question,
        session_id=payload.session_id,
    )


@router.get("/company/sessions", response_model=List[schemas.ChatSessionOut])
async def list_company_sessions(
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.list_sessions(
        db,
        visibility="company",
        company_id=current_company.id,
    )


@router.get(
    "/company/sessions/{session_id}/messages",
    response_model=List[schemas.ChatMessageOut],
)
async def get_company_session_messages(
    session_id: int,
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    session = await chat_service.get_owned_session(
        session_id,
        db,
        visibility="company",
        company_id=current_company.id,
    )

    return await chat_service.list_messages(session, db)


@router.delete("/company/sessions/{session_id}", status_code=204)
async def delete_company_session(
    session_id: int,
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    session = await chat_service.get_owned_session(
        session_id,
        db,
        visibility="company",
        company_id=current_company.id,
    )

    await chat_service.delete_session(session, db)

    return None


# ----------------------------------------
# Team Chat
#
# get_verified_team requires BOTH a valid team session AND a valid
# session for that team's owning company (see utils/authentication.py)
# ----------------------------------------

@router.post("/team/ask", response_model=schemas.ChatAskResponse)
async def ask_team(
    payload: schemas.ChatAskRequest,
    current_team: models.Team = Depends(get_verified_team),
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.ask_and_store(
        db,
        company_id=current_team.company_id,
        company_name=current_company.name,
        visibility="team",
        question=payload.question,
        team_id=current_team.id,
        team_name=current_team.name,
        session_id=payload.session_id,
    )


@router.get("/team/sessions", response_model=List[schemas.ChatSessionOut])
async def list_team_sessions(
    current_team: models.Team = Depends(get_verified_team),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.list_sessions(
        db,
        visibility="team",
        company_id=current_team.company_id,
        team_id=current_team.id,
    )


@router.get(
    "/team/sessions/{session_id}/messages",
    response_model=List[schemas.ChatMessageOut],
)
async def get_team_session_messages(
    session_id: int,
    current_team: models.Team = Depends(get_verified_team),
    db: AsyncSession = Depends(get_db),
):
    session = await chat_service.get_owned_session(
        session_id,
        db,
        visibility="team",
        company_id=current_team.company_id,
        team_id=current_team.id,
    )

    return await chat_service.list_messages(session, db)


@router.delete("/team/sessions/{session_id}", status_code=204)
async def delete_team_session(
    session_id: int,
    current_team: models.Team = Depends(get_verified_team),
    db: AsyncSession = Depends(get_db),
):
    session = await chat_service.get_owned_session(
        session_id,
        db,
        visibility="team",
        company_id=current_team.company_id,
        team_id=current_team.id,
    )

    await chat_service.delete_session(session, db)

    return None