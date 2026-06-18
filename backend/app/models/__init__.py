"""
Regroupe l'ensemble des modeles pour que Flask-Migrate / Alembic detecte
toutes les tables lors de `flask db migrate`.
"""
from app.models.auth import Role, Permission, RolePermission, User, TokenBlocklist
from app.models.company import Company, SubscriptionPlan, SubscriptionStatus, UserIndex
from app.models.catalog import (
    Branch,
    Category,
    Brand,
    Product,
    Stock,
    StockMovement,
    StockMovementType,
    ProductUnit,
)
from app.models.supplier import (
    Supplier,
    SupplierReception,
    SupplierReceptionLine,
    ReceptionStatus,
)
from app.models.transfer import Transfer, TransferLine, TransferStatus
from app.models.sales import (
    Customer,
    CustomerPayment,
    CustomerPaymentStatus,
    Sale,
    SaleLine,
    CustomerType,
    PaymentType,
    SaleStatus,
    SaleChannel,
)
from app.models.audit import AuditLog
from app.models.ml import MLModel, Prediction, MLModelType
from app.models.inventory import StockCount, StockCountLine, StockCountStatus
from app.models.feature_store import (
    FeatureDataSource,
    FsDailySales,
    FsCustomerRfm,
    FsCustomerCreditFeatures,
    FsTransactionFeatures,
)

__all__ = [
    "Role",
    "Permission",
    "RolePermission",
    "User",
    "TokenBlocklist",
    "Company",
    "SubscriptionPlan",
    "SubscriptionStatus",
    "UserIndex",
    "Branch",
    "Category",
    "Brand",
    "Product",
    "Stock",
    "StockMovement",
    "StockMovementType",
    "ProductUnit",
    "Supplier",
    "SupplierReception",
    "SupplierReceptionLine",
    "ReceptionStatus",
    "Transfer",
    "TransferLine",
    "TransferStatus",
    "Customer",
    "CustomerPayment",
    "CustomerPaymentStatus",
    "Sale",
    "SaleLine",
    "CustomerType",
    "PaymentType",
    "SaleStatus",
    "SaleChannel",
    "AuditLog",
    "MLModel",
    "Prediction",
    "MLModelType",
    "StockCount",
    "StockCountLine",
    "StockCountStatus",
    "FeatureDataSource",
    "FsDailySales",
    "FsCustomerCreditFeatures",
    "FsCustomerRfm",
    "FsTransactionFeatures",
]
