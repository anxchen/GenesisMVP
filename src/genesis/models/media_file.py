from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum, auto
from typing import List

from sqlalchemy import Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genesis.db.base import Base
from genesis.models.mixins import TimestampMixin


class MediaFileStatus(StrEnum):
    PENDING = auto()
    UPLOADED = auto()
    PROCESSING = auto()
    READY = auto()
    FAILED = auto()


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class MediaFile(TimestampMixin, Base):
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
    original_filename: Mapped[str] = mapped_column(String(length=255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(length=512), nullable=False, unique=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[MediaFileStatus] = mapped_column(
        Enum(MediaFileStatus, name="media_file_status"),
        default=MediaFileStatus.PENDING,
        nullable=False,
    )
    uploaded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(length=128), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(length=128), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="media_files")
    transcript: Mapped["Transcript | None"] = relationship(
        back_populates="media_file",
        uselist=False,
        cascade="all, delete-orphan",
    )
    scenes: Mapped[List["Scene"]] = relationship(
        back_populates="media_file",
        cascade="all, delete-orphan",
    )
