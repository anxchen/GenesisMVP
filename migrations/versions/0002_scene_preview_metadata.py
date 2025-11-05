"""add scene preview and metadata

Revision ID: 0002_scene_preview_metadata
Revises: 0001_initial
Create Date: 2024-06-01 01:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_scene_preview_metadata"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scene", sa.Column("preview_uri", sa.String(length=512), nullable=True))
    op.add_column("scene", sa.Column("metadata_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("scene", "metadata_json")
    op.drop_column("scene", "preview_uri")
