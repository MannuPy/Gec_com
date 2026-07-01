"""
Analyse du panier d'achat par règles d'association (Algorithme Apriori).
Identifie les couples et triplets de produits fréquemment achetés ensemble
pour les recommandations de vente croisée au point de vente (RF-26).

Repli : co-occurrence simple si mlxtend est indisponible.
Fréquence de ré-entraînement : hebdomadaire (tâche cron PythonAnywhere).
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from itertools import combinations

import pandas as pd

from app.extensions import db
from app.ml.common import record_predictions, register_model, latest_predictions
from app.models import Product, Sale, SaleLine, SaleStatus

PREDICTION_TYPE = "MARKET_BASKET"
MODEL_TYPE = "MARKET_BASKET"

try:
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder
    HAS_MLXTEND = True
except ImportError:
    HAS_MLXTEND = False


# ---------------------------------------------------------------------------
# Chargement des données
# ---------------------------------------------------------------------------

def _load_transactions(months: int = 6, branch_id: str = None) -> list[list[str]]:
    """Charge les transactions validées comme listes de noms de produits par vente."""
    cutoff = datetime.utcnow() - timedelta(days=months * 30)
    query = (
        db.session.query(Sale.id, Product.name)
        .join(SaleLine, SaleLine.sale_id == Sale.id)
        .join(Product, Product.id == SaleLine.product_id)
        .filter(
            Sale.status == SaleStatus.VALIDEE.value,
            Sale.created_at >= cutoff,
        )
    )
    if branch_id:
        query = query.filter(Sale.branch_id == branch_id)

    rows = query.all()
    if not rows:
        return []

    df = pd.DataFrame(rows, columns=["sale_id", "product_name"])
    transactions = df.groupby("sale_id")["product_name"].apply(list).tolist()
    # Garder uniquement les paniers multi-produits (association impossible sinon)
    return [t for t in transactions if len(t) >= 2]


# ---------------------------------------------------------------------------
# Algorithmes
# ---------------------------------------------------------------------------

def _apriori_rules(
    transactions: list,
    min_support: float = 0.02,
    min_confidence: float = 0.30,
    min_lift: float = 1.2,
) -> pd.DataFrame:
    """Règles d'association via l'algorithme Apriori (mlxtend)."""
    te = TransactionEncoder()
    te_array = te.fit(transactions).transform(transactions)
    df_encoded = pd.DataFrame(te_array, columns=te.columns_)

    frequent_itemsets = apriori(
        df_encoded,
        min_support=min_support,
        use_colnames=True,
        max_len=3,
    )
    if frequent_itemsets.empty:
        return pd.DataFrame()

    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_lift)
    rules = rules[rules["confidence"] >= min_confidence]
    return rules.sort_values("lift", ascending=False)


def _fallback_cooccurrence(transactions: list, top_n: int = 20) -> list[dict]:
    """
    Fallback sans mlxtend : co-occurrence simple par paire de produits.
    Moins rigoureux mathématiquement mais entièrement fonctionnel.
    """
    pair_counts: Counter = Counter()
    product_counts: Counter = Counter()
    total = len(transactions)

    for transaction in transactions:
        unique = list(set(transaction))
        for product in unique:
            product_counts[product] += 1
        for pair in combinations(sorted(unique), 2):
            pair_counts[pair] += 1

    results = []
    for (p1, p2), count in pair_counts.most_common(top_n):
        support = count / total
        conf_p1_p2 = count / product_counts[p1] if product_counts[p1] else 0
        conf_p2_p1 = count / product_counts[p2] if product_counts[p2] else 0
        p2_support = product_counts[p2] / total
        lift = conf_p1_p2 / p2_support if p2_support else 0

        results.append({
            "antecedent":    p1,
            "consequent":    p2,
            "support":       round(support, 4),
            "confidence":    round(max(conf_p1_p2, conf_p2_p1), 4),
            "lift":          round(lift, 3),
            "co_occurrences": count,
        })
    return results


# ---------------------------------------------------------------------------
# Entraînement
# ---------------------------------------------------------------------------

def train(
    months: int = 6,
    branch_id: str = None,
    min_support: float = 0.02,
    min_confidence: float = 0.30,
) -> dict:
    """Calcule les règles d'association et les stocke dans la table `predictions`."""
    transactions = _load_transactions(months=months, branch_id=branch_id)

    if len(transactions) < 30:
        return {
            "status":          "skipped",
            "reason":          f"Transactions insuffisantes : {len(transactions)} (minimum 30)",
            "nb_transactions": len(transactions),
        }

    algorithm = "FALLBACK_COOCCURRENCE"
    rules_list: list[dict] = []

    if HAS_MLXTEND:
        rules_df = _apriori_rules(
            transactions,
            min_support=min_support,
            min_confidence=min_confidence,
        )
        if not rules_df.empty:
            algorithm = "APRIORI"
            for _, row in rules_df.head(50).iterrows():
                rules_list.append({
                    "antecedent": list(row["antecedents"]),
                    "consequent": list(row["consequents"]),
                    "support":    round(float(row["support"]), 4),
                    "confidence": round(float(row["confidence"]), 4),
                    "lift":       round(float(row["lift"]), 3),
                })

    if not rules_list:
        rules_list = _fallback_cooccurrence(transactions)
        algorithm = "FALLBACK_COOCCURRENCE"

    metrics = {
        "nb_transactions": len(transactions),
        "nb_rules":        len(rules_list),
        "min_support":     min_support,
        "min_confidence":  min_confidence,
        "top_lift":        round(rules_list[0]["lift"], 3) if rules_list else 0.0,
    }

    model = register_model(
        model_type=MODEL_TYPE,
        algorithm=algorithm,
        metrics=metrics,
    )

    entries = [
        {
            "entity_type": "product_pair",
            "entity_id":   f"rule_{i}",
            "payload": {
                "rule":      rule,
                "branch_id": branch_id,
            },
        }
        for i, rule in enumerate(rules_list)
    ]
    record_predictions(model, PREDICTION_TYPE, entries)
    db.session.commit()

    return {"status": "success", **metrics}


# ---------------------------------------------------------------------------
# Lecture des prédictions
# ---------------------------------------------------------------------------

def latest(
    branch_id: str = None,
    min_lift: float = 1.0,
    product_name: str = None,
) -> list[dict]:
    """Retourne les règles stockées, filtrées par branch_id, lift et produit."""
    payloads = [p.payload_json for p in latest_predictions(PREDICTION_TYPE)]

    # Filtre par site
    if branch_id:
        payloads = [p for p in payloads if p.get("branch_id") == branch_id]

    # Extraire les règles imbriquées dans "rule"
    rules = [p.get("rule", p) for p in payloads]

    # Filtre par lift minimum
    if min_lift > 1.0:
        rules = [r for r in rules if r.get("lift", 0) >= min_lift]

    # Filtre par nom de produit
    if product_name:
        pn = product_name.lower()
        rules = [
            r for r in rules
            if pn in str(r.get("antecedent", "")).lower()
            or pn in str(r.get("consequent", "")).lower()
        ]

    return sorted(rules, key=lambda r: r.get("lift", 0), reverse=True)
