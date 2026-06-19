"""offline sync: sales.channel + sales.updated_at, stock negatif controle

Revision ID: 7c2f9a1d3e5b
Revises: 590c9c3a2981
Create Date: 2026-06-14 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c2f9a1d3e5b'
down_revision = '590c9c3a2981'
branch_labels = None
depends_on = None


def upgrade():
    # ### Lot 2 - Mode hors-ligne PWA (RF-20, RG-28 a RG-30) ###
    with op.batch_alter_table('sales', schema=None) as batch_op:
        batch_op.add_column(sa.Column('channel', sa.String(length=10), nullable=False, server_default='ONLINE'))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
        batch_op.create_check_constraint('ck_sale_channel_allowed', "channel IN ('ONLINE', 'OFFLINE')")

    # RG-30 : en cas de conflit de synchronisation, le stock peut etre mis en
    # negatif de maniere controlee (regularisation manuelle par l'admin).
    with op.batch_alter_table('stock', schema=None) as batch_op:
        batch_op.drop_constraint('ck_stock_quantity_non_negative', type_='check')
    # ### end Alembic commands ###


def downgrade():
    # ### Lot 2 - Mode hors-ligne PWA (RF-20, RG-28 a RG-30) ###
    with op.batch_alter_table('stock', schema=None) as batch_op:
        batch_op.create_check_constraint('ck_stock_quantity_non_negative', 'quantity >= 0')

    with op.batch_alter_table('sales', schema=None) as batch_op:
        batch_op.drop_constraint('ck_sale_channel_allowed', type_='check')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('chann