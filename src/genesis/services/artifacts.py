from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from genesis.models.artifact import Artifact
from genesis.models.project import Project
from genesis.models.run import Run
from genesis.services.base import ServiceBase


class ArtifactService(ServiceBase):
    async def list_artifacts_for_project(self, project_id: uuid.UUID) -> list[Artifact] | None:
        project_exists = await self.session.scalar(
            select(Project.id).where(Project.id == project_id)
        )
        if not project_exists:
            return None

        result = await self.session.execute(
            select(Artifact)
            .join(Run, Artifact.run_id == Run.id)
            .where(Run.project_id == project_id)
            .options(joinedload(Artifact.run))
        )
        return list(result.scalars().unique())
