"""Add ON DELETE CASCADE to auditlog foreign key

Revision ID: 0003
Revises: 0002_add_reasoning_column
Create Date: 2026-06-09 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002_add_reasoning_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the existing foreign key constraint
    op.drop_constraint('auditlog_target_review_id_fkey', 'auditlog', type_='foreignkey')
    
    # Create new foreign key with ON DELETE CASCADE
    op.create_foreign_key(
        'auditlog_target_review_id_fkey',
        'auditlog',
        'review',
        ['target_review_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop the cascade foreign key
    op.drop_constraint('auditlog_target_review_id_fkey', 'auditlog', type_='foreignkey')
    
    # Restore the original foreign key without cascade
    op.create_foreign_key(
        'auditlog_target_review_id_fkey',
        'auditlog',
        'review',
        ['target_review_id'],
        ['id']
    )
