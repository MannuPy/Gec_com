"""
Service ETL — extraction, validation et feature engineering (§21.6, §21.2-21.4).

Ce module implémente les trois étapes orchestrées par
`app/tasks/etl_tasks.py` (cf. 21-PIPELINE-ETL.md §21.3) :

1. :func:`extract_and_clean` — extraction des données sources (ventes,
   lignes de vente, clients, échéances de remboursement RF-26) sur une
   fenêtre glissante, et nettoyage (valeurs manquantes, doublons) ;
2. :func:`validate` — contrôle qualité (§21.4) via Great Expectations si
   disponible, avec repli sur des contrôles pandas équivalents
   (`HAS_GREAT_EXPECTATIONS`, même logique de cascade que `app/ml/*`). En cas
   d'échec, :class:`EtlValidationError` est levée et bloque l'étape suivante
   (§21.4 : "l'étape suivante est bloquée") ;
3. :func:`build_features` — purge et recalcule les quatre tables de la
   Feature Store (`fs_daily_sales`, `fs_customer_rfm`,
   `fs_customer_credit_features`, `fs_transaction_features`), consommées en
   priorité par `app/ml/*` (avec repli sur leurs requêtes directes /
   simulations historiques si la Feature Store est vide).

Pour `fs_customer_credit_features`, le `data_source` (`REAL`/`SIMULATED`) est
déterminé client par client : si l'historique réel des échéances
(`customer_payments`, RF-26) compte au moins :data:`MIN_PAYMENTS_FOR_REAL_DATA`
échéances résolues, `taux_retard` et `delai_moyen_remboursement_jours` sont
calculés à partir de ces données réelles (`REAL`) ; sinon on retombe sur la
simulation déterministe documentée en §20.6.2 (`SIMULATED`,
`app.ml.credit_scoring._deterministic_repayment_stats`).
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from app.extensions import db
from app.ml.credit_scoring import TAUX_RETARD_SEUIL, _deterministic_repayment_stats
from app.models import (
    Customer,
    CustomerPayment,
    CustomerPaymentStatus,
    CustomerType,
    FeatureDataSource,
    FsCustomerCreditFeatures,
    FsCustomerRfm,
    FsDailySales,
    FsTransactionFeatures,
    PaymentType,
    Sale,
    SaleLine,
    SaleStatus,
)

try:
    import great_expectations as ge

    HAS_GREAT_EXPECTATIONS = True
except ImportError:
    HAS_GREAT_EXPECTATIONS = False

logger = logging.getLogger(__name__)

# Fenêtre d'extraction par défaut (~6 mois, cf. app/ml/demand_forecast.py).
EXTRACTION_WINDOW_DAYS = 180
# Fenêtre RFM (§20.4 / fs_customer_rfm).
RFM_WINDOW_MONTHS = 12
# Fenêtre glissante de détection d'anomalies (§21.6 : 30 jours).
ANOMALY_WINDOW_DAYS = 30

# Nombre minimal d'échéances résolues (PAID ou en retard constaté) pour
# considérer l'historique de remboursement d'un client comme suffisant
# (data_source=REAL). En deçà, repli sur la simulation déterministe (§20.6.2).
MIN_PAYMENTS_FOR_REAL_DATA = 3
# Au-delà de ce délai (jours), une échéance est considérée en retard.
LATE_THRESHOLD_DAYS = 30


class EtlValidationError(Exception):
    """Échec de la validation qualité (§21.4) — bloque l'étape suivante."""


# ---------------------------------------------------------------------------
# 21.2 — Extraction + nettoyage (B1)
# ---------------------------------------------------------------------------

def extract_and_clean(days: int = EXTRACTION_WINDOW_DAYS) -> dict[str, pd.DataFrame]:
    """Extrait et nettoie les données sources (§21.2, sources A1/A4).

    Retourne un dict de DataFrames :
    - ``sale_lines`` : lignes de vente (+ dimensions vente) sur la fenêtre
      ``days`` jours, nettoyées (lignes incomplètes/doublons supprimés) ;
    - ``customers`` : clients (référentiel complet) ;
    - ``customer_payments`` : échéances de remboursement RF-26 (référentiel
      complet, utilisé par :func:`_real_repayment_stats`).
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.session.query(
            SaleLine.id,
            SaleLine.sale_id,
            SaleLine.product_id,
            SaleLine.quantity,
            SaleLine.unit_price_applied,
            SaleLine.price_type,
            SaleLine.line_total,
            Sale.branch_id,
            Sale.cashier_id,
            Sale.customer_id,
            Sale.created_at,
            Sale.discount_rate,
            Sale.payment_type,
            Sale.status,
        )
        .join(Sale, SaleLine.sale_id == Sale.id)
        .filter(
            Sale.status.in_([SaleStatus.VALIDEE.value, SaleStatus.EN_ATTENTE_APPROBATION.value]),
            Sale.created_at >= cutoff,
        )
        .all()
    )
    columns = [
        "sale_line_id",
        "sale_id",
        "product_id",
        "quantity",
        "unit_price_applied",
        "price_type",
        "line_total",
        "branch_id",
        "cashier_id",
        "customer_id",
        "created_at",
        "discount_rate",
        "payment_type",
        "status",
    ]
    df_sales = pd.DataFrame(rows, columns=columns)

    raw_count = len(df_sales)
    if not df_sales.empty:
        # Nettoyage (§21.2 B1) : valeurs manquantes sur colonnes critiques,
        # doublons éventuels (resynchronisation hors-ligne).
        df_sales = df_sales.dropna(subset=["product_id", "branch_id", "quantity"])
        df_sales = df_sales.drop_duplicates(subset=["sale_line_id"])
        df_sales["quantity"] = df_sales["quantity"].astype(int)
        df_sales["unit_price_applied"] = df_sales["unit_price_applied"].astype(float)
        df_sales["line_total"] = df_sales["line_total"].astype(float)
        df_sales["discount_rate"] = df_sales["discount_rate"].astype(int)
    clean_count = len(df_sales)

    customers = Customer.query.all()
    df_customers = pd.DataFrame(
        [
            {
                "customer_id": c.id,
                "full_name": c.full_name,
                "customer_type": c.customer_type,
                "credit_balance": float(c.credit_balance),
                "credit_limit": float(c.credit_limit),
                "created_at": c.created_at,
            }
            for c in customers
        ]
    )

    payments = CustomerPayment.query.all()
    df_payments = pd.DataFrame(
        [
            {
                "customer_id": p.customer_id,
                "amount": float(p.amount),
                "due_date": p.due_date,
                "paid_date": p.paid_date,
                "status": p.status,
            }
            for p in payments
        ]
    )

    logger.info(
        "etl_extract_and_clean: %d lignes brutes -> %d apres nettoyage "
        "(%d clients, %d echeances de remboursement)",
        raw_count,
        clean_count,
        len(df_customers),
        len(df_payments),
    )

    return {"sale_lines": df_sales, "customers": df_customers, "customer_payments": df_payments}


# ---------------------------------------------------------------------------
# 21.4 — Validation qualité (Great Expectations + repli pandas)
# ---------------------------------------------------------------------------

def validate(data: dict[str, pd.DataFrame]) -> dict:
    """Valide la qualité des données extraites (§21.4).

    Lève :class:`EtlValidationError` en cas d'échec — l'étape suivante
    (``etl_build_features``) est alors bloquée, conformément à §21.4 :
    "En cas d'échec de validation, l'étape suivante est bloquée".
    """
    df = data.get("sale_lines", pd.DataFrame())

    if df.empty:
        return {
            "success": True,
            "checks": [{"expectation": "non_empty_dataset", "success": True}],
            "engine": "EMPTY",
        }

    if HAS_GREAT_EXPECTATIONS:
        result = _validate_great_expectations(df)
    else:
        result = _validate_pandas_fallback(df)

    if not result["success"]:
        logger.warning("etl_validate: validation en echec - %s", result["checks"])
        raise EtlValidationError(
            f"Validation qualite (§21.4) en echec : {result['checks']}"
        )

    return result


def _validate_pandas_fallback(df: pd.DataFrame) -> dict:
    """Repli pandas — implémente les mêmes règles que la suite Great
    Expectations de référence (§21.4) lorsque la bibliothèque n'est pas
    installée."""
    checks: list[dict] = []

    for col in ("product_id", "branch_id", "quantity"):
        checks.append(
            {"expectation": f"not_null_{col}", "success": bool(df[col].notna().all())}
        )

    checks.append(
        {
            "expectation": "quantity_between_0_10000",
            "success": bool(df["quantity"].between(0, 10000).all()),
        }
    )
    checks.append(
        {
            "expectation": "unit_price_applied_between_0_1000000",
            "success": bool(df["unit_price_applied"].between(0, 1_000_000).all()),
        }
    )
    checks.append(
        {
            "expectation": "price_type_in_set_SIMPLE_TECHNICIEN",
            "success": bool(df["price_type"].isin(["SIMPLE", "TECHNICIEN"]).all()),
        }
    )

    return {"success": all(c["success"] for c in checks), "checks": checks, "engine": "PANDAS_FALLBACK"}


def _validate_great_expectations(df: pd.DataFrame) -> dict:
    try:
        gdf = ge.from_pandas(df)
        checks: list[dict] = []

        for col in ("product_id", "branch_id", "quantity"):
            res = gdf.expect_column_values_to_not_be_null(col)
            checks.append({"expectation": f"not_null_{col}", "success": bool(res.success)})

        res = gdf.expect_column_values_to_be_between("quantity", min_value=0, max_value=10000)
        checks.append({"expectation": "quantity_between_0_10000", "success": bool(res.success)})

        res = gdf.expect_column_values_to_be_between(
            "unit_price_applied", min_value=0, max_value=1_000_000
        )
        checks.append(
            {"expectation": "unit_price_applied_between_0_1000000", "success": bool(res.success)}
        )

        res = gdf.expect_column_values_to_be_in_set("price_type", ["SIMPLE", "TECHNICIEN"])
        checks.append(
            {"expectation": "price_type_in_set_SIMPLE_TECHNICIEN", "success": bool(res.success)}
        )

        return {
            "success": all(c["success"] for c in checks),
            "checks": checks,
            "engine": "GREAT_EXPECTATIONS",
        }
    except Exception:  # pragma: no cover - GE ne doit jamais bloquer le pipeline lui-meme
        logger.exception("etl_validate: erreur Great Expectations, repli sur la validation pandas")
        return _validate_pandas_fallback(df)


# ---------------------------------------------------------------------------
# 21.6 — Feature engineering (purge + recalcul des tables fs_*)
# ---------------------------------------------------------------------------

def build_features(days: int = EXTRACTION_WINDOW_DAYS) -> dict:
    """Exécute le pipeline complet (extraction -> validation -> features) et
    purge/recalcule les quatre tables de la Feature Store (§21.6).

    Lève :class:`EtlValidationError` si la validation échoue (§21.4) : aucune
    table ``fs_*`` n'est alors modifiée.
    """
    data = extract_and_clean(days=days)
    validation = validate(data)

    summary = {
        "validation": validation,
        "fs_daily_sales": _build_fs_daily_sales(data["sale_lines"]),
        "fs_customer_rfm": _build_fs_customer_rfm(),
        "fs_customer_credit_features": _build_fs_customer_credit_features(),
        "fs_transaction_features": _build_fs_transaction_features(),
    }
    db.session.commit()
    logger.info("etl_build_features: %s", {k: v for k, v in summary.items() if k != "validation"})
    return summary


def _build_fs_daily_sales(df: pd.DataFrame) -> dict:
    """Purge et recalcule `fs_daily_sales` : ventes agrégées par jour /
    produit / boutique + features calendaires (alimente
    `app/ml/demand_forecast.py`)."""
    FsDailySales.query.delete()

    if df.empty:
        db.session.flush()
        return {"rows": 0}

    work = df.copy()
    work["sale_date"] = pd.to_datetime(work["created_at"]).dt.normalize()
    grouped = (
        work.groupby(["sale_date", "product_id", "branch_id"])
        .agg(quantity_sold=("quantity", "sum"), revenue=("line_total", "sum"))
        .reset_index()
    )

    now = datetime.utcnow()
    entries = []
    for _, r in grouped.iterrows():
        sale_date = r["sale_date"].date()
        entries.append(
            FsDailySales(
                sale_date=sale_date,
                product_id=r["product_id"],
                branch_id=r["branch_id"],
                quantity_sold=int(r["quantity_sold"]),
                revenue=round(float(r["revenue"]), 2),
                day_of_week=sale_date.weekday(),
                is_weekend=sale_date.weekday() >= 5,
                month=sale_date.month,
                computed_at=now,
            )
        )

    db.session.bulk_save_objects(entries)
    db.session.flush()
    return {"rows": len(entries)}


def _build_fs_customer_rfm(months: int = RFM_WINDOW_MONTHS) -> dict:
    """Purge et recalcule `fs_customer_rfm` : récence/fréquence/montant par
    client sur ``months`` mois (alimente `app/ml/rfm_segmentation.py`)."""
    FsCustomerRfm.query.delete()

    cutoff = datetime.utcnow() - timedelta(days=months * 30)
    rows = (
        db.session.query(Sale.customer_id, Sale.created_at, SaleLine.line_total)
        .join(SaleLine, SaleLine.sale_id == Sale.id)
        .filter(
            Sale.status == SaleStatus.VALIDEE.value,
            Sale.created_at >= cutoff,
            Sale.customer_id.isnot(None),
        )
        .all()
    )
    df = pd.DataFrame(rows, columns=["customer_id", "created_at", "line_total"])
    if df.empty:
        db.session.flush()
        return {"rows": 0}

    df["line_total"] = df["line_total"].astype(float)
    now = datetime.utcnow()
    period_start = cutoff.date()
    period_end = now.date()

    grouped = df.groupby("customer_id").agg(
        recency_days=("created_at", lambda s: (now - s.max()).days),
        frequency=("created_at", "count"),
        monetary=("line_total", "sum"),
    )

    entries = []
    for customer_id, r in grouped.iterrows():
        entries.append(
            FsCustomerRfm(
                customer_id=customer_id,
                recency_days=int(r["recency_days"]),
                frequency=int(r["frequency"]),
                monetary=round(float(r["monetary"]), 2),
                period_start=period_start,
                period_end=period_end,
                computed_at=now,
            )
        )

    db.session.bulk_save_objects(entries)
    db.session.flush()
    return {"rows": len(entries)}


def _real_repayment_stats(customer_id: str) -> tuple[float, float] | None:
    """Calcule ``(taux_retard, delai_moyen_remboursement_jours)`` à partir de
    l'historique réel des échéances de remboursement (`customer_payments`,
    RF-26).

    Retourne ``None`` si l'historique est insuffisant
    (< :data:`MIN_PAYMENTS_FOR_REAL_DATA` échéances résolues), pour repli sur
    la simulation déterministe (§20.6.2,
    `app.ml.credit_scoring._deterministic_repayment_stats`).

    Une échéance est dite "résolue" si elle a été réglée (`PAID`) ou si sa
    date d'échéance est dans le passé (impayé constaté). Elle est considérée
    en retard si le règlement (ou la situation actuelle, pour un impayé) a
    lieu plus de :data:`LATE_THRESHOLD_DAYS` jours après l'échéance.
    """
    payments = (
        CustomerPayment.query.filter_by(customer_id=customer_id)
        .filter(CustomerPayment.status != CustomerPaymentStatus.CANCELLED.value)
        .all()
    )
    today = date.today()
    resolved = [
        p
        for p in payments
        if p.status == CustomerPaymentStatus.PAID.value or (p.due_date and p.due_date < today)
    ]
    if len(resolved) < MIN_PAYMENTS_FOR_REAL_DATA:
        return None

    delays = []
    late_count = 0
    for p in resolved:
        reference_date = p.paid_date or today
        delay = (reference_date - p.due_date).days
        delays.append(max(delay, 0))
        if delay > LATE_THRESHOLD_DAYS:
            late_count += 1

    taux_retard = late_count / len(resolved)
    delai_moyen = float(np.mean(delays)) if delays else 0.0
    return round(taux_retard, 4), round(delai_moyen, 1)


def _build_fs_customer_credit_features() -> dict:
    """Purge et recalcule `fs_customer_credit_features` (RF-26, §20.3.2).

    Pour chaque client ayant un historique d'achats à crédit, `taux_retard`
    et `delai_moyen_remboursement_jours` sont issus en priorité de
    l'historique réel des règlements (`data_source=REAL`) ; à défaut
    d'historique suffisant, on retombe sur la simulation déterministe
    documentée en §20.6.2 (`data_source=SIMULATED`).
    """
    FsCustomerCreditFeatures.query.delete()

    customers = Customer.query.all()
    now = datetime.utcnow()
    entries = []

    for customer in customers:
        credit_sales = Sale.query.filter_by(
            customer_id=customer.id,
            payment_type=PaymentType.CREDIT.value,
            status=SaleStatus.VALIDEE.value,
        ).all()
        if not credit_sales:
            continue

        nb_achats = len(credit_sales)
        montant_moyen = float(np.mean([float(s.total) for s in credit_sales]))
        anciennete_mois = max((now - customer.created_at).days / 30.0, 1 / 30.0)
        frequence_mensuelle = nb_achats / anciennete_mois

        real_stats = _real_repayment_stats(customer.id)
        if real_stats is not None:
            taux_retard, delai_moyen = real_stats
            data_source = FeatureDataSource.REAL.value
        else:
            taux_retard, delai_moyen = _deterministic_repayment_stats(customer.id)
            data_source = FeatureDataSource.SIMULATED.value

        entries.append(
            FsCustomerCreditFeatures(
                customer_id=customer.id,
                nb_achats_credit_total=nb_achats,
                montant_moyen_achat=round(montant_moyen, 2),
                delai_moyen_remboursement_jours=delai_moyen,
                taux_retard=taux_retard,
                anciennete_client_mois=round(anciennete_mois, 2),
                frequence_achat_mensuelle=round(frequence_mensuelle, 3),
                solde_du_actuel=round(float(customer.credit_balance), 2),
                is_technicien=customer.customer_type == CustomerType.TECHNICIEN.value,
                bon_payeur=taux_retard < TAUX_RETARD_SEUIL,
                data_source=data_source,
                computed_at=now,
            )
        )

    db.session.bulk_save_objects(entries)
    db.session.flush()

    n_real = sum(1 for e in entries if e.data_source == FeatureDataSource.REAL.value)
    return {
        "rows": len(entries),
        "data_source_real": n_real,
        "data_source_simulated": len(entries) - n_real,
    }


def _build_fs_transaction_features(days: int = ANOMALY_WINDOW_DAYS) -> dict:
    """Purge et recalcule `fs_transaction_features` : features de détection
    d'anomalies sur une fenêtre glissante de ``days`` jours (alimente
    `app/ml/anomaly_detection.py`)."""
    FsTransactionFeatures.query.delete()

    cutoff = datetime.utcnow() - timedelta(days=days)
    sales = Sale.query.filter(
        Sale.status.in_([SaleStatus.VALIDEE.value, SaleStatus.EN_ATTENTE_APPROBATION.value]),
        Sale.created_at >= cutoff,
    ).all()

    if not sales:
        db.session.flush()
        return {"rows": 0}

    rows = []
    for sale in sales:
        main_product_id = sale.lines[0].product_id if sale.lines else None
        rows.append(
            {
                "sale_id": sale.id,
                "branch_id": sale.branch_id,
                "cashier_id": sale.cashier_id,
                "product_id": main_product_id,
                "montant_total": float(sale.total),
                "remise_taux": int(sale.discount_rate),
                "heure_vente": sale.created_at.hour,
            }
        )
    df = pd.DataFrame(rows)

    product_mean = df.groupby("product_id")["montant_total"].transform("mean")
    cashier_mean = df.groupby("cashier_id")["montant_total"].transform("mean")
    df["ecart_vs_moyenne_produit"] = (df["montant_total"] - product_mean) / product_mean.replace(0, np.nan)
    df["ecart_vs_moyenne_vendeur"] = (df["montant_total"] - cashier_mean) / cashier_mean.replace(0, np.nan)
    df[["ecart_vs_moyenne_produit", "ecart_vs_moyenne_vendeur"]] = df[
        ["ecart_vs_moyenne_produit", "ecart_vs_moyenne_vendeur"]
    ].fillna(0.0)

    now = datetime.utcnow()
    entries = []
    for _, r in df.iterrows():
        entries.append(
            FsTransactionFeatures(
                sale_id=r["sale_id"],
                branch_id=r["branch_id"],
                cashier_id=r["cashier_id"],
                product_id=r["product_id"],
                montant_total=float(r["montant_total"]),
                quantity=int(r["quantity"]),
                ecart_vs_moyenne_produit=float(r["ecart_vs_moyenne_produit"]),
                ecart_vs_moyenne_vendeur=float(r["ecart_vs_moyenne_vendeur"]),
                computed_at=now,
            )
        )
    db.session.bulk_save_objects(entries)
    db.session.commit()
    return len(entries)
