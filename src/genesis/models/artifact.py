from __future__ import annotations

import uuid
from enum import StrEnum, auto
from typing import Any

from sqlalchemy import Enum, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genesis.db.base import Base
from genesis.models.mixins import TimestampMixin


class ArtifactType(StrEnum):
    TRANSCRIPT_JSON = auto()
    SCENE_JSON = auto()
    CHAPTER_JSON = auto()
    COMBINED_VIDEO = auto()
    LOG = auto()


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Artifact(TimestampMixin, Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=_uuid,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("run.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, name="artifact_type"),
        nullable=False,
    )
    s3_key: Mapped[str] = mapped_column(String(length=512), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    run: Mapped["Run"] = relationship(back_populates="artifacts")
