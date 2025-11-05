from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .session import get_session

DatabaseSession = AsyncSession

__all__ = ["DatabaseSession", "get_session"]
