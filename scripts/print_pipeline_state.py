import asyncio
import json
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from genesis.db.session import SessionLocal
from genesis.models import Artifact, Chapter, MediaFile, Project, Run, Scene, Transcript

async def dump(project_id: uuid.UUID) -> None:
    async with SessionLocal() as session:
        project = await session.get(Project, project_id)
        if project is None:
            raise SystemExit(f"Project {project_id} not found")

        runs = await session.execute(select(Run).where(Run.project_id == project_id))
        media_files = await session.execute(select(MediaFile).where(MediaFile.project_id == project_id))
        transcripts = await session.execute(
            select(Transcript)
            .join(MediaFile, Transcript.media_file_id == MediaFile.id)
            .where(MediaFile.project_id == project_id)
        )
        scenes = await session.execute(
            select(Scene).where(Scene.project_id == project_id).order_by(Scene.index)
        )
        chapters = await session.execute(
            select(Chapter).where(Chapter.project_id == project_id).order_by(Chapter.index)
        )
        artifacts = await session.execute(
            select(Artifact).join(Run).where(Run.project_id == project_id)
        )

        state = {
            "project": project.id,
            "runs": [row._asdict() for row in runs],
            "media_files": [row._asdict() for row in media_files],
            "transcripts": [row._asdict() for row in transcripts],
            "scenes": [row._asdict() for row in scenes],
            "chapters": [row._asdict() for row in chapters],
            "artifacts": [row._asdict() for row in artifacts],
        }
        print(json.dumps(state, indent=2, default=str))

if __name__ == "__main__":
    project_id = uuid.UUID(input("Project UUID: ").strip())
    asyncio.run(dump(project_id))
