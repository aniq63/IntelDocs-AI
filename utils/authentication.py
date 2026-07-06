import uuid
import bcrypt
from typing import Optional

from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import Company, Team
from utils.settings import get_settings

settings = get_settings()


# =============================================================================
# PASSWORD UTILITIES
# =============================================================================

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def generate_session_token() -> str:
    return uuid.uuid4().hex


# =============================================================================
# COMPANY AUTHENTICATION
# =============================================================================

async def get_current_company(
    session_token: Optional[str] = Header(None, alias="session-token"),
    db: AsyncSession = Depends(get_db)
) -> Company:

    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Session token is missing"
        )

    result = await db.execute(
        select(Company).where(
            Company.session_token == session_token
        )
    )

    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session token"
        )

    return company


async def get_optional_current_company(
    session_token: Optional[str] = Header(None, alias="session-token"),
    db: AsyncSession = Depends(get_db)
) -> Optional[Company]:

    if not session_token:
        return None

    result = await db.execute(
        select(Company).where(
            Company.session_token == session_token
        )
    )

    return result.scalar_one_or_none()


async def get_current_company_from_query(
    session_token: str,
    db: AsyncSession = Depends(get_db)
) -> Company:

    result = await db.execute(
        select(Company).where(
            Company.session_token == session_token
        )
    )

    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session token"
        )

    return company

async def get_current_company_header2(
    company_session_token: Optional[str] = Header(None, alias="company-session-token"),
    db: AsyncSession = Depends(get_db)
) -> Company:

    if not company_session_token:
        raise HTTPException(status_code=401, detail="Company session token is missing")

    result = await db.execute(
        select(Company).where(Company.session_token == company_session_token)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=401, detail="Invalid or expired company session token")
    return company

# =============================================================================
# TEAM AUTHENTICATION
# =============================================================================

async def get_current_team(
    session_token: Optional[str] = Header(None, alias="session-token"),
    db: AsyncSession = Depends(get_db)
) -> Team:

    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Session token is missing"
        )

    result = await db.execute(
        select(Team).where(
            Team.session_token == session_token
        )
    )

    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session token"
        )

    return team


async def get_optional_current_team(
    session_token: Optional[str] = Header(None, alias="session-token"),
    db: AsyncSession = Depends(get_db)
) -> Optional[Team]:

    if not session_token:
        return None

    result = await db.execute(
        select(Team).where(
            Team.session_token == session_token
        )
    )

    return result.scalar_one_or_none()


async def get_current_team_from_query(
    session_token: str,
    db: AsyncSession = Depends(get_db)
) -> Team:

    result = await db.execute(
        select(Team).where(
            Team.session_token == session_token
        )
    )

    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session token"
        )

    return team


# =============================================================================
# VERFIED TEAM AUTHENTICATION
# =============================================================================

from fastapi import Depends, HTTPException

from database import models
from utils.authentication import get_current_company, get_current_team


async def get_verified_team(
    current_team: Team = Depends(get_current_team),                 
    current_company: Company = Depends(get_current_company_header2),
) -> Team:
    if current_team.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="This team does not belong to the authenticated company.")
    return current_team
