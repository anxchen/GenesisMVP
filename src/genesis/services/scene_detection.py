from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from scenedetect import ContentDetector, SceneManager, VideoManager
from sqlalchemy import delete, select

from genesis.config import get_settings
from genesis.ml.captioner import caption_image
from genesis.models import MediaFile, Scene as SceneModel
from genesis.services.base import ServiceBase
from genesis.utils.ffmpeg import extract_scene_frame


class SceneDetectionService(ServiceBase):
    """Detect scenes, extract representative frames, and caption them."""

    def __init__(self, session, detector: Any | None = None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(session)
        self.detector = detector or ContentDetector(threshold=27.0, min_scene_len=15)

    async def detect_scenes(self, project_id: uuid.UUID) -> list[SceneModel]:
        await self.session.execute(
            delete(SceneModel).where(SceneModel.project_id == project_id)
        )

        result = await self.session.execute(
            select(MediaFile).where(MediaFile.project_id == project_id)
        )
        media_files = list(result.scalars().unique())

        scenes: list[SceneModel] = []
        scene_index = 0
        for media in media_files:
            media_path = Path(media.s3_key)
            if not media_path.exists():
                raise FileNotFoundError(f"Media path not found for scene detection: {media_path}")

            detections = await self._run_detection(media_path)
            if not detections:
                fallback_duration = (media.duration_ms or 5000) / 1000
                detections = [(0.0, fallback_duration, {})]

            for start_s, end_s, metadata in detections:
                start_ms = int(start_s * 1000)
                end_ms = int(end_s * 1000)
                label = metadata.get("label") or f"Scene {scene_index + 1}: {media.original_filename}"

                scene_model = SceneModel(
                    project_id=project_id,
                    media_file_id=media.id,
                    index=scene_index,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    label=label,
                )
                self.session.add(scene_model)
                await self.session.flush()

                preview_path = await self._generate_preview(scene_model, media_path, start_s, end_s)
                caption = await asyncio.to_thread(caption_image, preview_path)

                metadata_payload: dict[str, Any] = {
                    **metadata,
                    "caption": caption,
                    "preview_uri": str(preview_path),
                }
                scene_model.preview_uri = str(preview_path)
                scene_model.metadata_json = metadata_payload
                scenes.append(scene_model)
                scene_index += 1

        await self.session.flush()
        return scenes

    async def _run_detection(self, media_path: Path) -> list[tuple[float, float, dict[str, Any]]]:
        def _detect() -> list[tuple[float, float, dict[str, Any]]]:
            video_manager = VideoManager([str(media_path)])
            scene_manager = SceneManager()
            scene_manager.add_detector(self.detector)

            try:
                video_manager.start()
                scene_manager.detect_scenes(frame_source=video_manager)
                scene_list = scene_manager.get_scene_list()
            finally:
                video_manager.release()

            detections: list[tuple[float, float, dict[str, Any]]] = []
            for scene in scene_list:
                start_time = scene[0]
                end_time = scene[1]
                detections.append(
                    (
                        start_time.get_seconds(),
                        end_time.get_seconds(),
                        {
                            "start_timecode": str(start_time),
                            "end_timecode": str(end_time),
                        },
                    )
                )
            return detections

        return await asyncio.to_thread(_detect)

    async def _generate_preview(
        self,
        scene: SceneModel,
        media_path: Path,
        start_seconds: float,
        end_seconds: float,
    ) -> Path:
        midpoint = (start_seconds + end_seconds) / 2 if end_seconds > start_seconds else start_seconds
        settings = get_settings()
        preview_dir = Path(settings.artifact_root) / "scene_previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        output_path = preview_dir / f"{scene.id}.jpg"

        await asyncio.to_thread(
            extract_scene_frame,
            media_path,
            midpoint,
            output_path,
        )
        return output_path
