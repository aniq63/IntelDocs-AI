from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from utils.settings import get_settings
from utils.logger import logging as logger
from sqlalchemy.engine.url import make_url



settings = get_settings()


database_url = settings.database_url.strip()
# Normalize common Postgres URL forms to use asyncpg for async SQLAlchemy on Windows
# Prefer asyncpg driver; replace psycopg if present to avoid Windows ProactorEventLoop issues
if "+psycopg" in database_url and "+asyncpg" not in database_url:
    database_url = database_url.replace("+psycopg", "+asyncpg")

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql://"):
    if "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


url_obj = make_url(database_url)
connect_args = {}

# Handle statement_cache_size specifically
if "statement_cache_size" in url_obj.query:
    # We must remove it from the URL string to avoid string-typing conflicts
    # Reconstruct URL without this param
    new_query = {k: v for k, v in url_obj.query.items() if k != "statement_cache_size"}
    url_obj = url_obj._replace(query=new_query)
    # Pass strictly as integer in connect_args
    connect_args["statement_cache_size"] = 0

# Also enforce it for Supabase transaction pooler if not present
if "statement_cache_size" not in connect_args:
    connect_args["statement_cache_size"] = 0


# Create async engine
try:
    engine = create_async_engine(
        url_obj,
        echo=settings.debug,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    # logger.info("Database engine created successfully.")
except Exception as e:
    # Obfuscate password in URL for logging
    safe_url = str(url_obj).replace(url_obj.password or "___", "****") if url_obj.password else str(url_obj)
    logger.error(f"Failed to create database engine with URL: {safe_url}. Error: {e}")
    raise

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get database session.
    Automatically handles session lifecycle with proper error handling.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables.
    Called on application startup.
    """
    pass


async def close_db():
    """
    Close database connections.
    Called on application shutdown.
    """
    await engine.dispose()
