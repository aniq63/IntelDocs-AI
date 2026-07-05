from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import models, schemas
from utils.authentication import get_verified_team

from services.pipeline import dashboard_service_pipeline as dashboard_service

router = APIRouter(
    prefix="/dashboard/team",
    tags=["Team Dashboard"]
)


@router.get("/overview", response_model=schemas.TeamOverviewOut)
async def team_overview(
    current_team: models.Team = Depends(get_verified_team),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_service.get_team_overview(db, current_team.id)


@router.get("/documents", response_model=List[schemas.DocumentOut])
async def team_documents(
    current_team: models.Team = Depends(get_verified_team),
    db: AsyncSession = Depends(get_db),
):
    """
    This team's own uploaded documents only (visibility='team') - not
    the company-wide documents it can also read via /knowledge.
    """
    return await dashboard_service.list_team_documents(db, current_team.id)