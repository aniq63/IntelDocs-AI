from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime


# ------------------------------
# Company Authentication
# ------------------------------

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)
    email: EmailStr

class CompanyResponse(BaseModel):
    id: int
    name: str
    email: str
    model_config = ConfigDict(from_attributes=True)


class CompanyLogin(BaseModel):
    name : str
    password : str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ------------------------------
# Team Authentication
# ------------------------------

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    password: str = Field(..., min_length=6)


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)


class TeamResponse(BaseModel):
    id: int
    company_id: int
    name: str
    description: Optional[str]
    created_at: datetime

class TeamLogin(BaseModel):
    company_name: str
    team_name: str
    password: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 
    id: int
    company_id: int
    team_id: Optional[int] = None
    doc_length: int
    source: str
    visibility: str
    status: str
    uploaded_at: datetime

#------------------------------------
# CHAT 
# ----------------------------------


class ChatAskRequest(BaseModel):
    question: str
    # Omit to start a new session; pass an existing one to continue it.
    session_id: Optional[int] = None


class ChatAskResponse(BaseModel):
    session_id: int
    message_id: int
    question: str
    answer: str


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    visibility: str
    created_at: datetime
    updated_at: datetime


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str
    created_at: datetime




class CompanyOverviewOut(BaseModel):
    total_documents: int
    total_teams: int


class TeamOverviewOut(BaseModel):
    total_documents: int


class TeamSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime