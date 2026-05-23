"""
Async database engine and session factory.

FastAPI routes receive a DB session via Depends(get_db).
The session is always closed after the request — even if an error occurs.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# Connection pool — reuses connections instead of opening one per query
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # logs SQL in the terminal when DEBUG=true
    pool_pre_ping=True,  # verifies connections before use (avoids stale connections)
)

# Factory that creates AsyncSession instances
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes.

    Usage (later steps):
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_connection() -> bool:
    """Run SELECT 1 to verify PostgreSQL is reachable."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
