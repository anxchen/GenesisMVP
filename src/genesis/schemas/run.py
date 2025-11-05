from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from genesis.models.run import RunState


class RunCreate(BaseModel):
    pass


class RunRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    state: RunState
    started_at: datetime | None
    ended_at: datetime | None
    error_message: str | None
    step_details: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
