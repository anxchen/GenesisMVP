from __future__ import annotations

import uuid
from enum import StrEnum, auto
from typing import List

from sqlalchemy import CheckConstraint, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genesis.db.base import Base
from genesis.models.mixins import TimestampMixin


class ProjectStatus(StrEnum):
    DRAFT = auto()
    UPLOADING = auto()
    READY = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Project(TimestampMixin, Base):
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(length=255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(length=1024), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        nullable=False,
        default=ProjectStatus.DRAFT,
    )

    media_files: Mapped[List["MediaFile"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    scenes: Mapped[List["Scene"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    chapters: Mapped[List["Chapter"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    runs: Mapped[List["Run"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("length(title) > 0", name="ck_projects_title_non_empty"),
    )
