from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from genesis.models.artifact import ArtifactType


class ArtifactRead(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    type: ArtifactType
    s3_key: str
    metadata_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
