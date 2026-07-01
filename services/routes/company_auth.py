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
    prefix="/Company-Authentication",
    tags=["Company Authentication"]
)


# ---------------------------------
# Company Registration Endpoint
# ---------------------------------

@router.post(
    "/register/company",
    response_model=schemas.CompanyResponse
)
async def register(
    company: schemas.CompanyCreate,
    db: AsyncSession = Depends(get_db)
):

    # Check if company already exists
    result = await db.execute(
        select(models.Company).where(
            (models.Company.name == company.name) |
            (models.Company.email == company.email)
        )
    )

    existing_company = result.scalar_one_or_none()

    if existing_company:
        raise HTTPException(
            status_code=400,
            detail="Company with this name or email already exists"
        )

    # Hash password
    hashed_password = hash_password(company.password)

    # Create company
    new_company = models.Company(
        name=company.name,
        email=company.email,
        password_hash=hashed_password
    )

    db.add(new_company)

    await db.commit()
    await db.refresh(new_company)

    return new_company


# ---------------------------------
# Company Login Endpoint
# ---------------------------------

@router.post(
    "/company/login",
    response_model=schemas.TokenResponse
)
async def company_login(
    company: schemas.CompanyLogin,
    db: AsyncSession = Depends(get_db)
):

    # Find company
    result = await db.execute(
        select(models.Company).where(
            models.Company.name == company.name
        )
    )

    company_record = result.scalar_one_or_none()

    if not company_record:
        raise HTTPException(
            status_code=401,
            detail="Incorrect company name or password"
        )

    # Verify password
    if not verify_password(
        company.password,
        company_record.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect company name or password"
        )

    # Generate session token
    token = generate_session_token()

    company_record.session_token = token

    await db.commit()
    await db.refresh(company_record)

    return {
        "access_token": token,
        "token_type": "simple"
    }


# ---------------------------------
# Company Logout Endpoint
# ---------------------------------

@router.post("/company/logout")
async def company_logout(
    current_company: models.Company = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout the current company.
    """

    current_company.session_token = None

    await db.commit()

    return {
        "message": "Successfully logged out"
    }

# ---------------------------------
# Company Profile Endpoint
# ---------------------------------

@router.get(
    "/company/profile",
    response_model=schemas.CompanyResponse
)
async def get_company_profile(
    current_company: models.Company = Depends(get_current_company)
):
    """
    Return the profile of the currently authenticated company.
    """

    return current_company