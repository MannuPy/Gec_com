"""users: must_change_password (RF-05)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### Lot 3 - changement de mot de passe forcé à la 1re connexion (RF-05) ###
    # `server_default=sa.false()` : les comptes existants (déjà opérationnels)
    # ne sont pas impactés rétroactivement. Les nouveaux comptes créés par un
    # administrateur (cf. blueprints/users/routes.py::create_user) positionnent
    # explicitement `must_change_password=True`.
    # `sa.false()` (plutôt que `sa.text('false')`) est rendu par SQLAlchemy de
    # façon portable : `FALSE` sur PostgreSQL, `0` sur MySQL/MariaDB (où
    # `sa.Boolean()` correspond à `TINYINT(1)`).
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.false())
        )
    # ### end Alembic commands ###


def downgrade():
    # ### Lot 3 - changement de mot de passe forcé à la 1re connexion (RF-05) ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('must_change_password')
    # ### end Alembic commands ###
