from __future__ import annotations

import argparse
import asyncio
import uuid
from pathlib import Path

from genesis.db.session import SessionLocal
from genesis.services.pipeline import ProjectPipelineService


async def _process(
    project_id: uuid.UUID,
    run_id: uuid.UUID | None,
    *,
    voiceover_path: Path | None = None,
    voiceover_offset: float = 0.0,
    voiceover_gain: float = 1.0,
    bed_gain: float = 0.3,
) -> None:
    async with SessionLocal() as session:
        orchestrator = ProjectPipelineService(session)
        run = await orchestrator.process_project(
            project_id,
            run_id,
            voiceover_path=voiceover_path,
            voiceover_offset=voiceover_offset,
            voiceover_gain=voiceover_gain,
            bed_gain=bed_gain,
        )
        print(
            "Run completed",
            {
                "run_id": str(run.id),
                "state": run.state,
                "step_details": run.step_details,
                "started_at": run.started_at,
                "ended_at": run.ended_at,
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Process a Genesis project pipeline run")
    parser.add_argument("--project-id", required=True, help="UUID of the project to process")
    parser.add_argument("--run-id", help="Optional existing run UUID")
    parser.add_argument("--voiceover", help="Path to narration audio file")
    parser.add_argument(
        "--voiceover-offset",
        type=float,
        default=0.0,
        help="Seconds to delay the narration relative to video start",
    )
    parser.add_argument(
        "--voiceover-gain",
        type=float,
        default=1.0,
        help="Multiplier applied to the narration track volume",
    )
    parser.add_argument(
        "--bed-gain",
        type=float,
        default=0.3,
        help="Multiplier applied to the natural audio when narration is mixed",
    )
    args = parser.parse_args()

    project_id = uuid.UUID(args.project_id)
    run_id = uuid.UUID(args.run_id) if args.run_id else None
    voiceover_path = Path(args.voiceover).expanduser() if args.voiceover else None

    asyncio.run(
        _process(
            project_id,
            run_id,
            voiceover_path=voiceover_path,
            voiceover_offset=args.voiceover_offset,
            voiceover_gain=args.voiceover_gain,
            bed_gain=args.bed_gain,
        )
    )


if __name__ == "__main__":
    main()
