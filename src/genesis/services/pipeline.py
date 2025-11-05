from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import selectinload

from genesis.models import (
    Chapter,
    MediaFile,
    Project,
    ProjectStatus,
    Run,
    RunState,
    Scene,
)
from genesis.services.assembly import AssemblyService
from genesis.services.base import ServiceBase
from genesis.services.chapters import ChapterService
from genesis.services.narration import NarrationService
from genesis.services.scene_detection import SceneDetectionService
from genesis.services.transcription import TranscriptionService


class ProjectPipelineService(ServiceBase):
    """Coordinates the end-to-end processing pipeline for a project."""

    async def process_project(
        self,
        project_id: uuid.UUID,
        run_id: uuid.UUID | None = None,
        *,
        voiceover_path: Path | None = None,
        voiceover_offset: float = 0.0,
        voiceover_gain: float = 1.0,
        bed_gain: float = 0.3,
    ) -> Run:
        project = await self._load_project(project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found")

        run = await self._get_or_create_run(project_id, run_id)
        await self._update_project_status(project, ProjectStatus.PROCESSING)
        await self._transition_run(run, RunState.VALIDATING)

        step_details: dict[str, Any] = run.step_details or {}

        try:
            self._validate_project_inputs(project)

            await self._transition_run(run, RunState.TRANSCRIBING)
            transcripts = await TranscriptionService(self.session).transcribe_project(project_id)
            await self.session.commit()
            step_details["transcription"] = {
                "transcripts_created": len(transcripts),
                "media_files": [str(t.media_file_id) for t in transcripts],
            }
            await self._save_step_details(run, step_details)

            await self._transition_run(run, RunState.SCENE_DETECTING)
            scenes = await SceneDetectionService(self.session).detect_scenes(project_id)
            await self.session.commit()
            step_details["scene_detection"] = {
                "scenes_created": len(scenes),
                "captions_created": len(
                    [s for s in scenes if s.metadata_json and s.metadata_json.get("caption")]
                ),
            }
            await self._save_step_details(run, step_details)

            await self._transition_run(run, RunState.CHAPTERIZING)
            chapters = await ChapterService(self.session).build_chapters(project_id)
            await self.session.commit()
            step_details["chapters"] = {"chapters_created": len(chapters)}
            await self._save_step_details(run, step_details)

            voiceover_wav: Path | None = None
            if voiceover_path is not None:
                voiceover_artifact, voiceover_wav = await NarrationService(self.session).register_voiceover(
                    project_id,
                    run.id,
                    voiceover_path,
                    offset_seconds=voiceover_offset,
                    voiceover_gain=voiceover_gain,
                    bed_gain=bed_gain,
                )
                await self.session.commit()
                step_details["voiceover"] = {
                    "artifact_id": str(voiceover_artifact.id),
                    "wav_path": voiceover_artifact.metadata_json.get("wav_path") if voiceover_artifact.metadata_json else voiceover_artifact.s3_key,
                    "offset_seconds": voiceover_offset,
                    "voiceover_gain": voiceover_gain,
                    "bed_gain": bed_gain,
                }
                await self._save_step_details(run, step_details)

            await self._transition_run(run, RunState.ASSEMBLING)
            artifact = await AssemblyService(self.session).assemble(
                project_id,
                run.id,
                voiceover_wav=voiceover_wav,
                voiceover_offset=voiceover_offset,
                voiceover_gain=voiceover_gain,
                bed_gain=bed_gain,
            )
            await self.session.commit()
            step_details["assembly"] = {
                "artifact_id": str(artifact.id),
                "artifact_path": artifact.s3_key,
            }
            await self._save_step_details(run, step_details)

        except Exception as exc:  # pragma: no cover - defensive path
            run.error_message = str(exc)
            await self._transition_run(run, RunState.FAILED, ended=True)
            await self._update_project_status(project, ProjectStatus.FAILED)
            await self.session.commit()
            raise

        await self._transition_run(run, RunState.COMPLETED, ended=True)
        await self._update_project_status(project, ProjectStatus.COMPLETED)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def _load_project(self, project_id: uuid.UUID) -> Project | None:
        return await self.session.get(
            Project,
            project_id,
            options=(
                selectinload(Project.media_files).selectinload(MediaFile.transcript),
                selectinload(Project.scenes),
                selectinload(Project.chapters).selectinload(Chapter.scenes),
            ),
        )

    async def _get_or_create_run(self, project_id: uuid.UUID, run_id: uuid.UUID | None) -> Run:
        if run_id:
            run = await self.session.get(Run, run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")
            return run

        run = Run(
            project_id=project_id,
            state=RunState.PENDING,
            started_at=datetime.utcnow(),
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def _transition_run(
        self,
        run: Run,
        state: RunState,
        *,
        ended: bool = False,
    ) -> None:
        run.state = state
        if state == RunState.PENDING and run.started_at is None:
            run.started_at = datetime.utcnow()
        if ended:
            run.ended_at = datetime.utcnow()
        await self.session.commit()

    async def _save_step_details(self, run: Run, details: dict[str, Any]) -> None:
        run.step_details = details
        await self.session.commit()

    async def _update_project_status(self, project: Project, status: ProjectStatus) -> None:
        project.status = status
        await self.session.commit()

    def _validate_project_inputs(self, project: Project) -> None:
        if not project.media_files:
            raise ValueError("Project has no media files to process")
