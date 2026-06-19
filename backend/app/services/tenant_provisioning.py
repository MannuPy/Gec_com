"""Provisioning d'un nouveau tenant (entreprise cliente) - RF-01.

Cf. docs/27-MODELE-SAAS-MULTITENANT.md §27.4 : à l'inscription d'une nouvelle
entreprise, on enregistre une ligne dans le registre central
`public.companies`, on crée un schéma PostgreSQL dédié, on y crée les tables
applicatives, on initialise le RBAC par défaut (rôles/permissions), un site
"Dépôt Central" et le compte ADMIN initial, puis on indexe cet administrateur
dans `public.user_index` (§27.7) afin que `/auth/login` puisse résoudre son
tenant.

Écart par rapport au pseudo-code de §27.4 : plutôt que de rejouer
l'historique complet des migrations Alembic schéma par schéma (coûteux à
maintenir pour RNF-06 : jusqu'à 200 tenants, et nécessitant une table
`alembic_version` par schéma), les tables sont créées directement à partir
des modèles SQLAlchemy courants via `MetaData.create_all()` avec un
`schema_translate_map` - chaque nouveau tenant démarre ainsi avec la
structure de données la plus récente.
"""
from sqlalchemy import text

from app.extensions import db
from app.models.auth import User
from app.models.catalog import Branch
from app.models.company import Company, UserIndex
from app.seed import seed_permissions_and_roles
from app.utils.db_dialect import is_postgres_engine
from app.utils.errors import ApiError
from app.utils.tenant import register_user_index, schema_name_for_company, set_search_path


def provision_tenant(
    company_name: str,
    contact_email: str,
    admin_full_name: str,
    admin_email: str,
    admin_password: str,
) -> tuple[Company, User]:
    """Crée une nouvelle entreprise cliente et son tenant dédié.

    Retourne le tuple `(company, admin_user)`. À l'issue de l'appel, le
    `search_path` PostgreSQL de la session courante est positionné sur le
    schéma du nouveau tenant (afin de permettre, par exemple, l'écriture
    immédiate d'une entrée de journal d'audit dans ce tenant) ; il sera
    réinitialisé à `public` par le middleware `reset_tenant_schema` en fin de
    requête (cf. app/middleware/tenant.py).
    """
    # L'inscription self-service (RF-01) crée un schéma PostgreSQL dédié par
    # tenant (§27.4) : fonctionnalité indisponible sur un déploiement
    # mono-tenant MySQL (ex. PythonAnywhere, cf. docs/25-DEPLOIEMENT-CICD.md
    # §25.9), où une seule base de données est utilisée pour l'entreprise
    # exploitante.
    if not is_postgres_engine(db.session.get_bind()):
        raise ApiError(
            "MULTI_TENANT_UNAVAILABLE",
            "L'inscription en self-service de nouvelles entreprises "
            "nécessite une base de données PostgreSQL (schema-per-tenant). "
            "Ce déploiement utilise une base mono-tenant.",
            status_code=503,
        )

    admin_email = admin_email.lower()
    contact_email = contact_email.lower()

    schema_name = schema_name_for_company(company_name)

    if Company.query.filter_by(schema_name=schema_name).first() is not None:
        raise ApiError(
            "COMPANY_ALREADY_EXISTS",
            "Une entreprise avec un nom très proche est déjà inscrite.",
            status_code=409,
        )

    if UserIndex.query.filter_by(email=admin_email).first() is not None:
        raise ApiError(
            "EMAIL_ALREADY_USED",
            "Un compte existe déjà avec cet email.",
            status_code=409,
        )

    # 1. Registre central (§27.3)
    company = Company(
        name=company_name,
        schema_name=schema_name,
        contact_email=contact_email,
        subscription_plan="TRIAL",
        subscription_status="TRIAL",
    )
    db.session.add(company)
    db.session.commit()

    # 2. Création du schéma PostgreSQL dédié (nom validé par
    # `schema_name_for_company` : préfixe `tenant_` + slug ASCII).
    db.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    db.session.commit()

    # 3. Création des tables applicatives dans le nouveau schéma à partir des
    # modèles courants (les tables explicitement rattachées au schéma
    # `public`, comme `companies`/`user_index`, ne sont pas affectées par le
    # schema_translate_map et existent déjà).
    tenant_engine = db.engine.execution_options(schema_translate_map={None: schema_name})
    db.metadata.create_all(bind=tenant_engine)

    # 4. RBAC par défaut, site initial et compte ADMIN, dans le schéma du
    # tenant. `set_search_path` est ré-appliqué avant chaque étape : certaines
    # fonctions de seed effectuent leurs propres `commit()`, ce qui peut
    # entraîner la libération de la connexion vers le pool entre deux
    # instructions (§27.9) et donc la perte du `SET search_path` courant.
    set_search_path(schema_name)
    roles_by_name = seed_permissions_and_roles()

    set_search_path(schema_name)
    depot = Branch(name="Dépôt Central", code="DEPOT", is_depot=True)
    db.session.add(depot)
    db.session.flush()

    set_search_path(schema_name)
    admin_user = User(
        email=admin_email,
        full_name=admin_full_name,
        role_id=roles_by_name["ADMIN"].id,
        branch_id=None,
        language="fr",
    )
    admin_user.set_password(admin_password)
    db.session.add(admin_user)
    db.session.flush()

    # 5. Index global email -> schéma (§27.7), dans 