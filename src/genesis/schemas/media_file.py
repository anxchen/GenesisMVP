from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from genesis.models.media_file import MediaFileStatus


class MediaFileCreate(BaseModel):
    original_filename: str = Field(min_length=1, max_length=255)
    s3_key: str = Field(min_length=1, max_length=512)
    duration_ms: int | None = Field(default=None, ge=0)
    checksum: str | None = Field(default=None, max_length=128)
    mime_type: str | None = Field(default=None, max_length=128)


class MediaFileRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    original_filename: str
    s3_key: str
    duration_ms: int | None
    status: MediaFileStatus
    uploaded_at: datetime | None
    checksum: str | None
    mime_type: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
