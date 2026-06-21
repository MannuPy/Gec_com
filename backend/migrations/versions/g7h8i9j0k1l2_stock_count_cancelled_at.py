"""Ajoute cancelled_at a stock_counts

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-21 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'g7h8i9j0k1l2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('stock_counts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cancelled_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('stock_counts', schema=None) as batch_op:
        batch_op.drop_column('cancelled_at')
