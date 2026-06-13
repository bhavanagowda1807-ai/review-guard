"""Add actor_username and target_order_id to auditlog

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('auditlog', sa.Column('actor_username', sa.String(), nullable=True))
    op.add_column('auditlog', sa.Column('target_order_id', sa.Integer(), sa.ForeignKey('order.id'), nullable=True))


def downgrade() -> None:
    op.drop_column('auditlog', 'target_order_id')
    op.drop_column('auditlog', 'actor_username')
