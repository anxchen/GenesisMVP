from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from genesis.config import get_settings
from genesis.models import Artifact, ArtifactType, Run, Scene
from genesis.services.base import ServiceBase
from genesis.utils.ffmpeg import mix_voiceover, render_concatenation, trim_segment


class AssemblyService(ServiceBase):
    """Assemble detected scenes into a single rendered video artifact."""

    async def assemble(
        self,
        project_id: uuid.UUID,
        run_id: uuid.UUID,
        *,
        voiceover_wav: Path | None = None,
        voiceover_offset: float = 0.0,
        voiceover_gain: float = 1.0,
        bed_gain: float = 0.3,
    ) -> Artifact:
        await self.session.execute(
            delete(Artifact).where(
                Artifact.run_id == run_id, Artifact.type == ArtifactType.COMBINED_VIDEO
            )
        )

        run = await self.session.get(Run, run_id)
        if not run:
            raise ValueError("Run not found for assembly.")

        scenes = await self._load_scenes(project_id)
        if not scenes:
            raise ValueError("No scenes available for assembly.")

        settings = get_settings()
        render_dir = Path(settings.artifact_root) / "renders"
        render_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = render_dir / f"segments_{run_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        trimmed_segments: list[Path] = []
        for scene in scenes:
            media_path = Path(scene.media_file.s3_key)
            if not media_path.exists():
                raise FileNotFoundError(f"Scene media missing: {media_path}")

            start_seconds = scene.start_ms / 1000
            end_seconds = scene.end_ms / 1000
            output_segment = temp_dir / f"scene_{scene.index:04d}.mp4"

            await asyncio.to_thread(
                trim_segment,
                media_path,
                start_seconds,
                end_seconds,
                output_segment,
            )
            trimmed_segments.append(output_segment)

        combined_path = render_dir / f"project_{project_id}_run_{run_id}.mp4"
        await asyncio.to_thread(render_concatenation, trimmed_segments, combined_path)

        for segment in trimmed_segments:
            segment.unlink(missing_ok=True)
        try:
            temp_dir.rmdir()
        except OSError:
            pass

        final_path = combined_path
        if voiceover_wav:
            voiced_path = render_dir / f"project_{project_id}_run_{run_id}_voiceover.mp4"
            await asyncio.to_thread(
                mix_voiceover,
                combined_path,
                voiceover_wav,
                voiced_path,
                offset_seconds=voiceover_offset,
                voiceover_gain=voiceover_gain,
                bed_gain=bed_gain,
            )
            final_path = voiced_path
            combined_path.unlink(missing_ok=True)

        artifact = Artifact(
            run_id=run.id,
            type=ArtifactType.COMBINED_VIDEO,
            s3_key=str(final_path),
            metadata_json={
                "generator": "ffmpeg",
                "generated_at": datetime.utcnow().isoformat(),
                "scene_count": len(scenes),
                "voiceover_applied": bool(voiceover_wav),
            },
        )
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    async def _load_scenes(self, project_id: uuid.UUID) -> list[Scene]:
        result = await self.session.execute(
            select(Scene)
            .options(selectinload(Scene.media_file))
            .where(Scene.project_id == project_id)
            .order_by(Scene.index)
        )
        return list(result.scalars().unique())
