"""feature store tables (ETL §21.6)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    # ### Lot 3 - Feature Store ETL (§21.6) ###
    op.create_table(
        'fs_daily_sales',
        sa.Column('sale_date', sa.Date(), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('quantity_sold', sa.Integer(), nullable=False),
        sa.Column('revenue', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('is_weekend', sa.Boolean(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'sale_date', 'product_id', 'branch_id', name='uq_fs_daily_sales_date_product_branch'
        ),
    )
    with op.batch_alter_table('fs_daily_sales', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_fs_daily_sales_sale_date'), ['sale_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_fs_daily_sales_product_id'), ['product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_fs_daily_sales_branch_id'), ['branch_id'], unique=False)

    op.create_table(
        'fs_customer_rfm',
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('recency_days', sa.Integer(), nullable=False),
        sa.Column('frequency', sa.Integer(), nullable=False),
        sa.Column('monetary', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', name='uq_fs_customer_rfm_customer_id'),
    )
    with op.batch_alter_table('fs_customer_rfm', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_fs_customer_rfm_customer_id'), ['customer_id'], unique=False)

    op.create_table(
        'fs_customer_credit_features',
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('nb_achats_credit_total', sa.Integer(), nullable=False),
        sa.Column('montant_moyen_achat', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('delai_moyen_remboursement_jours', sa.Float(), nullable=False),
        sa.Column('taux_retard', sa.Float(), nullable=False),
        sa.Column('anciennete_client_mois', sa.Float(), nullable=False),
        sa.Column('frequence_achat_mensuelle', sa.Float(), nullable=False),
        sa.Column('solde_du_actuel', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('is_technicien', sa.Boolean(), nullable=False),
        sa.Column('bon_payeur', sa.Boolean(), nullable=False),
        sa.Column('data_source', sa.String(length=16), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id', name='uq_fs_customer_credit_features_customer_id'),
        sa.CheckConstraint(
            "data_source IN ('REAL', 'SIMULATED')", name='ck_fs_credit_features_data_source'
        ),
    )
    with op.batch_alter_table('fs_customer_credit_features', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_fs_customer_credit_features_customer_id'), ['customer_id'], unique=False
        )

    op.create_table(
        'fs_transaction_features',
        sa.Column('sale_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('cashier_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=True),
        sa.Column('montant_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('remise_taux', sa.Integer(), nullable=False),
        sa.Column('heure_vente', sa.Integer(), nullable=False),
        sa.Column('ecart_vs_moyenne_produit', sa.Float(), nullable=False),
        sa.Column('ecart_vs_moyenne_vendeur', sa.Float(), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id']),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
        sa.ForeignKeyConstraint(['cashier_id'], ['users.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sale_id', name='uq_fs_transaction_features_sale_id'),
    )
    with op.batch_alter_table('fs_transaction_features', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_fs_transaction_features_sale_id'), ['sale_id'], unique=False
        )
    # ### end Alembic commands ###


def downgrade():
    # ### Lot 3 - Feature Store ETL (§21.6) ###
    with op.batch_alter_table('fs_transaction_features', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_fs_transaction_features_sale_id'))
    op.drop_table('fs_transaction_features')

    with op.batch_alter_table('fs_customer_credit_features', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_fs_customer_credit_features_customer_id'))
    op.drop_table('fs_customer_credit_features')

    with op.batch_alter_table('fs_customer_rfm', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_fs_customer_rfm_customer_id'))
    op.drop_table('fs_customer_rfm')

    with op.batch_alter_table('fs_daily_sales', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_fs_daily_sales_branch_id'))
        batch_op.drop_index(batch_op.f('ix_fs_daily_sales_product_id'))
        ba