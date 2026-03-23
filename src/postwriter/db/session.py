"""Async SQLAlchemy session factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from postwriter.config import Settings, get_settings


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    if settings is None:
        settings = get_settings()
    return create_async_engine(
        settings.db.url,
        echo=settings.db.echo,
        pool_size=settings.db.pool_size,
        max_overflow=settings.db.max_overflow,
    )


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session(
    engine: AsyncEngine | None = None,
    settings: Settings | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """Convenience context manager for a single async session."""
    if engine is None:
        engine = get_engine(settings)
    factory = get_session_factory(engine)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
