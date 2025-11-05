from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from genesis.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    status: ProjectStatus | None = None


class ProjectRead(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
