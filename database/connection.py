from typing import AsyncGenerator

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from utils.logger import logging as logger
from utils.settings import get_settings


settings = get_settings()


def normalize_database_url(database_url: str) -> str:
    """
    Normalize PostgreSQL URLs for SQLAlchemy + asyncpg.

    - Convert plain postgres/postgresql URLs to asynchronous asyncpg URLs.
    - Convert psycopg URLs to asyncpg URLs.
    - For Supabase pooler endpoints, force the pgbouncer-compatible settings
      that the pooler expects (SSL and transaction-pooler defaults).
    """

    database_url = database_url.strip()

    # Normalize PostgreSQL URLs for async SQLAlchemy.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql+asyncpg://",
            1,
        )

    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

    elif "+psycopg" in database_url and "+asyncpg" not in database_url:
        database_url = database_url.replace(
            "+psycopg",
            "+asyncpg",
        )

    url_obj = make_url(database_url)

    # Supabase pooler endpoints require SSL and pgbouncer-compatible settings.
    if url_obj.host and ".pooler.supabase.com" in url_obj.host:
        query = dict(url_obj.query)
        query["sslmode"] = "require"
        query["pgbouncer"] = "true"

        # Supabase's transaction pooler generally uses port 6543.
        if url_obj.port in (None, 5432):
            url_obj = url_obj._replace(port=6543)

        url_obj = url_obj._replace(query=query)

    return str(url_obj)


# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------

database_url = normalize_database_url(settings.database_url)


# ---------------------------------------------------------------------------
# Connection arguments
# ---------------------------------------------------------------------------

url_obj = make_url(database_url)

connect_args = {
    # Disable asyncpg prepared-statement caching.
    # This is important when using Supabase/Supavisor poolers.
    "statement_cache_size": 0,
}


# Remove statement_cache_size from the URL if it was supplied there.
if "statement_cache_size" in url_obj.query:
    new_query = {
        key: value
        for key, value in url_obj.query.items()
        if key != "statement_cache_size"
    }

    url_obj = url_obj._replace(query=new_query)


# ---------------------------------------------------------------------------
# SQLAlchemy async engine
# ---------------------------------------------------------------------------

try:
    engine = create_async_engine(
        url_obj,
        echo=settings.debug,

        # Check that an existing connection is still alive
        # before giving it to the application.
        pool_pre_ping=True,

        # Keep the application pool conservative.
        # This is especially important when using Supabase/Supavisor.
        pool_size=5,
        max_overflow=0,

        # Wait up to 15 seconds for an available connection.
        pool_timeout=15,

        # Recycle connections periodically.
        pool_recycle=1800,

        connect_args=connect_args,
    )

except Exception as e:
    # Never expose the database password in logs.
    safe_url = (
        str(url_obj).replace(
            url_obj.password or "___",
            "****",
        )
        if url_obj.password
        else str(url_obj)
    )

    logger.error(
        f"Failed to create database engine with URL: "
        f"{safe_url}. Error: {e}"
    )

    raise


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# SQLAlchemy Base
# ---------------------------------------------------------------------------

Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI database dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session to a FastAPI request.

    The session is automatically closed after the request.
    Transactions should be committed explicitly by routes/services
    that modify the database.
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session

        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Database lifecycle
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """
    Initialize database resources.

    Tables should preferably be managed using Alembic migrations
    rather than creating them automatically here.
    """
    pass


async def close_db() -> None:
    """
    Dispose of the SQLAlchemy connection pool during application shutdown.
    """

    await engine.dispose()