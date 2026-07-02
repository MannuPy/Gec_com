"""
Analyse de l'élasticité-prix des remises par produit.

Élasticité = (ΔQ/Q) / (ΔP/P)
  < -1 : demande élastique — la remise augmente le CA total (rentable)
  > -1 : demande inélastique — la remise diminue le CA total (non rentable)

Méthode : régression log-log sur les ventes validées.
  ln(quantité) = α + β × ln(1 - taux_remise)
  β est l'élasticité.

Note modèle : Sale.discount_rate est un entier (0, 5, 10, 15, 20).
              SaleLine utilise unit_price_applied (prix effectif appliqué).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.extensions import db
from app.models import Product, Sale, SaleLine, SaleStatus


def compute_elasticity(
    months: int = 6,
    branch_id: str = None,
    min_sales: int = 20,
) -> dict:
    """
    Calcule l'élasticité-remise pour chaque produit ayant suffisamment de données.
    Utilise une régression log-log : ln(quantité) = α + β × ln(1 - taux_remise).
    β est l'élasticité.

    Args:
        months:    Fenêtre temporelle d'analyse (défaut 6 mois).
        branch_id: Filtrer par site (None = tous les sites).
        min_sales: Nombre minimum de lignes de vente pour inclure un produit.

    Returns:
        Liste de dicts triés par élasticité absolue décroissante.
    """
    cutoff = datetime.utcnow() - timedelta(days=months * 30)

    query = (
        db.session.query(
            SaleLine.product_id,
            Product.name.label("product_name"),
            SaleLine.quantity,
            SaleLine.unit_price_applied,
            Sale.discount_rate,          # entier : 0, 5, 10, 15, 20
        )
        .join(Sale, SaleLine.sale_id == Sale.id)
        .join(Product, Product.id == SaleLine.product_id)
        .filter(
            Sale.status == SaleStatus.VALIDEE.value,
            Sale.created_at >= cutoff,
            SaleLine.unit_price_applied > 0,
        )
    )
    if branch_id:
        query = query.filter(Sale.branch_id == branch_id)

    df = pd.DataFrame(
        query.all(),
        columns=["product_id", "product_name", "quantity", "unit_price_applied", "discount_rate"],
    )
    if df.empty:
        # Retourner une réponse structurée avec diagnostic plutôt que []
        return {"items": [], "count": 0, "diagnostic": "Aucune vente trouvée sur la période."}

    # Vérifier si des remises existent dans la base
    has_any_discount = (df["discount_rate"].astype(float) > 0).any()
    if not has_any_discount:
        # Calculer quand même les stats de vente sans remise (utile pour le jury)
        stats_sans_remise = []
        for product_id, group in df.assign(
            discount_rate=df["discount_rate"].astype(float) / 100.0,
            quantity=df["quantity"].astype(float),
        ).groupby("product_id"):
            if len(group) < min_sales:
                continue
            stats_sans_remise.append({
                "product_id":   str(product_id),
                "product_name": group["product_name"].iloc[0],
                "nb_sales":     len(group),
                "avg_discount_rate": 0.0,
                "elasticity":   None,
                "r_squared":    None,
                "interpretation": "Aucune remise enregistrée — élasticité non calculable",
                "recommendation": "Tester une remise de 5 % sur quelques produits pour mesurer la sensibilité",
            })
        return {
            "items":      stats_sans_remise,
            "count":      len(stats_sans_remise),
            "diagnostic": (
                "Aucune remise (discount_rate > 0) dans les données de la période. "
                "L'élasticité nécessite des ventes avec et sans remise pour être calculée. "
                "Les produits sont listés avec leurs volumes de vente."
            ),
        }

    # Convertir le taux entier en float 0-1
    df["discount_rate"] = df["discount_rate"].astype(float) / 100.0
    df["quantity"] = df["quantity"].astype(float)

    results = []
    for product_id, group in df.groupby("product_id"):
        if len(group) < min_sales:
            continue

        product_name = group["product_name"].iloc[0]

        with_discount    = group[group["discount_rate"] > 0.02]
        without_discount = group[group["discount_rate"] <= 0.02]

        avg_discount     = float(with_discount["discount_rate"].mean()) if not with_discount.empty else 0.0
        avg_qty_without  = float(without_discount["quantity"].mean())   if not without_discount.empty else None
        avg_qty_with     = float(with_discount["quantity"].mean())      if not with_discount.empty else None

        # Régression log-log (nécessite sklearn, présent comme dépendance)
        elasticity = None
        r_squared  = None
        discounted = group[group["discount_rate"] > 0]
        if len(discounted) >= 5:
            try:
                from sklearn.linear_model import LinearRegression
                X_log = np.log(
                    1 - discounted["discount_rate"].clip(0, 0.99) + 1e-6
                ).values.reshape(-1, 1)
                y_log = np.log(discounted["quantity"].clip(0.1)).values
                reg = LinearRegression().fit(X_log, y_log)
                elasticity = round(float(reg.coef_[0]), 3)
                r_squared  = round(float(reg.score(X_log, y_log)), 3)
            except Exception:
                pass

        results.append({
            "product_id":             str(product_id),
            "product_name":           product_name,
            "nb_sales":               len(group),
            "avg_discount_rate":      round(avg_discount, 3),
            "avg_qty_without_discount": round(avg_qty_without, 2) if avg_qty_without is not None else None,
            "avg_qty_with_discount":    round(avg_qty_with, 2)    if avg_qty_with    is not None else None,
            "elasticity":             elasticity,
            "r_squared":              r_squared,
            "interpretation":         _interpret_elasticity(elasticity),
            "recommendation":         _recommend_discount_policy(elasticity, avg_discount),
        })

    # Fix : normalise le type de retour — toujours un dict {"items", "count", "diagnostic"}
    # (les chemins no-data et no-discount retournaient deja un dict, ce chemin retournait une liste)
    return {
        "items": sorted(results, key=lambda r: abs(r.get("elasticity") or 0), reverse=True),
        "count": len(results),
        "diagnostic": None,
    }


def _interpret_elasticity(e: float | None) -> str:
    if e is None:  return "Données insuffisantes pour calculer l'élasticité"
    if e < -2.0:   return "Très élastique — les remises augmentent fortement le volume"
    if e < -1.0:   return "Élastique — les remises sont globalement rentables en volume"
    if e < -0.5:   return "Faiblement élastique — les remises ont un effet limité"
    if e <  0.0:   return "Inélastique — les remises n'améliorent pas significativement le volume"
    return "Élasticité positive — comportement atypique (produit de luxe ou erreur de données)"


def _recommend_discount_policy(e: float | None, avg_discount: float) -> str:
    pct = f"{avg_discount:.0%}"
    if e is None:  return "Collecter plus de données avant de décider"
    if e < -1.5:   return "Maintenez ou augmentez les remises — fort levier commercial"
    if e < -1.0:   return f"Remise actuelle ({pct}) efficace — à conserver"
    if e < -0.5:   return "Réduire les remises — gain de volume trop faible par rapport au manque à gagner"
    return "Supprimer les remises sur ce produit — elles ne stimulent pas les ventes"
