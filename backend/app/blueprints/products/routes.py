"""Routes du blueprint `products` : sites, categories, marques, produits."""
from flask import jsonify, request
from sqlalchemy import or_

from app.blueprints.products import products_bp
from app.blueprints.products.schemas import (
    BrandSchema,
    BrandWriteSchema,
    BranchSchema,
    CategorySchema,
    CategoryWriteSchema,
    ProductCreateSchema,
    ProductSchema,
    ProductUpdateSchema,
)
from app.extensions import db
from app.models import Branch, Brand, Category, Product
from app.utils.dates import parse_updated_since
from app.utils.decorators import require_permission
from app.utils.errors import conflict, not_found, validation_error
from app.utils.phonetic import phonetic_code

branch_schema = BranchSchema(many=True)
category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)
brand_schema = BrandSchema()
brands_schema = BrandSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


@products_bp.get("/branches")
@require_permission("products:read", "sales:create", "stock:read")
def list_branches():
    branches = Branch.query.filter_by(is_active=True).order_by(Branch.name).all()
    return jsonify(branch_schema.dump(branches))


@products_bp.get("/categories")
@require_permission("products:read")
def list_categories():
    categories = Category.query.order_by(Category.name).all()
    return jsonify(categories_schema.dump(categories))


@products_bp.post("/categories")
@require_permission("products:write")
def create_category():
    payload = CategoryWriteSchema().load(request.get_json(silent=True) or {})

    if Category.query.filter_by(name=payload["name"]).first() is not None:
        raise conflict("CATEGORY_ALREADY_EXISTS", "Cette categorie existe deja.")

    category = Category(name=payload["name"], description=payload.get("description"))
    db.session.add(category)
    db.session.commit()
    return jsonify(category_schema.dump(category)), 201


@products_bp.get("/brands")
@require_permission("products:read")
def list_brands():
    brands = Brand.query.order_by(Brand.name).all()
    return jsonify(brands_schema.dump(brands))


@products_bp.post("/brands")
@require_permission("products:write")
def create_brand():
    payload = BrandWriteSchema().load(request.get_json(silent=True) or {})

    if Brand.query.filter_by(name=payload["name"]).first() is not None:
        raise conflict("BRAND_ALREADY_EXISTS", "Cette marque existe deja.")

    brand = Brand(name=payload["name"])
    db.session.add(brand)
    db.session.commit()
    return jsonify(brand_schema.dump(brand)), 201


@products_bp.get("/products")
@require_permission("products:read", "sales:create", "stock:read")
def list_products():
    """Liste paginee des produits, avec recherche et filtres."""
    query = Product.query

    search = (request.args.get("search") or "").strip()
    if search:
        like = "%" + search + "%"
        conditions = [
            Product.name.ilike(like),
            Product.name_moore.ilike(like),
            Product.sku.ilike(like),
            Product.barcode.ilike(like),
        ]

        search_phonetic = phonetic_code(search)
        if search_phonetic:
            conditions.append(Product.name_phonetic.ilike("%" + search_phonetic + "%"))

        query = query.filter(or_(*conditions))

    category_id = request.args.get("category_id")
    if category_id:
        query = query.filter(Product.category_id == category_id)

    brand_id = request.args.get("brand_id")
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)

    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter(Product.is_active == (is_active.lower() in ("1", "true", "yes")))
    else:
        query = query.filter(Product.is_active.is_(True))

    updated_since = parse_updated_since(request.args.get("updated_since"))
    if updated_since is not None:
        query = query.filter(Product.updated_at >= updated_since)

    page = request.args.get("page", default=1, type=int)
    per_page = min(request.args.get("per_page", default=20, type=int), 100)

    pagination = query.order_by(Product.name).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "data": products_schema.dump(pagination.items),
        "meta": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
        },
    })


@products_bp.post("/products")
@require_permission("products:write")
def create_product():
    """Cree un produit (RF-06). Les contraintes RG-21 sont verifiees en base."""
    payload = ProductCreateSchema().load(request.get_json(silent=True) or {})

    if Product.query.filter_by(sku=payload["sku"]).first() is not None:
        raise conflict("SKU_ALREADY_EXISTS", "Ce SKU est deja utilise.")

    if payload.get("barcode") and Product.query.filter_by(barcode=payload["barcode"]).first():
        raise conflict("BARCODE_ALREADY_EXISTS", "Ce code-barres est deja utilise.")

    if payload["category_id"]:
        if Category.query.get(payload["category_id"]) is None:
            raise not_found("Categorie", payload["category_id"])

    if payload["brand_id"]:
        if Brand.query.get(payload["brand_id"]) is None:
            raise not_found("Marque", payload["brand_id"])

    if payload["technician_price"] > payload["simple_price"]:
        raise validation_error(
            "Le prix technicien ne peut pas depasser le prix grand public (RG-21).",
            details={"technician_price": "doit etre <= simple_price"},
        )

    product = Product(**payload)
    db.session.add(product)
    db.session.commit()

    return jsonify(product_schema.dump(product)), 201


@products_bp.get("/products/<string:product_id>")
@require_permission("products:read", "sales:create", "stock:read")
def get_product(product_id: str):
    product = Product.query.get(product_id)
    if product is None:
        raise not_found("Produit", product_id)
    return jsonify(product_schema.dump(product))


@products_bp.patch("/products/<string:product_id>")
@require_permission("products:write")
def update_product(product_id: str):
    """Met a jour un produit (prix, seuils, statut...) - cf. RG-21."""
    product = Product.query.get(product_id)
    if product is None:
        raise not_found("Produit", product_id)

    payload = ProductUpdateSchema().load(request.get_json(silent=True) or {}, partial=True)

    if "barcode" in payload and payload["barcode"]:
        existing = Product.query.filter(
            Product.barcode == payload["barcode"], Product.id != product.id
        ).first()
        if existing is not None:
            raise conflict("BARCODE_ALREADY_EXISTS", "Ce code-barres est deja utilise.")

    if "category_id" in payload and payload["category_id"]:
        if Category.query.get(payload["category_id"]) is None:
            raise not_found("Categorie", payload["category_id"])

    if "brand_id" in payload and payload["brand_id"]:
        if Brand.query.get(payload["brand_id"]) is None:
            raise not_found("Marque", payload["brand_id"])

    new_simple = payload.get("simple_price", product.simple_price)
    new_technician = payload.get("technician_price", product.technician_price)
    if new_technician > new_simple:
        raise validation_error(
            "Le prix technicien ne peut pas depasser le prix grand public (RG-21).",
            details={"technician_price": "doit etre inferieur ou egal a simple_price"},
        )

    for field, value in payload.items():
        setattr(product, field, value)

    db.session.commit()
    return jsonify(product_schema.dump(product))
