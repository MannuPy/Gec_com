"""Script d'amorçage des données de référence (RBAC, sites, catalogue démo).

Exécuté au démarrage du conteneur `api` (cf. docker-compose.yml) via
`python -m app.seed`. Idempotent : peut être exécuté plusieurs fois sans
dupliquer les données (vérifie l'existence avant insertion).

Cf. 18-SECURITE.md §18.1 (matrice RBAC) et 15-DICTIONNAIRE-DES-DONNEES.md
pour le référentiel produit de démonstration.
"""
import os

from app import create_app
from app.extensions import db
from app.models import (
    Branch,
    Brand,
    Category,
    Company,
    Customer,
    Permission,
    Product,
    Role,
    RolePermission,
    Stock,
    User,
)
from app.utils.tenant import register_user_index

# ---------------------------------------------------------------------------
# RBAC : permissions atomiques (`<ressource>:<action>`) et rôles (RG-02/RG-03)
# ---------------------------------------------------------------------------

PERMISSIONS: list[tuple[str, str]] = [
    ("*", "Accès total (réservé au rôle ADMIN)"),
    ("users:read", "Consulter les utilisateurs et rôles"),
    ("users:write", "Créer/modifier les utilisateurs"),
    ("products:read", "Consulter le catalogue produit"),
    ("products:write", "Créer/modifier le catalogue produit"),
    ("stock:read", "Consulter les niveaux et mouvements de stock"),
    ("stock:write", "Effectuer des ajustements de stock"),
    ("suppliers:read", "Consulter les fournisseurs"),
    ("suppliers:write", "Créer/modifier les fournisseurs"),
    ("receptions:read", "Consulter les réceptions"),
    ("receptions:write", "Créer/valider les réceptions"),
    ("transfers:read", "Consulter les transferts"),
    ("transfers:write", "Créer/expédier/réceptionner les transferts"),
    ("sales:read", "Consulter l'historique des ventes"),
    ("sales:create", "Enregistrer une vente en caisse"),
    ("sales:refund", "Émettre un avoir sur une vente"),
    ("sales:approve_discount", "Approuver une remise nécessitant un accord (RG-23)"),
    ("customers:read", "Consulter les clients"),
    ("customers:write", "Créer/modifier les clients"),
    ("reports:read", "Consulter le tableau de bord et les indicateurs"),
    ("analytics:read", "Consulter les tableaux de bord analytiques et l'IA"),
    ("inventory:read", "Consulter les sessions d'inventaire physique"),
    ("inventory:write", "Créer et valider des sessions d'inventaire physique"),
    ("ml:train", "Déclencher l'entraînement des modèles ML"),
]

ROLE_DEFINITIONS: dict[str, dict] = {
    "ADMIN": {
        "description": "Administrateur : accès total, approbation des remises, gestion des utilisateurs.",
        "permissions": ["*"],
    },
    "MAGASINIER": {
        "description": "Magasinier : gestion du dépôt central, réceptions, transferts.",
        "permissions": [
            "products:read",
            "stock:read",
            "stock:write",
            "suppliers:read",
            "suppliers:write",
            "receptions:read",
            "receptions:write",
            "transfers:read",
            "transfers:write",
            "customers:read",
            "reports:read",
            "analytics:read",
            "inventory:read",
            "inventory:write",
        ],
    },
    "VENDEUR": {
        "description": "Vendeur : caisse (ventes) et stock de sa boutique de rattachement.",
        "permissions": [
            "products:read",
            "stock:read",
            "sales:read",
            "sales:create",
            "customers:read",
            "customers:write",
            "transfers:read",
            "transfers:write",
            "reports:read",
            "analytics:read",
        ],
    },
}


def seed_permissions_and_roles() -> dict[str, Role]:
    permissions_by_code: dict[str, Permission] = {}
    for code, description in PERMISSIONS:
        permission = Permission.query.filter_by(code=code).first()
        if permission is None:
            permission = Permission(code=code, description=description)
            db.session.add(permission)
            db.session.flush()
        permissions_by_code[code] = permission

    roles_by_name: dict[str, Role] = {}
    for name, definition in ROLE_DEFINITIONS.items():
        role = Role.query.filter_by(name=name).first()
        if role is None:
            role = Role(name=name, description=definition["description"])
            db.session.add(role)
            db.session.flush()

        existing_permission_ids = {
            rp.permission_id for rp in RolePermission.query.filter_by(role_id=role.id).all()
        }
        for code in definition["permissions"]:
            permission = permissions_by_code[code]
            if permission.id not in existing_permission_ids:
                db.session.add(RolePermission(role_id=role.id, permission_id=permission.id))

        roles_by_name[name] = role

    db.session.commit()
    return roles_by_name


# ---------------------------------------------------------------------------
# Sites (RG-01 : un dépôt central + N boutiques)
# ---------------------------------------------------------------------------

BRANCHES: list[dict] = [
    {"name": "Dépôt Central", "code": "DEPOT", "is_depot": True, "address": "Zone industrielle, Ouagadougou"},
    {"name": "Boutique Tanghin", "code": "OUA-TAN", "is_depot": False, "address": "Tanghin, Ouagadougou"},
    {"name": "Boutique Gounghin", "code": "OUA-GOU", "is_depot": False, "address": "Gounghin, Ouagadougou"},
]


def seed_branches() -> dict[str, Branch]:
    branches_by_code: dict[str, Branch] = {}
    for data in BRANCHES:
        branch = Branch.query.filter_by(code=data["code"]).first()
        if branch is None:
            branch = Branch(**data)
            db.session.add(branch)
            db.session.flush()
        branches_by_code[data["code"]] = branch

    db.session.commit()
    return branches_by_code


# ---------------------------------------------------------------------------
# Utilisateurs de démonstration
# ---------------------------------------------------------------------------

def seed_users(roles_by_name: dict[str, Role], branches_by_code: dict[str, Branch]) -> None:
    admin_email = os.environ.get("SEED_ADMIN_EMAIL", "admin@gescom-bf.bf").lower()
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "Admin#2026")

    demo_users = [
        {
            "email": admin_email,
            "password": admin_password,
            "full_name": "Administrateur Système",
            "role": "ADMIN",
            "branch_code": None,
        },
        {
            "email": "magasinier@gescom-bf.bf",
            "password": "Magasinier#2026",
            "full_name": "Issa Kaboré (Magasinier)",
            "role": "MAGASINIER",
            "branch_code": "DEPOT",
        },
        {
            "email": "vendeur@gescom-bf.bf",
            "password": "Vendeur#2026",
            "full_name": "Aïcha Ouédraogo (Vendeuse)",
            "role": "VENDEUR",
            "branch_code": "OUA-TAN",
        },
    ]

    for data in demo_users:
        user = User.query.filter_by(email=data["email"]).first()
        if user is None:
            branch = branches_by_code[data["branch_code"]] if data["branch_code"] else None
            user = User(
                email=data["email"],
                full_name=data["full_name"],
                role_id=roles_by_name[data["role"]].id,
                branch_id=branch.id if branch else None,
                language="fr",
            )
            user.set_password(data["password"])
            db.session.add(user)

        # Index global email -> schema (§27.7) : les comptes de démonstration
        # appartiennent au tenant par défaut (V1 mono-tenant, schéma `public`).
        register_user_index(data["email"], "public")

    db.session.commit()


# ---------------------------------------------------------------------------
# Registre des tenants (multi-tenant SaaS, §27.3) : enregistre le tenant
# "historique" V1 mono-tenant (schéma `public`) dans `public.companies` afin
# que /auth/login et le middleware `set_tenant_schema` disposent d'une
# entrée cohérente pour ce tenant.
# ---------------------------------------------------------------------------

def seed_default_company() -> None:
    schema_name = "public"
    company = Company.query.filter_by(schema_name=schema_name).first()
    if company is None:
        company = Company(
            name=os.environ.get("COMPANY_NAME", "Gescom BF"),
            schema_name=schema_name,
            contact_email=os.environ.get("SEED_ADMIN_EMAIL", "admin@gescom-bf.bf").lower(),
            subscription_plan="ENTERPRISE",
            subscription_status="ACTIVE",
        )
        db.session.add(company)
        db.session.commit()


# ---------------------------------------------------------------------------
# Catalogue de démonstration (quincaillerie)
# ---------------------------------------------------------------------------

CATEGORIES = ["Visserie", "Peinture", "Plomberie", "Électricité", "Matériaux de construction", "Outillage"]
BRANDS = ["SOBA", "Dangote", "Tata", "CIMFASO", "Generic"]

PRODUCTS: list[dict] = [
    {
        "sku": "CIM-DAN-50",
        "name": "Ciment Dangote 50kg",
        "category": "Matériaux de construction",
        "brand": "Dangote",
        "unit": "SAC",
        "purchase_price": "4200",
        "simple_price": "4800",
        "technician_price": "4600",
        "min_stock_threshold": 50,
    },
    {
        "sku": "FER-T8-12M",
        "name": "Fer à béton torsadé Ø8 (barre 12m)",
        "category": "Matériaux de construction",
        "brand": "Generic",
        "unit": "UNITE",
        "purchase_price": "3500",
        "simple_price": "4000",
        "technician_price": "3800",
        "min_stock_threshold": 30,
    },
    {
        "sku": "PEI-SOBA-BLANC-20L",
        "name": "Peinture SOBA blanc mat 20L",
        "category": "Peinture",
        "brand": "SOBA",
        "unit": "BOITE",
        "purchase_price": "18000",
        "simple_price": "21000",
        "technician_price": "19500",
        "min_stock_threshold": 10,
    },
    {
        "sku": "VIS-6X40-BTE",
        "name": "Boîte de vis à bois 6x40mm (200 pcs)",
        "category": "Visserie",
        "brand": "Generic",
        "unit": "BOITE",
        "purchase_price": "1500",
        "simple_price": "2000",
        "technician_price": "1800",
        "min_stock_threshold": 20,
    },
    {
        "sku": "TUB-PVC-110-4M",
        "name": "Tube PVC évacuation Ø110mm (4m)",
        "category": "Plomberie",
        "brand": "Generic",
        "unit": "UNITE",
        "purchase_price": "6500",
        "simple_price": "7800",
        "technician_price": "7200",
        "min_stock_threshold": 15,
    },
    {
        "sku": "CAB-2X5-100M",
        "name": "Câble électrique 2x5mm² (rouleau 100m)",
        "category": "Électricité",
        "brand": "CIMFASO",
        "unit": "UNITE",
        "purchase_price": "45000",
        "simple_price": "52000",
        "technician_price": "49000",
        "min_stock_threshold": 5,
    },
    {
        "sku": "MAR-1KG",
        "name": "Marteau de menuisier 1kg",
        "category": "Outillage",
        "brand": "Tata",
        "unit": "UNITE",
        "purchase_price": "3000",
        "simple_price": "4000",
        "technician_price": "3500",
        "min_stock_threshold": 8,
    },
]

INITIAL_STOCK: dict[str, dict[str, int]] = {
    "CIM-DAN-50": {"DEPOT": 500, "OUA-TAN": 80, "OUA-GOU": 60},
    "FER-T8-12M": {"DEPOT": 300, "OUA-TAN": 40, "OUA-GOU": 25},
    "PEI-SOBA-BLANC-20L": {"DEPOT": 60, "OUA-TAN": 12, "OUA-GOU": 8},
    "VIS-6X40-BTE": {"DEPOT": 200, "OUA-TAN": 35, "OUA-GOU": 30},
    "TUB-PVC-110-4M": {"DEPOT": 90, "OUA-TAN": 18, "OUA-GOU": 10},
    "CAB-2X5-100M": {"DEPOT": 25, "OUA-TAN": 4, "OUA-GOU": 3},
    "MAR-1KG": {"DEPOT": 40, "OUA-TAN": 9, "OUA-GOU": 7},
}


def seed_catalog(branches_by_code: dict[str, Branch]) -> None:
    categories_by_name: dict[str, Category] = {}
    for name in CATEGORIES:
        category = Category.query.filter_by(name=name).first()
        if category is None:
            category = Category(name=name)
            db.session.add(category)
            db.session.flush()
        categories_by_name[name] = category

    brands_by_name: dict[str, Brand] = {}
    for name in BRANDS:
        brand = Brand.query.filter_by(name=name).first()
        if brand is None:
            brand = Brand(name=name)
            db.session.add(brand)
            db.session.flush()
        brands_by_name[name] = brand

    db.session.commit()

    for data in PRODUCTS:
        product = Product.query.filter_by(sku=data["sku"]).first()
        if product is None:
            product = Product(
                sku=data["sku"],
                name=data["name"],
                category_id=categories_by_name[data["category"]].id,
                brand_id=brands_by_name[data["brand"]].id,
                unit=data["unit"],
                purchase_price=data["purchase_price"],
                simple_price=data["simple_price"],
                technician_price=data["technician_price"],
                min_stock_threshold=data["min_stock_threshold"],
            )
            db.session.add(product)
            db.session.flush()

        for branch_code, quantity in INITIAL_STOCK.get(data["sku"], {}).items():
            branch = branches_by_code[branch_code]
            stock = Stock.query.filter_by(product_id=product.id, branch_id=branch.id).first()
            if stock is None:
                db.session.add(Stock(product_id=product.id, branch_id=branch.id, quantity=quantity))

    db.session.commit()


# ---------------------------------------------------------------------------
# Clients de démonstration
# ---------------------------------------------------------------------------

DEMO_CUSTOMERS: list[dict] = [
    {"full_name": "Client comptoir", "phone": None, "customer_type": "SIMPLE", "credit_limit": "0"},
    {
        "full_name": "Atelier Soudure Koudougou (Karim Traoré)",
        "phone": "+22670000001",
        "customer_type": "TECHNICIEN",
        "credit_limit": "500000",
    },
]


def seed_customers() -> None:
    for data in DEMO_CUSTOMERS:
        if data["phone"] and Customer.query.filter_by(phone=data["phone"]).first() is not None:
            continue
        if data["phone"] is None and Customer.query.filter_by(full_name=data["full_name"]).first() is not None:
            continue

        db.session.add(Customer(
            full_name=data["full_name"],
            phone=data["phone"],
            customer_type=data["customer_type"],
            credit_limit=data["credit_limit"],
        ))

    db.session.commit()


def run() -> None:
    roles = seed_permissions_and_roles()
    branches = seed_branches()
    seed_users(roles, branches)
    seed_default_company()
    seed_catalog(branches)
    seed_customers()
