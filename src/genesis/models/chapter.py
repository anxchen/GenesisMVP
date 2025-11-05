from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genesis.db.base import Base
from genesis.models.mixins import TimestampMixin


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Chapter(TimestampMixin, Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=_uuid,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
    )
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(length=512), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="chapters")
    scenes: Mapped[list["ChapterScene"]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
    )
