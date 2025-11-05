from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from genesis.models.project import Project, ProjectStatus
from genesis.schemas.project import ProjectCreate
from genesis.services.base import ServiceBase


class ProjectService(ServiceBase):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create_project(self, payload: ProjectCreate) -> Project:
        project = Project(
            title=payload.title,
            description=payload.description,
            status=ProjectStatus.DRAFT,
        )
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()
