from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import warnings

from database.connection import get_db
from database import models, schemas
from utils.authentication import (
    hash_password,
    verify_password,
    generate_session_token,
    get_current_company
)

warnings.filterwarnings("ignore")

router = APIRouter(
    prefix="/Team-Registration",
    tags=["Team Registration"]
)

# ---------------------------------
# Team Registration Endpoint
# ---------------------------------
@router.post(
    "/team/create",
    response_model=schemas.TeamResponse
)
async def create_team(
    team: schemas.TeamCreate,
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):

    team_name = team.name.strip().lower()

    result = await db.execute(
        select(models.Team).where(
            (models.Team.company_id == current_company.id) &
            (models.Team.name == team_name)
        )
    )

    existing_team = result.scalar_one_or_none()

    if existing_team:
        raise HTTPException(
            status_code=400,
            detail="Team with this name already exists."
        )

    new_team = models.Team(
        company_id=current_company.id,
        name=team_name,
        description=team.description,
        password_hash=hash_password(team.password)
    )

    db.add(new_team)

    await db.commit()
    await db.refresh(new_team)

    return new_team

# ---------------------------------
# Team Update Endpoint
# ---------------------------------

@router.put(
    "/team/{team_name}",
    response_model=schemas.TeamResponse
)
async def update_team(
    team_name: str,
    team: schemas.TeamUpdate,
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):

    team_name = team_name.strip().lower()

    # Find the existing team
    result = await db.execute(
        select(models.Team).where(
            (models.Team.company_id == current_company.id) &
            (models.Team.name == team_name)
        )
    )

    existing_team = result.scalar_one_or_none()

    if not existing_team:
        raise HTTPException(
            status_code=404,
            detail="Team not found."
        )

    # ----------------------------------------------------
    # If changing the team name, ensure it's still unique
    # ----------------------------------------------------
    if team.name is not None:

        new_team_name = team.name.strip().lower()

        result = await db.execute(
            select(models.Team).where(
                (models.Team.company_id == current_company.id) &
                (models.Team.name == new_team_name)
            )
        )

        duplicate_team = result.scalar_one_or_none()

        if duplicate_team and duplicate_team.id != existing_team.id:
            raise HTTPException(
                status_code=400,
                detail="Another team with this name already exists."
            )

        existing_team.name = new_team_name

    # Update description
    if team.description is not None:
        existing_team.description = team.description

    # Update password
    if team.password is not None:
        existing_team.password_hash = hash_password(team.password)

    await db.commit()
    await db.refresh(existing_team)

    return existing_team


# ---------------------------------
# Team Delete Endpoint
# ---------------------------------
@router.delete("/team/{team_name}")
async def delete_team(
    team_name: str,
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):

    team_name = team_name.strip().lower()

    result = await db.execute(
        select(models.Team).where(
            (models.Team.company_id == current_company.id) &
            (models.Team.name == team_name)
        )
    )

    existing_team = result.scalar_one_or_none()

    if not existing_team:
        raise HTTPException(
            status_code=404,
            detail="Team not found."
        )

    await db.delete(existing_team)

    await db.commit()

    return {
        "message": f"Team '{team_name}' deleted successfully."
    }



# ---------------------------------
# Team List Endpoint
# ---------------------------------

@router.get(
    "/team/list",
    response_model=list[schemas.TeamResponse]
)
async def list_teams(
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(models.Team).where(
            models.Team.company_id == current_company.id
        )
    )

    teams = result.scalars().all()

    return teams