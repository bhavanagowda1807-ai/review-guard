"""add reasoning column to review

Revision ID: 0002_add_reasoning_column
Revises: 0001_initial_schema
Create Date: 2026-06-05

"""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_reasoning_column"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "review",
        sa.Column("reasoning", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_column("review", "reasoning")
