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
    get_current_team,
    get_verified_team,
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
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    """
    A team can only be logged into while its company session is
    active. The company is taken from the authenticated company
    session (not from the request body), so there's no way to log
    into a team belonging to a company you aren't authenticated as.
    """

    team_name = team.team_name.strip().lower()

    # Find team within the *currently authenticated* company only
    team_result = await db.execute(
        select(models.Team).where(
            (models.Team.company_id == current_company.id) &
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
    current_team: models.Team = Depends(get_verified_team),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout the currently authenticated team. Requires both the team
    session and its owning company's session to be active.
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
    current_team: models.Team = Depends(get_verified_team)
):
    """
    Return the profile of the currently authenticated team. Requires
    both the team session and its owning company's session to be
    active.
    """

    return current_team