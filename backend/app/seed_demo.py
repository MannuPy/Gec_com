"""Générateur de données commerciales de démonstration (jeu de test complet).

Cf. requête utilisateur : alimenter le système avec un historique réaliste
(6 à 12 mois) couvrant l'ensemble des fonctionnalités -> catalogue étendu,
clients, fournisseurs, ventes/POS, stock (réceptions, transferts,
inventaires), crédit client (RF-26) et anomalies volontaires (RF-28).

Usage :
    flask seed-demo --months 6 --seed 42

Prérequis : `flask seed` doit avoir été exécuté au préalable (RBAC, sites,
catalogue de base, utilisateurs, "Client comptoir").

⚠️ Non idempotent : ce script insère un historique daté (ventes, mouvements
de stock, etc.). Une seconde exécution dupliquerait les données. À lancer
UNE SEULE FOIS sur une base fraîchement amorcée (`flask db upgrade` +
`flask seed`). Pour repartir de zéro, recréer le schéma puis ré-exécuter
`flask seed` et `flask seed-demo`.

Après génération, exécuter :
    flask etl-daily --days <= months*30 (par défaut 180)
    flask ml-train-all --months <months>
pour alimenter le feature store et entraîner les modèles ML (RF-25 à RF-28).
"""
from __future__ import annotations

import os
import random
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.extensions import db
from app.models import (
    Branch,
    Brand,
    Category,
    Customer,
    CustomerPayment,
    CustomerPaymentStatus,
    CustomerType,
    PaymentType,
    Product,
    ReceptionStatus,
    Role,
    Sale,
    SaleChannel,
    SaleLine,
    SaleStatus,
    Stock,
    StockCount,
    StockCountLine,
    StockCountStatus,
    StockMovement,
    StockMovementType,
    Supplier,
    SupplierReception,
    SupplierReceptionLine,
    Transfer,
    TransferLine,
    TransferStatus,
    User,
)
from app.utils.tenant import register_user_index

ZERO = Decimal("0")
ONE = Decimal("1")


def _money(value) -> Decimal:
    """Arrondit un montant FCFA à l'unité (pas de centimes en pratique)."""
    return Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


# =============================================================================
# 1. Catalogue étendu (complète CATEGORIES/BRANDS/PRODUCTS de app/seed.py)
# =============================================================================

EXTRA_BRANDS: list[str] = ["Philips", "Sanifix"]

EXTRA_PRODUCTS: list[dict] = [
    {
        "sku": "PEI-SOBA-ROUGE-1L",
        "name": "Peinture SOBA rouge brillant 1L",
        "category": "Peinture",
        "brand": "SOBA",
        "unit": "BOITE",
        "purchase_price": "2200",
        "simple_price": "2800",
        "technician_price": "2600",
        "min_stock_threshold": 15,
    },
    {
        "sku": "VIS-4X30-BTE",
        "name": "Boîte de vis à bois 4x30mm (200 pcs)",
        "category": "Visserie",
        "brand": "Generic",
        "unit": "BOITE",
        "purchase_price": "1200",
        "simple_price": "1700",
        "technician_price": "1500",
        "min_stock_threshold": 25,
    },
    {
        "sku": "TUB-PVC-50-4M",
        "name": "Tube PVC évacuation Ø50mm (4m)",
        "category": "Plomberie",
        "brand": "Generic",
        "unit": "UNITE",
        "purchase_price": "2800",
        "simple_price": "3500",
        "technician_price": "3200",
        "min_stock_threshold": 20,
    },
    {
        "sku": "FER-T6-12M",
        "name": "Fer à béton torsadé Ø6 (barre 12m)",
        "category": "Matériaux de construction",
        "brand": "Generic",
        "unit": "UNITE",
        "purchase_price": "2000",
        "simple_price": "2400",
        "technician_price": "2200",
        "min_stock_threshold": 40,
    },
    {
        "sku": "CAB-2X25-100M",
        "name": "Câble électrique 2x2.5mm² (rouleau 100m)",
        "category": "Électricité",
        "brand": "CIMFASO",
        "unit": "UNITE",
        "purchase_price": "28000",
        "simple_price": "33000",
        "technician_price": "31000",
        "min_stock_threshold": 8,
    },
    {
        "sku": "AMP-LED-9W",
        "name": "Ampoule LED 9W culot E27",
        "category": "Électricité",
        "brand": "Philips",
        "unit": "UNITE",
        "purchase_price": "800",
        "simple_price": "1200",
        "technician_price": "1100",
        "min_stock_threshold": 50,
    },
    {
        "sku": "ROB-EVIER-STD",
        "name": "Robinet d'évier mitigeur standard",
        "category": "Plomberie",
        "brand": "Sanifix",
        "unit": "UNITE",
        "purchase_price": "8000",
        "simple_price": "11000",
        "technician_price": "10000",
        "min_stock_threshold": 6,
    },
    {
        "sku": "CAD-50MM",
        "name": "Cadenas à anse 50mm",
        "category": "Outillage",
        "brand": "Generic",
        "unit": "UNITE",
        "purchase_price": "1500",
        "simple_price": "2200",
        "technician_price": "2000",
        "min_stock_threshold": 15,
    },
    {
        "sku": "BROUETTE-STD",
        "name": "Brouette de chantier 80L",
        "category": "Outillage",
        "brand": "Generic",
        "unit": "UNITE",
        "purchase_price": "15000",
        "simple_price": "20000",
        "technician_price": "18500",
        "min_stock_threshold": 5,
    },
]

EXTRA_INITIAL_STOCK: dict[str, dict[str, int]] = {
    "PEI-SOBA-ROUGE-1L": {"DEPOT": 80, "OUA-TAN": 15, "OUA-GOU": 10},
    "VIS-4X30-BTE": {"DEPOT": 250, "OUA-TAN": 40, "OUA-GOU": 35},
    "TUB-PVC-50-4M": {"DEPOT": 100, "OUA-TAN": 20, "OUA-GOU": 15},
    "FER-T6-12M": {"DEPOT": 400, "OUA-TAN": 60, "OUA-GOU": 45},
    "CAB-2X25-100M": {"DEPOT": 30, "OUA-TAN": 5, "OUA-GOU": 4},
    "AMP-LED-9W": {"DEPOT": 600, "OUA-TAN": 100, "OUA-GOU": 80},
    "ROB-EVIER-STD": {"DEPOT": 25, "OUA-TAN": 4, "OUA-GOU": 3},
    "CAD-50MM": {"DEPOT": 120, "OUA-TAN": 20, "OUA-GOU": 15},
    "BROUETTE-STD": {"DEPOT": 20, "OUA-TAN": 3, "OUA-GOU": 2},
}

# Profils de demande par SKU (ABC : poids relatif de rotation : XYZ :
# saisonnalité). Couvre les 7 produits historiques + les 9 nouveaux (16 au
# total) afin de produire une distribution exploitable par RF-25/RF-27.
PRODUCT_PROFILES: dict[str, dict] = {
    "CIM-DAN-50": {"weight": 10.0, "qty_range": (1, 5), "season": "construction"},
    "FER-T8-12M": {"weight": 8.0, "qty_range": (1, 10), "season": "construction"},
    "FER-T6-12M": {"weight": 5.0, "qty_range": (2, 12), "season": "construction"},
    "PEI-SOBA-BLANC-20L": {"weight": 4.0, "qty_range": (1, 2), "season": "finition"},
    "PEI-SOBA-ROUGE-1L": {"weight": 5.0, "qty_range": (1, 3), "season": "finition"},
    "VIS-6X40-BTE": {"weight": 9.0, "qty_range": (1, 3), "season": None},
    "VIS-4X30-BTE": {"weight": 8.0, "qty_range": (1, 4), "season": None},
    "TUB-PVC-110-4M": {"weight": 4.0, "qty_range": (1, 4), "season": None},
    "TUB-PVC-50-4M": {"weight": 4.0, "qty_range": (1, 4), "season": None},
    "CAB-2X5-100M": {"weight": 3.0, "qty_range": (1, 2), "season": None},
    "CAB-2X25-100M": {"weight": 6.0, "qty_range": (1, 3), "season": None},
    "AMP-LED-9W": {"weight": 12.0, "qty_range": (1, 6), "season": None},
    "ROB-EVIER-STD": {"weight": 3.0, "qty_range": (1, 2), "season": None},
    "MAR-1KG": {"weight": 1.5, "qty_range": (1, 1), "season": None},
    "CAD-50MM": {"weight": 2.0, "qty_range": (1, 2), "season": None},
    "BROUETTE-STD": {"weight": 0.8, "qty_range": (1, 1), "season": None},
}

# Facteurs saisonniers mensuels (1 = neutre). "construction" = matériaux de
# gros œuvre, plus demandés en saison sèche (nov-mai) ; "finition" = peinture,
# pic après le gros œuvre (mars-juin).
SEASONAL_FACTORS: dict[str, dict[int, float]] = {
    "construction": {
        1: 1.3, 2: 1.3, 3: 1.3, 4: 1.25, 5: 1.15, 6: 0.75,
        7: 0.7, 8: 0.7, 9: 0.75, 10: 0.85, 11: 1.25, 12: 1.3,
    },
    "finition": {
        1: 0.9, 2: 1.0, 3: 1.2, 4: 1.3, 5: 1.3, 6: 1.2,
        7: 0.9, 8: 0.8, 9: 0.85, 10: 0.9, 11: 0.95, 12: 1.0,
    },
}


def _seasonal_factor(sku: str, month: int) -> float:
    season = PRODUCT_PROFILES.get(sku, {}).get("season")
    if not season:
        return 1.0
    return SEASONAL_FACTORS[season].get(month, 1.0)


def seed_extended_catalog(branches_by_code: dict[str, Branch]) -> dict[str, Product]:
    """Ajoute les marques/produits/stocks complémentaires et retourne
    {sku: Product} pour l'ENSEMBLE du catalogue (base + extension)."""
    categories_by_name = {c.name: c for c in Category.query.all()}
    brands_by_name = {b.name: b for b in Brand.query.all()}

    for name in EXTRA_BRANDS:
        if name not in brands_by_name:
            brand = Brand(name=name)
            db.session.add(brand)
            db.session.flush()
            brands_by_name[name] = brand
    db.session.commit()

    for data in EXTRA_PRODUCTS:
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

        for branch_code, quantity in EXTRA_INITIAL_STOCK.get(data["sku"], {}).items():
            branch = branches_by_code[branch_code]
            stock = Stock.query.filter_by(product_id=product.id, branch_id=branch.id).first()
            if stock is None:
                db.session.add(Stock(product_id=product.id, branch_id=branch.id, quantity=quantity))

    db.session.commit()
    return {p.sku: p for p in Product.query.all()}


# =============================================================================
# 2. Clients étendus (complète DEMO_CUSTOMERS de app/seed.py)
# =============================================================================

EXTRA_CUSTOMERS: list[dict] = [
    # ---- Particuliers (SIMPLE) : paiement comptant uniquement ----
    {"full_name": "Issouf Konaté", "phone": "+22670111001", "customer_type": "SIMPLE", "credit_limit": "0"},
    {"full_name": "Aminata Sawadogo", "phone": "+22670111002", "customer_type": "SIMPLE", "credit_limit": "0"},
    {"full_name": "Boukary Ouédraogo", "phone": "+22670111003", "customer_type": "SIMPLE", "credit_limit": "0"},
    {"full_name": "Fatimata Zongo", "phone": "+22670111004", "customer_type": "SIMPLE", "credit_limit": "0"},
    {"full_name": "Moussa Kaboré", "phone": "+22670111005", "customer_type": "SIMPLE", "credit_limit": "0"},
    {"full_name": "Awa Sankara", "phone": "+22670111006", "customer_type": "SIMPLE", "credit_limit": "0"},
    {"full_name": "Salif Compaoré", "phone": "+22670111007", "customer_type": "SIMPLE", "credit_limit": "0"},
    {"full_name": "Rasmata Nikiéma", "phone": "+22670111008", "customer_type": "SIMPLE", "credit_limit": "0"},
    {"full_name": "Drissa Traoré", "phone": "+22670111009", "customer_type": "SIMPLE", "credit_limit": "0"},
    {"full_name": "Mariam Bancé", "phone": "+22670111010", "customer_type": "SIMPLE", "credit_limit": "0"},
    # ---- Professionnels (TECHNICIEN) : vente à crédit possible (RG-26) ----
    {"full_name": "Faso Construction BTP (Yacouba Sanou)", "phone": "+22670222001", "customer_type": "TECHNICIEN", "credit_limit": "800000"},
    {"full_name": "Atelier Métallique Zongo & Fils", "phone": "+22670222002", "customer_type": "TECHNICIEN", "credit_limit": "400000"},
    {"full_name": "Plomberie Express Ouaga (Hamidou Diallo)", "phone": "+22670222003", "customer_type": "TECHNICIEN", "credit_limit": "300000"},
    {"full_name": "Électricité Générale Sahel (Lassané Ouattara)", "phone": "+22670222004", "customer_type": "TECHNICIEN", "credit_limit": "350000"},
    {"full_name": "Garage Moderne Gounghin (Issa Drabo)", "phone": "+22670222005", "customer_type": "TECHNICIEN", "credit_limit": "250000"},
    {"full_name": "Coopérative Habitat Tanghin", "phone": "+22670222006", "customer_type": "TECHNICIEN", "credit_limit": "600000"},
]


def seed_extended_customers() -> None:
    for data in EXTRA_CUSTOMERS:
        if Customer.query.filter_by(phone=data["phone"]).first() is not None:
            continue
        db.session.add(Customer(
            full_name=data["full_name"],
            phone=data["phone"],
            customer_type=data["customer_type"],
            credit_limit=data["credit_limit"],
        ))
    db.session.commit()


# =============================================================================
# 3. Fournisseurs (RF-11)
# =============================================================================

SUPPLIERS: list[dict] = [
    {
        "name": "Dangote Cement Burkina",
        "contact_name": "Service Commercial",
        "phone": "+22625001000",
        "email": "commercial@dangote-bf.com",
        "address": "Zone industrielle, Ouagadougou",
        "skus": ["CIM-DAN-50"],
    },
    {
        "name": "CIMFASO Matériaux",
        "contact_name": "Responsable Ventes",
        "phone": "+22625001100",
        "email": "ventes@cimfaso.bf",
        "address": "Route de Bobo, Ouagadougou",
        "skus": ["FER-T8-12M", "FER-T6-12M", "CAB-2X5-100M", "CAB-2X25-100M"],
    },
    {
        "name": "Quincaillerie Faso Import",
        "contact_name": "Mme Salimata Ouédraogo",
        "phone": "+22625001200",
        "email": "contact@fasoimport.bf",
        "address": "Marché central, Ouagadougou",
        "skus": [
            "VIS-6X40-BTE", "VIS-4X30-BTE", "MAR-1KG", "CAD-50MM", "BROUETTE-STD",
            "TUB-PVC-110-4M", "TUB-PVC-50-4M", "PEI-SOBA-BLANC-20L", "PEI-SOBA-ROUGE-1L",
        ],
    },
    {
        "name": "Électro Plus Distribution",
        "contact_name": "M. Paul Kientega",
        "phone": "+22625001300",
        "email": "commercial@electroplus.bf",
        "address": "Avenue Kwame Nkrumah, Ouagadougou",
        "skus": ["AMP-LED-9W", "ROB-EVIER-STD"],
    },
]


def seed_suppliers() -> dict[str, Supplier]:
    suppliers_by_name: dict[str, Supplier] = {}
    for data in SUPPLIERS:
        supplier = Supplier.query.filter_by(name=data["name"]).first()
        if supplier is None:
            supplier = Supplier(
                name=data["name"],
                contact_name=data["contact_name"],
                phone=data["phone"],
                email=data["email"],
                address=data["address"],
            )
            db.session.add(supplier)
            db.session.flush()
        suppliers_by_name[data["name"]] = supplier
    db.session.commit()
    return suppliers_by_name


# =============================================================================
# 4. Utilisateur supplémentaire (vendeur OUA-GOU, absent de app/seed.py)
# =============================================================================

EXTRA_USERS: list[dict] = [
    {
        "email": "vendeur2@gescom-bf.bf",
        "password": "Vendeur2#2026",
        "full_name": "Issa Drabo (Vendeur)",
        "role": "VENDEUR",
        "branch_code": "OUA-GOU",
    },
]


def seed_extra_users(roles_by_name: dict[str, Role], branches_by_code: dict[str, Branch]) -> dict[str, User]:
    users_by_email: dict[str, User] = {}
    for data in EXTRA_USERS:
        user = User.query.filter_by(email=data["email"]).first()
        if user is None:
            branch = branches_by_code[data["branch_code"]]
            user = User(
                email=data["email"],
                full_name=data["full_name"],
                role_id=roles_by_name[data["role"]].id,
                branch_id=branch.id,
                language="fr",
            )
            user.set_password(data["password"])
            db.session.add(user)
            db.session.flush()
        register_user_index(data["email"], "public")
        users_by_email[data["email"]] = user
    db.session.commit()
    return users_by_email


# =============================================================================
# 5. Génération de l'historique commercial
# =============================================================================

DISCOUNT_RATES = [0, 5, 10, 15, 20]
DISCOUNT_WEIGHTS = [70, 15, 7, 5, 3]
# Au-delà de ce seuil, une approbation est obligatoire (RG-23, cf.
# app.config.BaseConfig.DISCOUNT_APPROVAL_THRESHOLD).
DISCOUNT_APPROVAL_THRESHOLD = 10

HOUR_CHOICES = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
HOUR_WEIGHTS = [3, 5, 7, 7, 5, 3, 4, 5, 6, 6, 5, 2]

LINE_COUNT_CHOICES = [1, 2, 3, 4]
LINE_COUNT_WEIGHTS = [35, 40, 18, 7]

# Volume de ventes/jour par boutique (min, max) selon le jour de la semaine.
SALES_PER_DAY: dict[str, dict[str, tuple[int, int]]] = {
    "OUA-TAN": {"weekday": (5, 9), "sunday": (2, 4)},
    "OUA-GOU": {"weekday": (4, 7), "sunday": (1, 3)},
}

# Réapprovisionnement : multiplicateurs appliqués au seuil mini (RF-10).
TRANSFER_TARGET_MULTIPLIER = 3
DEPOT_BUFFER_MULTIPLIER = 1
RECEPTION_TARGET_MULTIPLIER = 6

# Inventaires : seuil d'écart nécessitant justification (RG-33, cf.
# app.config.BaseConfig.INVENTORY_VARIANCE_THRESHOLD_PCT = 5%).
VARIANCE_THRESHOLD_PCT = Decimal("0.05")
VARIANCE_REASONS = [
    "Casse non déclarée lors de la manipulation.",
    "Erreur de saisie sur une vente précédente - à corriger.",
    "Écart constaté - vol suspecté, à investiguer.",
    "Produit retrouvé mal rangé sur un autre site.",
    "Unités endommagées mises au rebut (non comptabilisées).",
]

# Anomalies volontaires (RF-28)
ANOMALY_COUNT = 18
ANOMALY_WINDOW_DAYS = 60


class GenerationContext:
    """État mutable partagé par les fonctions de génération."""

    def __init__(
        self,
        rng: random.Random,
        branches: dict[str, Branch],
        products: dict[str, Product],
        stock_by_key: dict[tuple[str, str], Stock],
        users: dict[str, User],
        comptoir: Customer,
        simple_customers: list[Customer],
        technicien_customers: list[Customer],
    ) -> None:
        self.rng = rng
        self.branches = branches
        self.products = products
        self.stock_by_key = stock_by_key
        self.users = users
        self.comptoir = comptoir
        self.simple_customers = simple_customers
        self.technicien_customers = technicien_customers

        self.sale_seq = 0
        self.transfer_seq = 0
        self.reception_seq = 0
        self.count_seq = 0
        self.running_credit_unpaid: dict[str, Decimal] = {}
        self.refund_candidates: list[tuple] = []
        self.today: date = date.today()

    def cashier_for_branch(self, branch_code: str) -> User:
        if branch_code == "OUA-TAN":
            return self.users["vendeur_tan"]
        if branch_code == "OUA-GOU":
            return self.users["vendeur_gou"]
        return self.users["magasinier"]


def _pick_customer(ctx: GenerationContext, branch: Branch) -> Customer:
    rng = ctx.rng
    if branch.code == "DEPOT":
        return rng.choice(ctx.technicien_customers)
    r = rng.random()
    if r < 0.55:
        return ctx.comptoir
    if r < 0.85:
        return rng.choice(ctx.simple_customers)
    return rng.choice(ctx.technicien_customers)


def _weighted_sample(rng: random.Random, items: list, weights: list[float], k: int) -> list:
    """Échantillonnage pondéré SANS remise (k éléments distincts)."""
    pool = list(zip(items, weights))
    chosen = []
    for _ in range(k):
        if not pool:
            break
        total = sum(w for _, w in pool)
        r = rng.uniform(0, total)
        upto = 0.0
        for i, (item, w) in enumerate(pool):
            upto += w
            if upto >= r:
                chosen.append(item)
                pool.pop(i)
                break
    return chosen


def _create_credit_payments(ctx: GenerationContext, sale: Sale, customer: Customer, total: Decimal, day: date) -> None:
    """Génère l'échéancier de remboursement (RF-26) pour une vente à crédit."""
    if total <= Decimal(200000):
        schedule = [(total, 30)]
    else:
        first = _money(total / 2)
        schedule = [(first, 30), (total - first, 60)]

    for amount, offset in schedule:
        due_date = day + timedelta(days=offset)
        paid_date = None
        note = None

        if due_date > ctx.today:
            status = CustomerPaymentStatus.PENDING.value
        else:
            roll = ctx.rng.random()
            if roll < 0.62:
                status = CustomerPaymentStatus.PAID.value
                if ctx.rng.random() < 0.7:
                    paid_date = due_date - timedelta(days=ctx.rng.randint(0, 5))
                    if paid_date < day:
                        paid_date = day
                else:
                    paid_date = due_date + timedelta(days=ctx.rng.randint(1, 20))
                    if paid_date > ctx.today:
                        paid_date = ctx.today
            elif roll < 0.92:
                status = CustomerPaymentStatus.LATE.value
                note = "Échéance en retard - relance à effectuer"
            else:
                status = CustomerPaymentStatus.CANCELLED.value
                note = "Échéance annulée (accord commercial)"

        recorded_by_id = (
            ctx.users["admin"].id
            if status in (CustomerPaymentStatus.PAID.value, CustomerPaymentStatus.CANCELLED.value)
            else None
        )

        record_dt = datetime.combine(day, time(9, 0))
        db.session.add(CustomerPayment(
            customer_id=customer.id,
            sale_id=sale.id,
            amount=amount,
            due_date=due_date,
            paid_date=paid_date,
            status=status,
            recorded_by_id=recorded_by_id,
            note=note,
            created_at=record_dt,
            updated_at=record_dt,
        ))

        if status in (CustomerPaymentStatus.PENDING.value, CustomerPaymentStatus.LATE.value):
            ctx.running_credit_unpaid[customer.id] = ctx.running_credit_unpaid.get(customer.id, ZERO) + amount


def _generate_one_sale(ctx: GenerationContext, branch: Branch, day: date, customer: Customer | None = None, anomaly: bool = False) -> Sale | None:
    rng = ctx.rng

    candidates = [
        p for p in ctx.products.values()
        if (s := ctx.stock_by_key.get((p.id, branch.id))) and s.quantity > 0
    ]
    if not candidates:
        return None

    if anomaly:
        # Produits a faible rotation -> ecart marque vs moyenne produit (RF-28)
        candidates = sorted(candidates, key=lambda p: PRODUCT_PROFILES.get(p.sku, {}).get("weight", 1.0))
        chosen_products = candidates[: min(2, len(candidates))]
    else:
        weights = [
            PRODUCT_PROFILES.get(p.sku, {}).get("weight", 1.0) * _seasonal_factor(p.sku, day.month)
            for p in candidates
        ]
        n_lines = rng.choices(LINE_COUNT_CHOICES, weights=LINE_COUNT_WEIGHTS, k=1)[0]
        chosen_products = _weighted_sample(rng, candidates, weights, min(n_lines, len(candidates)))

    if customer is None:
        customer = _pick_customer(ctx, branch)

    price_type = customer.customer_type

    lines_data = []
    for product in chosen_products:
        stock = ctx.stock_by_key[(product.id, branch.id)]
        profile = PRODUCT_PROFILES.get(product.sku, {"qty_range": (1, 2)})
        if anomaly:
            # Quantite anormalement elevee, sans plafonnement sur le stock
            # disponible (le stock peut devenir negatif - RG-30).
            qty = rng.randint(15, 40)
        else:
            qty = rng.randint(*profile["qty_range"])
            qty = max(1, min(qty, stock.quantity))
        unit_price = product.price_for(price_type)
        line_total = _money(unit_price * qty)
        lines_data.append({"product": product, "quantity": qty, "unit_price": unit_price, "line_total": line_total})

    subtotal = sum((l["line_total"] for l in lines_data), ZERO)

    if anomaly:
        discount_rate = 20
    else:
        discount_rate = rng.choices(DISCOUNT_RATES, weights=DISCOUNT_WEIGHTS, k=1)[0]
    discount_amount = _money(subtotal * Decimal(discount_rate) / Decimal(100))
    total = subtotal - discount_amount

    approved_by_id = ctx.users["admin"].id if discount_rate >= DISCOUNT_APPROVAL_THRESHOLD else None

    # ---- statut ----
    if anomaly:
        status = SaleStatus.VALIDEE.value
    elif rng.random() < 0.015:
        status = SaleStatus.ANNULEE.value
    else:
        status = SaleStatus.VALIDEE.value

    # ---- moyen de paiement (RG-26 : credit reserve aux clients TECHNICIEN) ----
    payment_type = PaymentType.CASH.value
    if (
        not anomaly
        and status == SaleStatus.VALIDEE.value
        and customer.customer_type == CustomerType.TECHNICIEN.value
        and customer.credit_limit
        and customer.credit_limit > 0
        and rng.random() < 0.35
    ):
        projected = ctx.running_credit_unpaid.get(customer.id, ZERO) + total
        if projected <= customer.credit_limit:
            payment_type = PaymentType.CREDIT.value

    # ---- canal et horodatage ----
    if anomaly:
        channel = SaleChannel.OFFLINE.value
        offline_uuid = None
        hour = rng.choice([1, 2, 3, 4, 5])
    else:
        channel = SaleChannel.ONLINE.value if rng.random() < 0.06 else SaleChannel.OFFLINE.value
        offline_uuid = (
            str(uuid.uuid4())
            if channel == SaleChannel.OFFLINE.value and rng.random() < 0.25
            else None
        )
        hour = rng.choices(HOUR_CHOICES, weights=HOUR_WEIGHTS, k=1)[0]

    created_at = datetime.combine(day, time(hour, rng.randint(0, 59)))

    ctx.sale_seq += 1
    reference = f"VTE-{day:%Y%m%d}-{ctx.sale_seq:05d}"
    cashier = ctx.cashier_for_branch(branch.code)

    sale = Sale(
        reference=reference,
        branch_id=branch.id,
        cashier_id=cashier.id,
        customer_id=customer.id,
        subtotal=subtotal,
        discount_rate=discount_rate,
        discount_amount=discount_amount,
        total=total,
        payment_type=payment_type,
        status=status,
        approved_by_id=approved_by_id,
        offline_uuid=offline_uuid,
        channel=channel,
        created_at=created_at,
        updated_at=created_at,
    )
    db.session.add(sale)
    db.session.flush()

    for line in lines_data:
        db.session.add(SaleLine(
            sale_id=sale.id,
            product_id=line["product"].id,
            quantity=line["quantity"],
            unit_price_applied=line["unit_price"],
            price_type=price_type,
            line_total=line["line_total"],
        ))

    # ---- impact stock + mouvements (uniquement pour une vente validee) ----
    if status == SaleStatus.VALIDEE.value:
        for line in lines_data:
            stock = ctx.stock_by_key[(line["product"].id, branch.id)]
            stock.quantity -= line["quantity"]
            db.session.add(StockMovement(
                product_id=line["product"].id,
                branch_id=branch.id,
                movement_type=StockMovementType.SORTIE_VENTE.value,
                quantity=line["quantity"],
                reference_type="sale",
                reference_id=sale.id,
                created_by_id=cashier.id,
                created_at=created_at,
            ))

        if payment_type == PaymentType.CREDIT.value:
            _create_credit_payments(ctx, sale, customer, total, day)

        if not anomaly and total < Decimal(100000) and day <= ctx.today - timedelta(days=14):
            ctx.refund_candidates.append((sale, branch, lines_data, customer, created_at))

    return sale


def generate_daily_sales(ctx: GenerationContext, day: date) -> None:
    weekday = day.weekday()  # 0=lundi .. 6=dimanche
    for branch_code, config in SALES_PER_DAY.items():
        branch = ctx.branches[branch_code]
        lo, hi = config["sunday"] if weekday == 6 else config["weekday"]
        n_sales = ctx.rng.randint(lo, hi)
        for _ in range(n_sales):
            _generate_one_sale(ctx, branch, day)

    # Ventes B2B occasionnelles au depot central (clients techniciens)
    if ctx.rng.random() < 0.30:
        _generate_one_sale(ctx, ctx.branches["DEPOT"], day)


def generate_weekly_transfers(ctx: GenerationContext, day: date) -> None:
    """Transferts hebdomadaires DEPOT -> boutiques pour reapprovisionnement (RG-17/18)."""
    depot = ctx.branches["DEPOT"]
    for branch_code in ("OUA-TAN", "OUA-GOU"):
        branch = ctx.branches[branch_code]
        lines: list[tuple[Product, int]] = []
        for product in ctx.products.values():
            depot_stock = ctx.stock_by_key.get((product.id, depot.id))
            dest_stock = ctx.stock_by_key.get((product.id, branch.id))
            if depot_stock is None or dest_stock is None:
                continue
            threshold = max(product.min_stock_threshold, 1)
            target = threshold * TRANSFER_TARGET_MULTIPLIER
            needed = target - dest_stock.quantity
            if needed <= 0:
                continue
            available = depot_stock.quantity - threshold * DEPOT_BUFFER_MULTIPLIER
            if available <= 0:
                continue
            qty = min(needed, available)
            if qty <= 0:
                continue
            lines.append((product, int(qty)))

        if not lines:
            continue

        lines = lines[:6]
        ctx.transfer_seq += 1
        reference = f"TRF-{day:%Y%m%d}-{ctx.transfer_seq:03d}"
        sent_at = datetime.combine(day, time(8, 0))
        received_at = datetime.combine(day + timedelta(days=1), time(9, 0))
        receiver = ctx.cashier_for_branch(branch_code)

        transfer = Transfer(
            reference=reference,
            source_branch_id=depot.id,
            destination_branch_id=branch.id,
            status=TransferStatus.RECU.value,
            created_by_id=ctx.users["magasinier"].id,
            sent_at=sent_at,
            received_by_id=receiver.id,
            received_at=received_at,
            created_at=sent_at,
            updated_at=received_at,
        )
        db.session.add(transfer)
        db.session.flush()

        for product, qty in lines:
            db.session.add(TransferLine(
                transfer_id=transfer.id,
                product_id=product.id,
                quantity_sent=qty,
                quantity_received=qty,
            ))
            depot_stock = ctx.stock_by_key[(product.id, depot.id)]
            dest_stock = ctx.stock_by_key[(product.id, branch.id)]
            depot_stock.quantity -= qty
            dest_stock.quantity += qty

            db.session.add(StockMovement(
                product_id=product.id, branch_id=depot.id,
                movement_type=StockMovementType.SORTIE_TRANSFERT.value,
                quantity=qty, reference_type="transfer", reference_id=transfer.id,
                created_by_id=ctx.users["magasinier"].id, created_at=sent_at,
            ))
            db.session.add(StockMovement(
                product_id=product.id, branch_id=branch.id,
                movement_type=StockMovementType.ENTREE_TRANSFERT.value,
                quantity=qty, reference_type="transfer", reference_id=transfer.id,
                created_by_id=receiver.id, created_at=received_at,
            ))


def generate_supplier_reception(ctx: GenerationContext, day: date, suppliers_by_name: dict[str, Supplier]) -> None:
    """Réceptions fournisseurs bimensuelles au dépôt central (RF-11)."""
    depot = ctx.branches["DEPOT"]
    supplier_name = ctx.rng.choice(list(suppliers_by_name.keys()))
    supplier = suppliers_by_name[supplier_name]
    skus = next(s["skus"] for s in SUPPLIERS if s["name"] == supplier_name)

    lines: list[tuple[Product, int]] = []
    for sku in skus:
        product = ctx.products.get(sku)
        if product is None:
            continue
        depot_stock = ctx.stock_by_key.get((product.id, depot.id))
        if depot_stock is None:
            continue
        threshold = max(product.min_stock_threshold, 1)
        target = threshold * RECEPTION_TARGET_MULTIPLIER
        needed = target - depot_stock.quantity
        if needed <= 0:
            needed = max(threshold, 5)  # reappro minimal meme si stock suffisant
        lines.append((product, int(needed)))

    if not lines:
        return

    ctx.reception_seq += 1
    reference = f"REC-{day:%Y%m%d}-{ctx.reception_seq:03d}"
    received_at = datetime.combine(day, time(10, 0))

    reception = SupplierReception(
        reference=reference,
        supplier_id=supplier.id,
        branch_id=depot.id,
        status=ReceptionStatus.VALIDEE.value,
        received_at=received_at,
        created_by_id=ctx.users["magasinier"].id,
        created_at=received_at,
        updated_at=received_at,
    )
    db.session.add(reception)
    db.session.flush()

    for product, qty in lines:
        qty = max(1, qty)
        variation = Decimal(str(round(ctx.rng.uniform(-0.03, 0.05), 3)))
        unit_price = _money(product.purchase_price * (ONE + variation))
        db.session.add(SupplierReceptionLine(
            reception_id=reception.id,
            product_id=product.id,
            quantity=qty,
            unit_purchase_price=unit_price,
        ))
        stock = ctx.stock_by_key[(product.id, depot.id)]
        stock.quantity += qty
        db.session.add(StockMovement(
            product_id=product.id, branch_id=depot.id,
            movement_type=StockMovementType.ENTREE_RECEPTION.value,
            quantity=qty, reference_type="reception", reference_id=reception.id,
            created_by_id=ctx.users["magasinier"].id, created_at=received_at,
        ))


def generate_stock_count(ctx: GenerationContext, branch_code: str, day: date) -> None:
    """Session d'inventaire VALIDE avec écarts (RG-33) -> AJUSTEMENT_INVENTAIRE."""
    branch = ctx.branches[branch_code]
    ctx.count_seq += 1
    reference = f"INV-{branch_code}-{day:%Y%m%d}"
    created_dt = datetime.combine(day, time(8, 0))
    validated_dt = datetime.combine(day, time(17, 0))
    creator = ctx.users["magasinier"] if branch_code == "DEPOT" else ctx.cashier_for_branch(branch_code)

    stock_count = StockCount(
        reference=reference,
        branch_id=branch.id,
        status=StockCountStatus.VALIDE.value,
        created_by_id=creator.id,
        validated_by_id=ctx.users["admin"].id,
        validated_at=validated_dt,
        created_at=created_dt,
        updated_at=validated_dt,
    )
    db.session.add(stock_count)
    db.session.flush()

    for product in ctx.products.values():
        stock = ctx.stock_by_key.get((product.id, branch.id))
        if stock is None:
            continue
        theoretical = stock.quantity
        roll = ctx.rng.random()
        if roll < 0.12 and theoretical > 0:
            pct = ctx.rng.choice([Decimal("0.06"), Decimal("-0.07"), Decimal("0.09"), Decimal("-0.10"), Decimal("0.12"), Decimal("-0.15")])
        elif roll < 0.45:
            pct = Decimal(ctx.rng.choice([-2, -1, 0, 1, 2])) / Decimal(100)
        else:
            pct = Decimal("0")

        variance = int((Decimal(theoretical) * pct).to_integral_value(rounding=ROUND_HALF_UP))
        counted = max(0, theoretical + variance)
        variance = counted - theoretical

        comment = None
        if theoretical > 0 and variance != 0 and abs(Decimal(variance)) / Decimal(theoretical) >= VARIANCE_THRESHOLD_PCT:
            comment = ctx.rng.choice(VARIANCE_REASONS)
        elif variance != 0:
            comment = "Écart mineur constaté lors du comptage (à surveiller)."

        db.session.add(StockCountLine(
            stock_count_id=stock_count.id,
            product_id=product.id,
            theoretical_quantity=theoretical,
            counted_quantity=counted,
            variance=variance,
            comment=comment,
        ))

        if variance != 0:
            stock.quantity = counted
            db.session.add(StockMovement(
                product_id=product.id, branch_id=branch.id,
                movement_type=StockMovementType.AJUSTEMENT_INVENTAIRE.value,
                quantity=variance, reference_type="stock_count", reference_id=stock_count.id,
                created_by_id=ctx.users["admin"].id, created_at=validated_dt,
                comment=comment,
            ))


def generate_refund_and_status_samples(ctx: GenerationContext) -> None:
    """Quelques avoirs (AVOIR_EMIS) et ventes EN_ATTENTE_APPROBATION pour
    couvrir les statuts non générés naturellement par la boucle quotidienne."""
    rng = ctx.rng

    # ---- Avoirs sur des ventes anciennes (RG-27 : correction par avoir) ----
    candidates = ctx.refund_candidates
    n_refunds = min(8, len(candidates))
    chosen = rng.sample(candidates, n_refunds) if candidates else []

    for sale, branch, lines_data, customer, original_created_at in chosen:
        refund_created_at = original_created_at + timedelta(days=rng.randint(2, 10))
        if refund_created_at.date() > ctx.today:
            continue

        ctx.sale_seq += 1
        reference = f"AVO-{refund_created_at:%Y%m%d}-{ctx.sale_seq:05d}"
        cashier = ctx.cashier_for_branch(branch.code)

        refund = Sale(
            reference=reference,
            branch_id=branch.id,
            cashier_id=cashier.id,
            customer_id=customer.id,
            subtotal=sale.subtotal,
            discount_rate=sale.discount_rate,
            discount_amount=sale.discount_amount,
            total=sale.total,
            payment_type=sale.payment_type,
            status=SaleStatus.AVOIR_EMIS.value,
            approved_by_id=sale.approved_by_id,
            channel=sale.channel,
            refund_of_sale_id=sale.id,
            created_at=refund_created_at,
            updated_at=refund_created_at,
        )
        db.session.add(refund)
        db.session.flush()

        for line in lines_data:
            db.session.add(SaleLine(
                sale_id=refund.id,
                product_id=line["product"].id,
                quantity=line["quantity"],
                unit_price_applied=line["unit_price"],
                price_type=customer.customer_type,
                line_total=line["line_total"],
            ))
            stock = ctx.stock_by_key.get((line["product"].id, branch.id))
            if stock is not None:
                stock.quantity += line["quantity"]
            db.session.add(StockMovement(
                product_id=line["product"].id, branch_id=branch.id,
                movement_type=StockMovementType.ENTREE_RETOUR_VENTE.value,
                quantity=line["quantity"], reference_type="sale", reference_id=refund.id,
                created_by_id=cashier.id, created_at=refund_created_at,
                comment="Retour client - avoir émis",
            ))

    # ---- Ventes EN_ATTENTE_APPROBATION (remise 15%, approbation non encore donnee) ----
    for branch_code in ("OUA-TAN", "OUA-GOU"):
        branch = ctx.branches[branch_code]
        eligible = [
            p for p in ctx.products.values()
            if (s := ctx.stock_by_key.get((p.id, branch.id))) and s.quantity > 1
        ]
        if not eligible:
            continue
        product = rng.choice(eligible)
        stock = ctx.stock_by_key[(product.id, branch.id)]
        profile = PRODUCT_PROFILES.get(product.sku, {"qty_range": (1, 2)})
        qty = max(1, min(rng.randint(*profile["qty_range"]), stock.quantity))
        customer = ctx.comptoir
        unit_price = product.price_for(customer.customer_type)
        line_total = _money(unit_price * qty)
        subtotal = line_total
        discount_rate = 15
        discount_amount = _money(subtotal * Decimal(discount_rate) / Decimal(100))
        total = subtotal - discount_amount

        ctx.sale_seq += 1
        created_at = datetime.combine(ctx.today, time(rng.choice(HOUR_CHOICES), rng.randint(0, 59)))
        reference = f"VTE-{ctx.today:%Y%m%d}-{ctx.sale_seq:05d}"

        pending_sale = Sale(
            reference=reference,
            branch_id=branch.id,
            cashier_id=ctx.cashier_for_branch(branch_code).id,
            customer_id=customer.id,
            subtotal=subtotal,
            discount_rate=discount_rate,
            discount_amount=discount_amount,
            total=total,
            payment_type=PaymentType.CASH.value,
            status=SaleStatus.EN_ATTENTE_APPROBATION.value,
            approved_by_id=None,
            channel=SaleChannel.OFFLINE.value,
            created_at=created_at,
            updated_at=created_at,
        )
        db.session.add(pending_sale)
        db.session.flush()
        db.session.add(SaleLine(
            sale_id=pending_sale.id,
            product_id=product.id,
            quantity=qty,
            unit_price_applied=unit_price,
            price_type=customer.customer_type,
            line_total=line_total,
        ))
        # Pas de mouvement de stock : vente non validee (remise en attente d'approbation, RG-23)


def inject_anomalies(ctx: GenerationContext) -> None:
    """Injecte ~ANOMALY_COUNT ventes anormales sur les ANOMALY_WINDOW_DAYS
    derniers jours, pour exercer la detection d'anomalies (RF-28) :
    quantite tres superieure a la normale, heure inhabituelle, remise max."""
    rng = ctx.rng
    branch_codes = ["OUA-TAN", "OUA-GOU"]
    for _ in range(ANOMALY_COUNT):
        day_offset = rng.randint(1, ANOMALY_WINDOW_DAYS)
        day = ctx.today - timedelta(days=day_offset)
        branch = ctx.branches[rng.choice(branch_codes)]
        _generate_one_sale(ctx, branch, day, customer=ctx.comptoir, anomaly=True)


# =============================================================================
# 6. Orchestration
# =============================================================================

# Inventaires periodiques par site : premier comptage decale (jours depuis le
# debut de la periode), puis tous les STOCK_COUNT_INTERVAL_DAYS jours.
STOCK_COUNT_INTERVAL_DAYS = 70
STOCK_COUNT_FIRST_OFFSETS: dict[str, int] = {"DEPOT": 25, "OUA-TAN": 35, "OUA-GOU": 45}


def run(months: int = 6, seed: int = 42) -> None:
    rng = random.Random(seed)

    roles_by_name = {r.name: r for r in Role.query.all()}
    branches_by_code = {b.code: b for b in Branch.query.all()}

    admin_email = os.environ.get("SEED_ADMIN_EMAIL", "admin@gescom-bf.bf").lower()
    admin = User.query.filter_by(email=admin_email).first()
    magasinier = User.query.filter_by(email="magasinier@gescom-bf.bf").first()
    vendeur_tan = User.query.filter_by(email="vendeur@gescom-bf.bf").first()

    if admin is None or magasinier is None or vendeur_tan is None or not branches_by_code or not roles_by_name:
        raise RuntimeError(
            "Donnees de base manquantes : executez 'flask seed' avant 'flask seed-demo'."
        )

    extra_users = seed_extra_users(roles_by_name, branches_by_code)
    vendeur_gou = extra_users["vendeur2@gescom-bf.bf"]

    products_by_sku = seed_extended_catalog(branches_by_code)
    seed_extended_customers()
    suppliers_by_name = seed_suppliers()

    customers = Customer.query.all()
    comptoir = next(c for c in customers if c.full_name == "Client comptoir")
    simple_customers = [c for c in customers if c.customer_type == CustomerType.SIMPLE.value and c.id != comptoir.id]
    technicien_customers = [c for c in customers if c.customer_type == CustomerType.TECHNICIEN.value]

    stock_by_key = {(s.product_id, s.branch_id): s for s in Stock.query.all()}

    ctx = GenerationContext(
        rng=rng,
        branches=branches_by_code,
        products=products_by_sku,
        stock_by_key=stock_by_key,
        users={
            "admin": admin,
            "magasinier": magasinier,
            "vendeur_tan": vendeur_tan,
            "vendeur_gou": vendeur_gou,
        },
        comptoir=comptoir,
        simple_customers=simple_customers,
        technicien_customers=technicien_customers,
    )

    today = date.today()
    ctx.today = today
    start_date = today - timedelta(days=months * 30)
    total_days = (today - start_date).days

    # Planification des sessions d'inventaire (RF-21)
    stock_count_days: dict[date, list[str]] = {}
    for branch_code, first_offset in STOCK_COUNT_FIRST_OFFSETS.items():
        offset = first_offset
        while offset <= total_days - 5:
            count_day = start_date + timedelta(days=offset)
            stock_count_days.setdefault(count_day, []).append(branch_code)
            offset += STOCK_COUNT_INTERVAL_DAYS

    day = start_date
    week_index = 0
    while day <= today:
        if day.weekday() == 0:
            week_index += 1
            generate_weekly_transfers(ctx, day)
            if week_index % 2 == 0:
                generate_supplier_reception(ctx, day, suppliers_by_name)

        generate_daily_sales(ctx, day)

        for branch_code in stock_count_days.get(day, []):
            generate_stock_count(ctx, branch_code, day)

        db.session.commit()
        day += timedelta(days=1)

    generate_refund_and_status_samples(ctx)
    inject_anomalies(ctx)

    for customer in customers:
        customer.credit_balance = ctx.running_credit_unpaid.get(customer.id, ZERO)

    db.session.commit()

    print(
        f"Donnees de demonstration generees : {ctx.sale_seq} ventes "
        f"({start_date.isoformat()} -> {today.isoformat()}), "
        f"{ctx.transfer_seq} transferts, {ctx.reception_seq} receptions, "
        f"{ctx.count_seq} inventaires."
    )


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        run()
