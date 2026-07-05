from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import models, schemas
from utils.authentication import get_current_company

from services.pipeline import dashboard_service_pipeline as dashboard_service

router = APIRouter(
    prefix="/dashboard/company",
    tags=["Company Dashboard"]
)


@router.get("/overview", response_model=schemas.CompanyOverviewOut)
async def company_overview(
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_service.get_company_overview(db, current_company.id)


@router.get("/documents", response_model=List[schemas.DocumentOut])
async def company_documents(
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """
    Every document under this company - both company-wide uploads and
    every team's own documents.
    """
    return await dashboard_service.list_company_documents(db, current_company.id)


@router.get("/teams", response_model=List[schemas.TeamSummaryOut])
async def company_teams(
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_service.list_company_teams(db, current_company.id)