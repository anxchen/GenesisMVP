from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genesis.api.deps import get_db_session
from genesis.schemas.upload import (
    UploadFinalizeRequest,
    UploadFinalizeResponse,
    UploadPresignRequest,
    UploadPresignResponse,
)
from genesis.services.uploads import UploadService

router = APIRouter(prefix="/v1/projects/{project_id}", tags=["uploads"])


@router.post("/uploads:presign", response_model=UploadPresignResponse)
async def generate_presigned_uploads(
    project_id: uuid.UUID,
    payload: UploadPresignRequest,
    session: AsyncSession = Depends(get_db_session),
) -> UploadPresignResponse:
    result = await UploadService(session).generate_presigned_urls(project_id, payload)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return result


@router.post(
    "/uploads:finalize",
    response_model=UploadFinalizeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def finalize_uploads(
    project_id: uuid.UUID,
    payload: UploadFinalizeRequest,
    session: AsyncSession = Depends(get_db_session),
) -> UploadFinalizeResponse:
    response = await UploadService(session).finalize_uploads(project_id, payload)
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return response
