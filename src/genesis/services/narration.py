from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import delete

from genesis.config import get_settings
from genesis.models import Artifact, ArtifactType, Run
from genesis.services.base import ServiceBase
from genesis.utils.ffmpeg import convert_audio_to_wav


class NarrationService(ServiceBase):
    """Manage voiceover assets and prepare them for assembly."""

    async def register_voiceover(
        self,
        project_id: uuid.UUID,
        run_id: uuid.UUID,
        source_audio: Path,
        *,
        offset_seconds: float = 0.0,
        voiceover_gain: float = 1.0,
        bed_gain: float = 0.3,
    ) -> tuple[Artifact, Path]:
        if not source_audio.exists():
            raise FileNotFoundError(f"Voiceover audio file not found: {source_audio}")

        run = await self.session.get(Run, run_id)
        if not run:
            raise ValueError("Run not found for narration registration.")

        settings = get_settings()
        voiceover_dir = Path(settings.artifact_root) / "voiceovers"
        voiceover_dir.mkdir(parents=True, exist_ok=True)
        wav_output = voiceover_dir / f"project_{project_id}_run_{run_id}.wav"

        # Convert to managed WAV asset
        await asyncio.to_thread(convert_audio_to_wav, source_audio, wav_output)

        metadata: dict[str, Any] = {
            "kind": "voiceover_audio",
            "original_path": str(source_audio),
            "wav_path": str(wav_output),
            "offset_seconds": offset_seconds,
            "voiceover_gain": voiceover_gain,
            "bed_gain": bed_gain,
        }

        # Remove prior voiceover artifacts for this run
        await self.session.execute(
            delete(Artifact).where(
                Artifact.run_id == run_id,
                Artifact.type == ArtifactType.LOG,
            )
        )

        artifact = Artifact(
            run_id=run_id,
            type=ArtifactType.LOG,
            s3_key=str(wav_output),
            metadata_json=metadata,
        )
        self.session.add(artifact)
        await self.session.flush()
        return artifact, wav_output
