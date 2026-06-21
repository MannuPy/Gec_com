"""products: name_moore (RF-09) + name_phonetic (RF-08)

Revision ID: a1b2c3d4e5f6
Revises: 7c2f9a1d3e5b
Create Date: 2026-06-15 09:00:00.000000

"""
from alembic import op, context as alembic_context
import sqlalchemy as sa

from app.utils.phonetic import phonetic_code


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '7c2f9a1d3e5b'
branch_labels = None
depends_on = None


def upgrade():
    # ### Lot 3 - i18n moore + recherche phonetique (RF-08/RF-09) ###
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name_moore', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('name_phonetic', sa.String(length=255), nullable=True))
        batch_op.create_index(batch_op.f('ix_products_name_phonetic'), ['name_phonetic'], unique=False)

    # Calcule le code phonetique initial des produits existants (RF-08).
    # Les ecritures suivantes sont gerees par les event listeners SQLAlchemy
    # (cf. app/models/catalog.py).
    # En mode offline (`flask db upgrade --sql`), `op.get_bind()` renvoie un
    # objet "mock" qui ne peut pas executer des SELECT retournant des resultats
    # (cf. alembic.runtime.migration.MigrationContext.bind docstring). On
    # saute le backfill de donnees dans ce cas : il n'y a de toute facon
    # aucune ligne a retraiter lors d'une migration sur base vide.
    if alembic_context.is_offline_mode():
        return

    bind = op.get_bind()
    products = sa.table(
        'products',
        sa.column('id', sa.String),
        sa.column('name', sa.String),
        sa.column('name_phonetic', sa.String),
    )
    rows = bind.execute(sa.select(products.c.id, products.c.name)).fetchall()
    for product_id, name in rows:
        bind.execute(
            products.update()
            .where(products.c.id == product_id)
            .values(name_phonetic=phonetic_code(name))
        )
    # ### end Alembic commands ###


def downgrade():
    # ### Lot 3 - i18n moore + recherche phonetique (RF-08/RF-09) ###
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_products_name_phonetic'))
        batch_op.drop_column('name_phonetic')
        batch_op.drop_column('name_moore')
    # ### end Alembic commands ###
