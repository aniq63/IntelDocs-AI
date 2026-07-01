from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import warnings

from database.connection import get_db
from database import models, schemas
from utils.authentication import (
    get_current_company,
    get_current_team
)


# ----------------------------------------
# Company Knowldge
# ----------------------------------------
