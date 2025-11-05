from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select

from genesis.models.project import Project, ProjectStatus
from genesis.models.run import Run, RunState
from genesis.orchestration.workflow import WorkflowOrchestrator
from genesis.services.base import ServiceBase


class RunService(ServiceBase):
    async def _get_project(self, project_id: uuid.UUID) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def start_run(self, project_id: uuid.UUID) -> Run | None:
        project = await self._get_project(project_id)
        if project is None:
            return None

        run = Run(
            project_id=project_id,
            state=RunState.PENDING,
            started_at=datetime.utcnow(),
        )
        project.status = ProjectStatus.PROCESSING
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)

        orchestrator = WorkflowOrchestrator(self.session)
        await orchestrator.enqueue(run)

        return run

    async def get_run(self, project_id: uuid.UUID, run_id: uuid.UUID) -> Run | None:
        result = await self.session.execute(
            select(Run).where(Run.id == run_id, Run.project_id == project_id)
        )
        return result.scalar_one_or_none()
