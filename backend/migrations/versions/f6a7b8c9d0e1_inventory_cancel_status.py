"""Ajout du statut ANNULE et cancelled_by_id sur stock_counts

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('stock_counts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cancelled_by_id', sa.String(36), nullable=True))
        batch_op.create_foreign_key(
            'fk_stock_counts_cancelled_by',
            'users', ['cancelled_by_id'], ['id']
        )
    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('stock_counts', schema=None) as batch_op:
        batch_op.drop_constraint('fk_stock_counts_cancelled_by', type_='foreignkey')
        batch_op.drop_column('cancelled_by_id')
    # ### end Alembic commands ###
