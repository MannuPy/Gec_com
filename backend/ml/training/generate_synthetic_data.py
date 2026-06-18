"""
Génération de données historiques synthétiques pour l'entraînement des
modèles de Machine Learning (cf. docs/20-MACHINE-LEARNING.md §20.6).

Le jeu de données décrit dans la documentation (5 boutiques + 1 dépôt,
200 produits / 8 catégories, 500 clients) est un jeu *de référence* destiné
à produire les métriques cibles présentées dans le document. Ce script
applique la **même méthodologie** (saisonnalités, bruit, ruptures injectées,
profils clients à crédit) mais à l'échelle réelle du catalogue initialisé
par `app/seed.py` (1 dépôt + boutiques actives, catalogue de démonstration),
afin de fournir un historique exploitable directement par les tâches
Celery d'entraînement (cf. 21-PIPELINE-ETL.md).

Hypothèses et limites assumées (cf. §20.6.2) :
- Les ventes générées sont historiques et servent uniquement à
  l'entraînement / l'évaluation des modèles : ce script **ne modifie pas**
  les niveaux de stock courants (`stock`) ni ne crée de `stock_movements`,
  afin de ne pas désynchroniser l'état opérationnel de la démo.
- Le calendrier des fêtes mobiles (Tabaski) est approximé par des dates
  fixes par année simulée.
- Le schéma V1 ne comporte pas de table de suivi des remboursements à
  crédit ; le `taux_retard` utilisé pour le scoring de solvabilité
  (cf. app/ml/credit_scoring.py) est dérivé de manière déterministe à
  partir de l'identifiant client (distribution Beta), pas d'un historique
  de remboursement réel.
- Idempotent : chaque vente synthétique porte un `offline_uuid` déterministe
  (préfixe `SYNTH-`) ; une ré-exécution ne duplique pas les données.

Usage :
    python -m ml.training.generate_synthetic_data [--months 24] [--extra-customers 40] [--seed 42]
"""
import argparse
import sys
from datetime import datetime, timedelta
from decimal import Decimal

import numpy as np

sys.path.insert(0, ".")

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import (  # noqa: E402
    Branch,
    Customer,
    CustomerType,
    PaymentType,
    Product,
    Sale,
    SaleLine,
    SaleStatus,
    User,
)
from app.models.base import generate_uuid  # noqa: E402

# ---------------------------------------------------------------------------
# Référentiel calendaire simplifié (BF) — cf. §20.2.2 / §20.6.1
# ---------------------------------------------------------------------------

# Saison des pluies : juin à octobre -> +40% pour les "Matériaux de construction"
RAINY_SEASON_MONTHS = {6, 7, 8, 9, 10}

# Approximation de dates fixes pour Tabaski / fêtes de fin d'année par année
# (à remplacer par un calendrier lunaire réel en production, cf. §20.6.2)
TABASKI_APPROX = {
    2024: (6, 17),
    2025: (6, 7),
    2026: (5, 27),
    2027: (5, 17),
}


def is_holiday_period(d: datetime.date) -> bool:
    """Tabaski (+/- 3 jours) ou période Noël/Nouvel An (20 déc -> 2 jan)."""
    if (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 2):
        return True
    tabaski = TABASKI_APPROX.get(d.year)
    if tabaski:
        from datetime import date as _date

        tdate = _date(d.year, *tabaski)
        if abs((d - tdate).days) <= 3:
            return True
    return False


def base_daily_demand(purchase_price: Decimal, rng: np.random.Generator) -> float:
    """Heuristique : un produit moins cher se vend en plus grande quantité."""
    price = float(purchase_price) if purchase_price else 1000.0
    scale = max(0.3, min(8.0, 15000.0 / max(price, 500.0)))
    return float(rng.uniform(scale * 0.5, scale * 1.5))


def daily_quantity(
    base: float,
    d: datetime.date,
    category_name: str | None,
    stockout: bool,
    rng: np.random.Generator,
) -> int:
    if stockout:
        return 0

    factor = 1.0
    # Saisonnalité hebdomadaire : +30% le week-end (samedi/dimanche)
    if d.weekday() in (5, 6):
        factor *= 1.30
    # Saisonnalité annuelle : +50% Tabaski / Noël-Nouvel An
    if is_holiday_period(d):
        factor *= 1.50
    # Saisonnalité "matériaux" pendant la saison des pluies
    if category_name == "Matériaux de construction" and d.month in RAINY_SEASON_MONTHS:
        factor *= 1.40

    noise = max(0.0, rng.normal(1.0, 0.15))
    quantity = round(base * factor * noise)
    return max(0, int(quantity))


def pick_cashier(branch: Branch, fallback_admin: User) -> User:
    user = User.query.filter_by(branch_id=branch.id, is_active=True).first()
    return user or fallback_admin


def build_stockout_windows(
    branches: list[Branch], products: list[Product], months: int, rng: np.random.Generator
) -> set[tuple[str, str, int]]:
    """Retourne l'ensemble des (branch_id, product_id, jour_offset) en rupture.

    ~5% des couples (produit, boutique) subissent une fenêtre de rupture de
    2 à 4 semaines tirée aléatoirement sur la période (cf. §20.6.1).
    """
    stockout_days: set[tuple[str, str, int]] = set()
    total_days = months * 30
    pairs = [(b, p) for b in branches for p in products]
    n_stockout_pairs = max(1, round(len(pairs) * 0.05))
    chosen = rng.choice(len(pairs), size=n_stockout_pairs, replace=False)
    for idx in chosen:
        branch, product = pairs[int(idx)]
        window_len = int(rng.integers(14, 29))
        start = int(rng.integers(0, max(1, total_days - window_len)))
        for offset in range(start, start + window_len):
            stockout_days.add((branch.id, product.id, offset))
    return stockout_days


def generate_sales_history(
    app, months: int, rng: np.random.Generator, batch_size: int = 1000
) -> int:
    branches = Branch.query.filter_by(is_depot=False, is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    if not branches or not products:
        print("Aucune boutique/produit actif : exécutez d'abord `python -m app.seed`.")
        return 0

    admin = User.query.join(User.role).filter_by(name="ADMIN").first()
    cashier_by_branch = {b.id: pick_cashier(b, admin) for b in branches}

    existing = {
        row[0]
        for row in db.session.query(Sale.offline_uuid)
        .filter(Sale.offline_uuid.like("SYNTH-%"))
        .all()
    }

    end_date = datetime.utcnow().date() - timedelta(days=1)
    start_date = end_date - timedelta(days=months * 30)

    stockout_days = build_stockout_windows(branches, products, months, rng)

    sale_rows: list[dict] = []
    line_rows: list[dict] = []
    created = 0

    total_days = (end_date - start_date).days
    for offset in range(total_days):
        d = start_date + timedelta(days=offset)
        for branch in branches:
            cashier = cashier_by_branch[branch.id]
            for product in products:
                category_name = product.category.name if product.category else None
                base = base_daily_demand(product.purchase_price, rng)
                is_stockout = (branch.id, product.id, offset) in stockout_days
                qty = daily_quantity(base, d, category_name, is_stockout, rng)
                if qty <= 0:
                    continue

                offline_uuid = f"SYNTH-{branch.code}-{product.sku}-{d.isoformat()}"
                if offline_uuid in existing:
                    continue

                unit_price = product.simple_price
                line_total = Decimal(unit_price) * qty
                sale_id = generate_uuid()
                created_at = datetime.combine(d, datetime.min.time()) + timedelta(hours=10)

                sale_rows.append(
                    {
                        "id": sale_id,
                        "reference": f"VTE-SYNTH-{d:%Y%m%d}-{generate_uuid()[:6].upper()}",
                        "branch_id": branch.id,
                        "cashier_id": cashier.id,
                        "customer_id": None,
                        "subtotal": line_total,
                        "discount_rate": 0,
                        "discount_amount": Decimal("0"),
                        "total": line_total,
                        "payment_type": PaymentType.CASH.value,
                        "status": SaleStatus.VALIDEE.value,
                        "approved_by_id": None,
                        "offline_uuid": offline_uuid,
                        "refund_of_sale_id": None,
                        "created_at": created_at,
                    }
                )
                line_rows.append(
                    {
                        "id": generate_uuid(),
                        "sale_id": sale_id,
                        "product_id": product.id,
                        "quantity": qty,
                        "unit_price_applied": unit_price,
                        "price_type": CustomerType.SIMPLE.value,
                        "line_total": line_total,
                    }
                )
                created += 1

                if len(sale_rows) >= batch_size:
                    db.session.bulk_insert_mappings(Sale, sale_rows)
                    db.session.bulk_insert_mappings(SaleLine, line_rows)
                    db.session.commit()
                    sale_rows.clear()
                    line_rows.clear()

    if sale_rows:
        db.session.bulk_insert_mappings(Sale, sale_rows)
        db.session.bulk_insert_mappings(SaleLine, line_rows)
        db.session.commit()

    return created


def generate_credit_customers(
    app, months: int, extra_customers: int, rng: np.random.Generator
) -> int:
    """Crée des clients TECHNICIEN avec un historique d'achats à crédit.

    Sert au scoring de solvabilité (cf. app/ml/credit_scoring.py) : les
    features `nb_achats_credit_total`, `montant_moyen_achat`,
    `frequence_achat_mensuelle`, `solde_du_actuel`, `anciennete_client_mois`
    sont calculées à partir de ces ventes ; le `taux_retard` est dérivé
    déterministiquement de l'identifiant client (cf. en-tête du module).
    """
    branches = Branch.query.filter_by(is_depot=False, is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    admin = User.query.join(User.role).filter_by(name="ADMIN").first()
    cashier_by_branch = {b.id: pick_cashier(b, admin) for b in branches}

    if not branches or not products:
        return 0

    existing_names = {c.full_name for c in Customer.query.all()}
    created_customers = 0
    sale_rows: list[dict] = []
    line_rows: list[dict] = []

    for i in range(extra_customers):
        name = f"Client Crédit Synthétique {i + 1:03d}"
        if name in existing_names:
            continue

        customer = Customer(
            full_name=name,
            phone=None,
            customer_type=CustomerType.TECHNICIEN.value,
            credit_limit=Decimal(int(rng.choice([100000, 250000, 500000, 1000000]))),
        )
        db.session.add(customer)
        db.session.flush()
        created_customers += 1

        # Nombre d'achats à crédit sur la période (1 à 4 / mois en moyenne)
        nb_achats = int(rng.integers(max(1, months // 2), months * 4))
        for j in range(nb_achats):
            days_ago = int(rng.integers(0, months * 30))
            d = datetime.utcnow().date() - timedelta(days=days_ago)
            branch = branches[int(rng.integers(0, len(branches)))]
            product = products[int(rng.integers(0, len(products)))]
            qty = int(rng.integers(1, 5))
            unit_price = product.technician_price
            line_total = Decimal(unit_price) * qty
            sale_id = generate_uuid()
            offline_uuid = f"SYNTH-CREDIT-{customer.id}-{j}"

            sale_rows.append(
                {
                    "id": sale_id,
                    "reference": f"VTE-SYNTH-{d:%Y%m%d}-{generate_uuid()[:6].upper()}",
                    "branch_id": branch.id,
                    "cashier_id": cashier_by_branch[branch.id].id,
                    "customer_id": customer.id,
                    "subtotal": line_total,
                    "discount_rate": 0,
                    "discount_amount": Decimal("0"),
                    "total": line_total,
                    "payment_type": PaymentType.CREDIT.value,
                    "status": SaleStatus.VALIDEE.value,
                    "approved_by_id": None,
                    "offline_uuid": offline_uuid,
                    "refund_of_sale_id": None,
                    "created_at": datetime.combine(d, datetime.min.time()) + timedelta(hours=14),
                }
            )
            line_rows.append(
                {
                    "id": generate_uuid(),
                    "sale_id": sale_id,
                    "product_id": product.id,
                    "quantity": qty,
                    "unit_price_applied": unit_price,
                    "price_type": CustomerType.TECHNICIEN.value,
                    "line_total": line_total,
                }
            )

    if sale_rows:
        db.session.bulk_insert_mappings(Sale, sale_rows)
        db.session.bulk_insert_mappings(SaleLine, line_rows)
    db.session.commit()
    return created_customers


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=int, default=24, help="Historique en mois (défaut: 24)")
    parser.add_argument(
        "--extra-customers", type=int, default=40, help="Clients crédit synthétiques (défaut: 40)"
    )
    parser.add_argument("--seed", type=int, default=42, help="Graine aléatoire (défaut: 42)")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    app = create_app()
    with app.app_context():
        n_sales = generate_sales_history(app, args.months, rng)
        n_customers = generate_credit_customers(app, args.months, args.extra_customers, rng)

    print(
        f"Données synthétiques générées : {n_sales} ventes sur {args.months} mois, "
        f"{n_customers} nouveaux clients crédit."
    )


if __name__ == "__main__":
    main()
