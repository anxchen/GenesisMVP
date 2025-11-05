from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///./genesis.db"


def _get_database_url() -> str:
    raw_url = os.getenv("DATABASE_URL")
    if raw_url:
        return raw_url
    return DEFAULT_SQLITE_URL


def create_engine() -> AsyncEngine:
    database_url = _get_database_url()
    return create_async_engine(database_url, future=True, echo=False)


engine = create_engine()
SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
