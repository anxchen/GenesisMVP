from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from genesis.db.session import get_session


async def get_db_session() -> AsyncSession:
    async for session in get_session():
        yield session


DbSession = Depends(get_db_session)
