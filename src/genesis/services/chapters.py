from __future__ import annotations

import uuid
from dataclasses import dataclass
from sqlalchemy import delete, select

from genesis.models import Chapter, ChapterScene, Scene
from genesis.services.base import ServiceBase


@dataclass
class ChapterResult:
    chapter: Chapter
    scenes: list[ChapterScene]


class ChapterService(ServiceBase):
    """Simple grouping that merges all scenes into a single chapter."""

    async def build_chapters(self, project_id: uuid.UUID) -> list[ChapterResult]:
        chapter_ids_subquery = select(Chapter.id).where(Chapter.project_id == project_id)
        await self.session.execute(
            delete(ChapterScene).where(ChapterScene.chapter_id.in_(chapter_ids_subquery))
        )
        await self.session.execute(delete(Chapter).where(Chapter.project_id == project_id))

        result = await self.session.execute(
            select(Scene).where(Scene.project_id == project_id).order_by(Scene.index)
        )
        scenes = list(result.scalars())

        if not scenes:
            return []

        chapter = Chapter(
            project_id=project_id,
            index=0,
            start_ms=min(scene.start_ms for scene in scenes),
            end_ms=max(scene.end_ms for scene in scenes),
            title="Bakery Crawl Highlight",
            description="Auto-generated chapter covering the full crawl.",
        )
        self.session.add(chapter)
        await self.session.flush()

        chapter_scenes: list[ChapterScene] = []
        for order_index, scene in enumerate(scenes):
            link = ChapterScene(
                chapter_id=chapter.id,
                scene_id=scene.id,
                order_index=order_index,
            )
            self.session.add(link)
            chapter_scenes.append(link)

        await self.session.flush()
        return [ChapterResult(chapter=chapter, scenes=chapter_scenes)]
