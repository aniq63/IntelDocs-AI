from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import models


# ----------------------------------------
# Company dashboard
# ----------------------------------------

async def get_company_overview(db: AsyncSession, company_id: int) -> dict:
    """
    total_documents counts EVERY document under this company,
    including team-scoped ones - this is an org-wide admin view.
    """

    doc_count = await db.execute(
        select(func.count(models.Document.id))
        .where(models.Document.company_id == company_id)
    )

    team_count = await db.execute(
        select(func.count(models.Team.id))
        .where(models.Team.company_id == company_id)
    )

    return {
        "total_documents": doc_count.scalar_one(),
        "total_teams": team_count.scalar_one(),
    }


async def list_company_documents(
    db: AsyncSession,
    company_id: int,
) -> List[models.Document]:
    """
    All documents under this company - both visibility='company' and
    every team's visibility='team' documents.
    """

    result = await db.execute(
        select(models.Document)
        .where(models.Document.company_id == company_id)
        .order_by(models.Document.uploaded_at.desc())
    )

    return list(result.scalars().all())


async def list_company_teams(
    db: AsyncSession,
    company_id: int,
) -> List[models.Team]:
    result = await db.execute(
        select(models.Team)
        .where(models.Team.company_id == company_id)
        .order_by(models.Team.created_at.desc())
    )

    return list(result.scalars().all())


# ----------------------------------------
# Team dashboard
# ----------------------------------------

async def get_team_overview(db: AsyncSession, team_id: int) -> dict:
    """
    total_documents here is scoped to this team's OWN documents only
    (visibility='team'), not the company-wide ones it can also read.
    """

    doc_count = await db.execute(
        select(func.count(models.Document.id))
        .where(
            models.Document.team_id == team_id,
            models.Document.visibility == "team",
        )
    )

    return {"total_documents": doc_count.scalar_one()}


async def list_team_documents(
    db: AsyncSession,
    team_id: int,
) -> List[models.Document]:
    result = await db.execute(
        select(models.Document)
        .where(
            models.Document.team_id == team_id,
            models.Document.visibility == "team",
        )
        .order_by(models.Document.uploaded_at.desc())
    )

    return list(result.scalars().all())