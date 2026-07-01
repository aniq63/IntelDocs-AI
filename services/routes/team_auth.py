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
    get_current_company,
    get_current_team
)

warnings.filterwarnings("ignore")

router = APIRouter(
    prefix="/Team-Authentication",
    tags=["Team Authentication"]
)


# ---------------------------------
# Team Login Endpoint
# ---------------------------------

@router.post(
    "/team/login",
    response_model=schemas.TokenResponse
)
async def team_login(
    team: schemas.TeamLogin,
    db: AsyncSession = Depends(get_db)
):

    company_name = team.company_name.strip().lower()
    team_name = team.team_name.strip().lower()

    # Find company
    company_result = await db.execute(
        select(models.Company).where(
            models.Company.name == company_name
        )
    )

    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=401,
            detail="Invalid company name."
        )

    # Find team within this company
    team_result = await db.execute(
        select(models.Team).where(
            (models.Team.company_id == company.id) &
            (models.Team.name == team_name)
        )
    )

    team_record = team_result.scalar_one_or_none()

    if not team_record:
        raise HTTPException(
            status_code=401,
            detail="Incorrect team name or password."
        )

    # Verify password
    if not verify_password(
        team.password,
        team_record.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect team name or password."
        )

    # Generate session token
    token = generate_session_token()

    team_record.session_token = token

    await db.commit()
    await db.refresh(team_record)

    return {
        "access_token": token,
        "token_type": "simple"
    }

# ---------------------------------
# Team Logout Endpoint
# ---------------------------------

@router.post("/team/logout")
async def team_logout(
    current_team: models.Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout the currently authenticated team.
    """

    current_team.session_token = None

    await db.commit()

    return {
        "message": "Successfully logged out."
    }


# ---------------------------------
# Team Profile Endpoint
# ---------------------------------

@router.get(
    "/team/profile",
    response_model=schemas.TeamResponse
)
async def team_profile(
    current_team: models.Team = Depends(get_current_team)
):
    """
    Return the profile of the currently authenticated team.
    """

    return current_team