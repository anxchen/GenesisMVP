"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-06-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    project_status = sa.Enum(
        "DRAFT",
        "UPLOADING",
        "READY",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
        name="project_status",
    )
    media_file_status = sa.Enum(
        "PENDING",
        "UPLOADED",
        "PROCESSING",
        "READY",
        "FAILED",
        name="media_file_status",
    )
    run_state = sa.Enum(
        "PENDING",
        "VALIDATING",
        "TRANSCRIBING",
        "SCENE_DETECTING",
        "CHAPTERIZING",
        "ASSEMBLING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        name="run_state",
    )
    artifact_type = sa.Enum(
        "TRANSCRIPT_JSON",
        "SCENE_JSON",
        "CHAPTER_JSON",
        "COMBINED_VIDEO",
        "LOG",
        name="artifact_type",
    )

    project_status.create(op.get_bind(), checkfirst=True)
    media_file_status.create(op.get_bind(), checkfirst=True)
    run_state.create(op.get_bind(), checkfirst=True)
    artifact_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "project",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("status", project_status, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("length(title) > 0", name="ck_projects_title_non_empty"),
    )

    op.create_table(
        "mediafile",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("status", media_file_status, nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("s3_key"),
    )

    op.create_table(
        "run",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("state", run_state, nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("step_details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chapter",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "scene",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("media_file_id", sa.Uuid(), nullable=True),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["media_file_id"], ["mediafile.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "transcript",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("media_file_id", sa.Uuid(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("json_uri", sa.String(length=512), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["media_file_id"], ["mediafile.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chapterscene",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chapter_id", sa.Uuid(), nullable=False),
        sa.Column("scene_id", sa.Uuid(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapter.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scene_id"], ["scene.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "artifact",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("type", artifact_type, nullable=False),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["run.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("artifact")
    op.drop_table("chapterscene")
    op.drop_table("transcript")
    op.drop_table("scene")
    op.drop_table("chapter")
    op.drop_table("run")
    op.drop_table("mediafile")
    op.drop_table("project")

    artifact_type = sa.Enum(name="artifact_type")
    run_state = sa.Enum(name="run_state")
    media_file_status = sa.Enum(name="media_file_status")
    project_status = sa.Enum(name="project_status")

    artifact_type.drop(op.get_bind(), checkfirst=True)
    run_state.drop(op.get_bind(), checkfirst=True)
    media_file_status.drop(op.get_bind(), checkfirst=True)
    project_status.drop(op.get_bind(), checkfirst=True)
