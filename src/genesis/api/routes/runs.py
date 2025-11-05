from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genesis.api.deps import get_db_session
from genesis.schemas.run import RunRead
from genesis.services.runs import RunService

router = APIRouter(prefix="/v1/projects/{project_id}", tags=["runs"])


@router.post(":start", response_model=RunRead, status_code=status.HTTP_202_ACCEPTED)
async def start_run(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> RunRead:
    run = await RunService(session).start_run(project_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return RunRead.model_validate(run)


@router.get("/runs/{run_id}", response_model=RunRead)
async def get_run(
    project_id: uuid.UUID,
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> RunRead:
    run = await RunService(session).get_run(project_id, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return RunRead.model_validate(run)
