"""companies registry (public schema, multi-tenant)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-15 09:30:00.000000

Cf. docs/27-MODELE-SAAS-MULTITENANT.md (§27.3) et docs/14-MPD.md (§14.2) :
table `public.companies`, registre global des tenants (entreprises
clientes), distincte des schemas `tenant_<slug>` qui portent les donnees
metier de chacune.

Portabilite MySQL (deploiement mono-tenant, ex. PythonAnywhere, cf.
docs/25-DEPLOIEMENT-CICD.md §25.9) : `CREATE SCHEMA` et l'argument
`schema='public'` sont des specificites PostgreSQL (un "schema" PostgreSQL
n'est pas une base de donnees). Sur MySQL, ces tables sont creees directement
dans la base applicative courante (pas de schema dedie) - cf.
app/models/company.py (`_PUBLIC_SCHEMA_ARGS`).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade():
    schema = "public" if _is_postgres() else None

    if schema:
        op.execute("CREATE SCHEMA IF NOT EXISTS public")

    op.create_table(
        'companies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('schema_name', sa.String(length=63), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=False),
        sa.Column('subscription_plan', sa.String(length=20), nullable=False),
        sa.Column('subscription_status', sa.String(length=20), nullable=False),
        sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "subscription_plan IN ('TRIAL','STANDARD','PRO','ENTERPRISE')",
            name='ck_companies_subscription_plan',
        ),
        sa.CheckConstraint(
            "subscription_status IN ('TRIAL','ACTIVE','SUSPENDED','CANCELLED')",
            name='ck_companies_subscription_status',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('schema_name'),
        schema=schema,
    )
    op.create_index(
        op.f('ix_companies_schema_name'),
        'companies',
        ['schema_name'],
        unique=False,
        schema=schema,
    )

    # Table d'index global email -> schema, utilisee par /auth/login pour
    # localiser le tenant d'un utilisateur sans scanner tous les schemas
    # (§27.7). Maintenue par l'application lors de la creation/suppression
    # d'utilisateurs (cf. app/utils/tenant.py).
    op.create_table(
        'user_index',
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('schema_name', sa.String(length=63), nullable=False),
        sa.PrimaryKeyConstraint('email'),
        schema=schema,
    )


def downgrade():
    schema = "public" if _is_postgres() else None

    op.drop_table('user_index', schema=schema)
    op.drop_index(op.f('ix_companies_schema_name', table_name='companies'))
    op.drop_table('companies')
    # ### end Alembic commands ###
