from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    ForeignKey,
    TIMESTAMP,
    JSON,
    func,
)

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector

from database.connection import Base


# =============================================================================
# COMPANY
# =============================================================================

class Company(Base):
    __tablename__ = "companies"

    id = Column(BigInteger, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False, index=True)

    password_hash = Column(String, nullable=False)

    session_token = Column(String)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    teams = relationship(
        "Team",
        back_populates="company",
        cascade="all, delete-orphan"
    )

    documents = relationship(
        "Document",
        back_populates="company",
        cascade="all, delete-orphan"
    )

    chunks = relationship(
        "DocumentChunk",
        back_populates="company",
        cascade="all, delete-orphan"
    )

    chat_sessions = relationship(
        "ChatSession",
        back_populates="company",
        cascade="all, delete-orphan"
    )

    chat_messages = relationship(
        "ChatMessage",
        back_populates="company",
        cascade="all, delete-orphan"
    )


# =============================================================================
# TEAM
# =============================================================================

class Team(Base):
    __tablename__ = "teams"

    id = Column(BigInteger, primary_key=True, index=True)

    company_id = Column(
        BigInteger,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name = Column(String, nullable=False)

    description = Column(Text)

    password_hash = Column(String)

    session_token = Column(String)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    company = relationship(
        "Company",
        back_populates="teams"
    )

    documents = relationship(
        "Document",
        back_populates="team",
        cascade="all, delete-orphan"
    )

    chunks = relationship(
        "DocumentChunk",
        back_populates="team",
        cascade="all, delete-orphan"
    )

    chat_sessions = relationship(
        "ChatSession",
        back_populates="team",
        cascade="all, delete-orphan"
    )

    chat_messages = relationship(
        "ChatMessage",
        back_populates="team",
        cascade="all, delete-orphan"
    )


# =============================================================================
# DOCUMENT
# =============================================================================

class Document(Base):
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True, index=True)

    company_id = Column(
        BigInteger,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    team_id = Column(
        BigInteger,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    doc_length = Column(BigInteger, nullable=False)

    source = Column(Text, nullable=False)

    visibility = Column(Text, nullable=False)

    status = Column(
        Text,
        nullable=False,
        default="ready"
    )

    uploaded_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    company = relationship(
        "Company",
        back_populates="documents"
    )

    team = relationship(
        "Team",
        back_populates="documents"
    )

    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )


# =============================================================================
# DOCUMENT CHUNK
# =============================================================================

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(BigInteger, primary_key=True, index=True)

    company_id = Column(
        BigInteger,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    team_id = Column(
        BigInteger,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    document_id = Column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    chunk_index = Column(
        BigInteger,
        nullable=False
    )

    page_number = Column(
        BigInteger
    )

    chunk_text = Column(
        Text,
        nullable=False
    )

    token_count = Column(
        BigInteger
    )

    # PostgreSQL Full Text Search column
    search_vector = Column(
        TSVECTOR
    )

    # IMPORTANT:
    # "metadata" is reserved by SQLAlchemy, so expose it as
    # metadata_json in Python while keeping the DB column name "metadata".
    metadata_json = Column(
        "metadata",
        JSON,
        nullable=True
    )

    # pgvector embedding
    embedding = Column(
        Vector(384)
    )

    company = relationship(
        "Company",
        back_populates="chunks"
    )

    team = relationship(
        "Team",
        back_populates="chunks"
    )

    document = relationship(
        "Document",
        back_populates="chunks"
    )


# =============================================================================
# CHAT SESSION
# =============================================================================

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(BigInteger, primary_key=True, index=True)

    company_id = Column(
        BigInteger,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    team_id = Column(
        BigInteger,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    visibility = Column(Text, nullable=False)

    title = Column(Text)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    company = relationship(
        "Company",
        back_populates="chat_sessions"
    )

    team = relationship(
        "Team",
        back_populates="chat_sessions"
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )


# =============================================================================
# CHAT MESSAGE
# =============================================================================

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, index=True)

    session_id = Column(
        BigInteger,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    company_id = Column(
        BigInteger,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    team_id = Column(
        BigInteger,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    question = Column(Text, nullable=False)

    answer = Column(Text, nullable=False)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    session = relationship(
        "ChatSession",
        back_populates="messages"
    )

    company = relationship(
        "Company",
        back_populates="chat_messages"
    )

    team = relationship(
        "Team",
        back_populates="chat_messages"
    )