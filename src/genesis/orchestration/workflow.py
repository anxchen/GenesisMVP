from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from genesis.models.run import Run

logger = structlog.get_logger(__name__)


class WorkflowOrchestrator:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def enqueue(self, run: Run) -> None:
        """Placeholder Step Functions invocation."""
        logger.info(
            "workflow.enqueue",
            run_id=str(run.id),
            project_id=str(run.project_id),
            state=run.state,
        )
        # TODO: Connect to AWS Step Functions StartExecution call.
