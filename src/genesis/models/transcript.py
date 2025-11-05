from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genesis.db.base import Base
from genesis.models.mixins import TimestampMixin


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Transcript(TimestampMixin, Base):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=_uuid,
    )
    media_file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("mediafile.id", ondelete="CASCADE"),
        nullable=False,
    )
    language: Mapped[str | None] = mapped_column(String(length=16), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    json_uri: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=None
    )

    media_file: Mapped["MediaFile"] = relationship(back_populates="transcript")
