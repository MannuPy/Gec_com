"""customer payments (RF-26)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    # ### Lot 3 - suivi des remboursements de crédit (RF-26, §20.6.2) ###
    op.create_table(
        'customer_payments',
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('sale_id', sa.String(length=36), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('recorded_by_id', sa.String(length=36), nullable=True),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id']),
        sa.ForeignKeyConstraint(['recorded_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount > 0', name='ck_customer_payment_amount_positive'),
        sa.CheckConstraint(
            "status IN ('PENDING', 'PAID', 'LATE', 'CANCELLED')",
            name='ck_customer_payment_status_allowed',
        ),
    )
    with op.batch_alter_table('customer_payments', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_customer_payments_customer_id'), ['customer_id'], unique=False
        )
    # ### end Alembic commands ###


def downgrade():
    # ### Lot 3 - suivi des remboursements de crédit (RF-26, §20.6.2) ###
    with op.batch_alter_table('customer_payments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_customer_payments_customer_id'))

    op.drop_table('