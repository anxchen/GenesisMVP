from __future__ import annotations

import uuid
from pydantic import BaseModel, Field, model_validator


class UploadPresignRequest(BaseModel):
    filenames: list[str] = Field(min_length=1)
    content_types: list[str | None] | None = None

    @model_validator(mode="after")
    def validate_lengths(self) -> "UploadPresignRequest":
        if len(self.filenames) > 10:
            raise ValueError("filenames cannot exceed 10 entries per request")
        return self


class PresignedUpload(BaseModel):
    filename: str
    upload_url: str
    fields: dict[str, str] | None = None
    headers: dict[str, str] | None = None
    expires_in: int = Field(ge=1)


class UploadPresignResponse(BaseModel):
    uploads: list[PresignedUpload]


class UploadFinalizeRequest(BaseModel):
    uploads: list["UploadFinalizeEntry"]


class UploadFinalizeEntry(BaseModel):
    filename: str
    s3_key: str
    checksum: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    mime_type: str | None = Field(default=None, max_length=128)


class UploadFinalizeResponse(BaseModel):
    project_id: uuid.UUID
    media_file_ids: list[uuid.UUID]


UploadFinalizeRequest.model_rebuild()
