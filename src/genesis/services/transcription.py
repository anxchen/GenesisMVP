from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from genesis.ml.whisper import get_whisper_model
from genesis.models import MediaFile, MediaFileStatus, Transcript
from genesis.services.base import ServiceBase


class TranscriptionService(ServiceBase):
    """Run Whisper transcription for each media file in a project."""

    async def transcribe_project(self, project_id: uuid.UUID) -> list[Transcript]:
        result = await self.session.execute(
            select(MediaFile).where(MediaFile.project_id == project_id)
        )
        media_files = list(result.scalars().unique())

        transcripts: list[Transcript] = []
        for media in media_files:
            if media.transcript:
                continue

            media_path = Path(media.s3_key)
            if not media_path.exists():
                raise FileNotFoundError(f"Media path not found for transcription: {media_path}")

            segments, info = await self._run_whisper(media_path)
            text = " ".join(segment["text"] for segment in segments).strip()

            transcript = Transcript(
                media_file_id=media.id,
                language=info.get("language"),
                text=text,
                json_uri=None,
                metadata_json={
                    "segments": segments,
                    "generated_at": datetime.utcnow().isoformat(),
                    "whisper_info": info,
                },
            )
            self.session.add(transcript)
            transcripts.append(transcript)

            duration = info.get("duration")
            if duration and media.duration_ms is None:
                media.duration_ms = int(duration * 1000)
            media.status = MediaFileStatus.READY

        await self.session.flush()
        return transcripts

    async def _run_whisper(self, media_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        model = get_whisper_model()

        def _transcribe() -> tuple[list[dict[str, Any]], dict[str, Any]]:
            segments_iter, info = model.transcribe(
                str(media_path),
                beam_size=5,
                vad_filter=True,
            )
            segments: list[dict[str, Any]] = []
            for seg in segments_iter:
                segments.append(
                    {
                        "id": seg.id,
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text.strip(),
                        "avg_logprob": seg.avg_logprob,
                        "temperature": seg.temperature,
                        "compression_ratio": seg.compression_ratio,
                    }
                )
            info_dict = {
                "duration": info.duration,
                "language": info.language,
                "language_probability": info.language_probability,
                "vad_probability": getattr(info, "vad_probability", None),
            }
            return segments, info_dict

        return await asyncio.to_thread(_transcribe)
