from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from genesis.api.deps import get_db_session
from genesis.schemas.artifact import ArtifactRead
from genesis.services.artifacts import ArtifactService

router = APIRouter(prefix="/v1/projects/{project_id}", tags=["artifacts"])


@router.get("/artifacts", response_model=list[ArtifactRead])
async def list_artifacts(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[ArtifactRead]:
    artifacts = await ArtifactService(session).list_artifacts_for_project(project_id)
    if artifacts is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return [ArtifactRead.model_validate(artifact) for artifact in artifacts]
