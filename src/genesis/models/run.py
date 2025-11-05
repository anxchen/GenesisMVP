from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum, auto
from typing import Any, List

from sqlalchemy import Enum, ForeignKey, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genesis.db.base import Base
from genesis.models.mixins import TimestampMixin


class RunState(StrEnum):
    PENDING = auto()
    VALIDATING = auto()
    TRANSCRIBING = auto()
    SCENE_DETECTING = auto()
    CHAPTERIZING = auto()
    ASSEMBLING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Run(TimestampMixin, Base):
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
    state: Mapped[RunState] = mapped_column(
        Enum(RunState, name="run_state"),
        default=RunState.PENDING,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(nullable=True)
    step_details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="runs")
    artifacts: Mapped[List["Artifact"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )
