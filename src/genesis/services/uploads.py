from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select

from genesis.models.media_file import MediaFile, MediaFileStatus
from genesis.models.project import Project
from genesis.schemas.upload import (
    PresignedUpload,
    UploadFinalizeRequest,
    UploadFinalizeResponse,
    UploadPresignRequest,
    UploadPresignResponse,
)
from genesis.services.base import ServiceBase


class UploadService(ServiceBase):
    async def _get_project(self, project_id: uuid.UUID) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def generate_presigned_urls(
        self,
        project_id: uuid.UUID,
        payload: UploadPresignRequest,
    ) -> UploadPresignResponse | None:
        project = await self._get_project(project_id)
        if project is None:
            return None

        # TODO: integrate with real S3 presigning via boto3/aioboto3
        uploads: list[PresignedUpload] = []
        expiration_seconds = 900
        for filename in payload.filenames:
            s3_key = f"projects/{project_id}/raw/{uuid.uuid4()}-{filename}"
            uploads.append(
                PresignedUpload(
                    filename=filename,
                    upload_url=f"https://example-bucket.s3.amazonaws.com/{s3_key}",
                    fields=None,
                    headers={"x-amz-meta-project-id": str(project_id)},
                    expires_in=expiration_seconds,
                )
            )

        return UploadPresignResponse(uploads=uploads)

    async def finalize_uploads(
        self,
        project_id: uuid.UUID,
        payload: UploadFinalizeRequest,
    ) -> UploadFinalizeResponse | None:
        project = await self._get_project(project_id)
        if project is None:
            return None

        media_file_ids: list[uuid.UUID] = []
        for entry in payload.uploads:
            media_file = MediaFile(
                project_id=project_id,
                original_filename=entry.filename,
                s3_key=entry.s3_key,
                duration_ms=entry.duration_ms,
                status=MediaFileStatus.UPLOADED,
                uploaded_at=datetime.utcnow(),
                checksum=entry.checksum,
                mime_type=entry.mime_type,
            )
            self.session.add(media_file)
            media_file_ids.append(media_file.id)

        await self.session.commit()
        return UploadFinalizeResponse(project_id=project_id, media_file_ids=media_file_ids)
