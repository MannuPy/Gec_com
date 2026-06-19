"""Feature Store (ETL) - tables intermediaires."""
from __future__ import annotations

import enum

from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin


class FeatureDataSource(str, enum.Enum):
    REAL = "REAL"
    SIMULATED = "SIMULATED"


class FsDailySales(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "fs_daily_sales"

    sale_date = db.Column(db.Date, nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False, index=True)

    quantity_sold = db.Column(db.Integer, nullable=False, default=0)
    revenue = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    day_of_week = db.Column(db.Integer, nullable=False)
    is_weekend = db.Column(db.Boolean, nullable=False, default=False)
    month = db.Column(db.Integer, nullable=False)

    computed_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    product = db.relationship("Product", lazy="joined")
    branch = db.relationship("Branch", lazy="joined")

    __table_args__ = (
        db.UniqueConstraint(
            "sale_date", "product_id", "branch_id", name="uq_fs_daily_sales_date_product_branch"
        ),
    )


class FsCustomerRfm(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "fs_customer_rfm"

    customer_id = db.Column(
        db.String(36), db.ForeignKey("customers.id"), nullable=False, unique=True, index=True
    )

    recency_days = db.Column(db.Integer, nullable=False)
    frequency = db.Column(db.Integer, nullable=False)
    monetary = db.Column(db.Numeric(12, 2), nullable=False)

    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)

    computed_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    customer = db.relationship("Customer", lazy="joined")


class FsCustomerCreditFeatures(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "fs_customer_credit_features"

    customer_id = db.Column(
        db.String(36), db.ForeignKey("customers.id"), nullable=False, unique=True, index=True
    )

    nb_achats_credit_total = db.Column(db.Integer, nullable=False, default=0)
    montant_moyen_achat = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    delai_moyen_remboursement_jours = db.Column(db.Float, nullable=False, default=0)
    taux_retard = db.Column(db.Float, nullable=False, default=0)
    anciennete_client_mois = db.Column(db.Float, nullable=False, default=0)
    frequence_achat_mensuelle = db.Column(db.Float, nullable=False, default=0)
    solde_du_actuel = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    is_technicien = db.Column(db.Boolean, nullable=False, default=False)
    bon_payeur = db.Column(db.Boolean, nullable=False, default=True)

    data_source = db.Column(db.String(16), nullable=False, default=FeatureDataSource.SIMULATED.value)
    computed_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    customer = db.relationship("Customer", lazy="joined")

    __table_args__ = (
        db.CheckConstraint(
            "data_source IN ('REAL', 'SIMULATED')", name="ck_fs_credit_features_data_source"
        ),
    )


class FsTransactionFeatures(db.Model, UUIDPrimaryKeyMixin):
    __tablename__ = "fs_transaction_features"

    sale_id = db.Column(
        db.String(36), db.ForeignKey("sales.id"), nullable=False, unique=True, index=True
    )
    branch_id = db.Column(db.String(36), db.ForeignKey("branches.id"), nullable=False)
    cashier_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=True)

    montant_total = db.Column(db.Numeric(12, 2), nullable=False)
    remise_taux = db.Column(db.Integer, nullable=False, default=0)
    heure_vente = db.Column(db.Integer, nullable=False)
    ecart_vs_moyenne_produit = db.Column(db.Float, nullable=False, default=0)
    ecart_vs_moyenne_vendeur = db.Column(db.Float, nullable=False, default=0)

    computed_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    sale = db.relationship("Sale", lazy="joined")
    branch = db.relationship("Branch", lazy="joined")
