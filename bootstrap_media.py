import asyncio, pathlib, uuid, datetime
from genesis.db.session import SessionLocal
from genesis.models import Project, ProjectStatus, MediaFile, MediaFileStatus

MEDIA_ROOT = pathlib.Path("sample_media")

async def seed_project_from_folder():
    async with SessionLocal() as session:
        project = Project(title="Bakery Crawl", status=ProjectStatus.READY)
        session.add(project)
        await session.flush()

        for clip in sorted(MEDIA_ROOT.glob("*.mp4")):
            session.add(
                MediaFile(
                    project_id=project.id,
                    original_filename=clip.name,
                    s3_key=str(clip),            # reference local path for now
                    duration_ms=None,            # fill in if you have metadata
                    status=MediaFileStatus.UPLOADED,
                    uploaded_at=datetime.datetime.utcnow(),
                )
            )
        await session.commit()
        print("Project created:", project.id)

asyncio.run(seed_project_from_folder())