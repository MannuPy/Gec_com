"""Service de gestion du stock : application des mouvements (RG-17, RG-24).

Toute variation de stock (réception, transfert, vente, ajustement) doit
passer par `apply_stock_movement` afin de garantir :
  - la cohérence de la table `stock` (une ligne par couple produit/site) ;
  - la traçabilité complète via `stock_movements` ;
  - le respect de la contrainte `quantity >= 0` (RG : pas de stock négatif).
"""
from app.extensions import db
from app.models import Stock, StockMovement
from app.utils.errors import ApiError


def get_or_create_stock_row(product_id: str, branch_id: str) -> Stock:
    """Retourne la ligne de stock (produit, site), en la créant à 0 si besoin."""
    stock = Stock.query.filter_by(product_id=product_id, branch_id=branch_id).first()
    if stock is None:
        stock = Stock(product_id=product_id, branch_id=branch_id, quantity=0)
        db.session.add(stock)
        db.session.flush()
    return stock


def apply_stock_movement(
    *,
    product_id: str,
    branch_id: str,
    quantity: int,
    movement_type: str,
    reference_type: str | None = None,
    reference_id: str | None = None,
    created_by_id: str | None = None,
    comment: str | None = None,
    allow_negative: bool = False,
) -> StockMovement:
    """Applique un mouvement de stock signé et journalise l'opération.

    `quantity` est signé : positif pour une entrée, négatif pour une sortie.
    Lève `INSUFFICIENT_STOCK` (409) si le mouvement ferait passer le stock
    sous zéro et que `allow_negative` est `False`.
    """
    if quantity == 0:
        raise ApiError("INVALID_MOVEMENT", "La quantité du mouvement ne peut pas être nulle.")

    stock = get_or_create_stock_row(product_id, branch_id)
    new_quantity = stock.quantity + quantity

    if new_quantity < 0 and not allow_negative:
        raise ApiError(
            "INSUFFICIENT_STOCK",
            "Stock insuffisant pour réaliser cette opération.",
            status_code=409,
            details={
                "product_id": product_id,
                "branch_id": branch_id,
                "available": stock.quantity,
                "requested": -quantity,
            },
        )

    stock.quantity = new_quantity

    movement = StockMovement(
        product_id=product_id,
        branch_id=branch_id,
        movement_type=movement_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by_id=created_by_id,
        comment=comment,
    )
    db.session.add(movement)
    return movement
