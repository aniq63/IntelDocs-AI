from typing import List

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import models, schemas
from utils.authentication import get_current_company, get_current_team

from services.pipeline import knowledge_service_pipeline as knowledge_service

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge"]
)


# ----------------------------------------
# Company Knowledge
# ----------------------------------------

@router.post(
    "/company/knowledge/upload",
    response_model=schemas.DocumentOut,
    status_code=201,
)
async def upload_company_document(
    file: UploadFile = File(...),
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    return await knowledge_service.process_and_store_document(
        file=file,
        company_id=current_company.id,
        team_id=None,
        visibility="company",
        db=db,
    )


@router.get("/company/knowledge", response_model=List[schemas.DocumentOut])
async def list_company_documents(
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    return await knowledge_service.list_documents(
        db,
        visibility="company",
        company_id=current_company.id,
    )


@router.get(
    "/company/knowledge/by-name",
    response_model=schemas.DocumentOut,
)
async def get_company_document_by_name(
    name: str,
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    return await knowledge_service.get_owned_document_by_source(
        name,
        db,
        visibility="company",
        company_id=current_company.id,
    )


@router.delete("/company/knowledge/by-name", status_code=204)
async def delete_company_document_by_name(
    name: str,
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    document = await knowledge_service.get_owned_document_by_source(
        name,
        db,
        visibility="company",
        company_id=current_company.id,
    )

    await knowledge_service.delete_document(document, db)

    return None


@router.put(
    "/company/knowledge/by-name",
    response_model=schemas.DocumentOut,
)
async def update_company_document_by_name(
    name: str,
    file: UploadFile = File(...),
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    document = await knowledge_service.get_owned_document_by_source(
        name,
        db,
        visibility="company",
        company_id=current_company.id,
    )

    return await knowledge_service.replace_document(document, file, db)


# ----------------------------------------
# Team Knowledge
# ----------------------------------------

@router.post(
    "/team/knowledge/upload",
    response_model=schemas.DocumentOut,
    status_code=201,
)
async def upload_team_document(
    file: UploadFile = File(...),
    current_team: models.Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    return await knowledge_service.process_and_store_document(
        file=file,
        company_id=current_team.company_id,
        team_id=current_team.id,
        visibility="team",
        db=db,
    )


@router.get("/team/knowledge", response_model=List[schemas.DocumentOut])
async def list_team_documents(
    current_team: models.Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    return await knowledge_service.list_documents(
        db,
        visibility="team",
        team_id=current_team.id,
    )


@router.get(
    "/team/knowledge/by-name",
    response_model=schemas.DocumentOut,
)
async def get_team_document_by_name(
    name: str,
    current_team: models.Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    return await knowledge_service.get_owned_document_by_source(
        name,
        db,
        visibility="team",
        team_id=current_team.id,
    )


@router.delete("/team/knowledge/by-name", status_code=204)
async def delete_team_document_by_name(
    name: str,
    current_team: models.Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    document = await knowledge_service.get_owned_document_by_source(
        name,
        db,
        visibility="team",
        team_id=current_team.id,
    )

    await knowledge_service.delete_document(document, db)

    return None


@router.put(
    "/team/knowledge/by-name",
    response_model=schemas.DocumentOut,
)
async def update_team_document_by_name(
    name: str,
    file: UploadFile = File(...),
    current_team: models.Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    document = await knowledge_service.get_owned_document_by_source(
        name,
        db,
        visibility="team",
        team_id=current_team.id,
    )

    return await knowledge_service.replace_document(document, file, db)