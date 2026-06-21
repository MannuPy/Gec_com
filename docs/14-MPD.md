# 14. Modèle Physique de Données (MPD) — DDL PostgreSQL

## 14.1 Préambule

Ce DDL est généré par les migrations **Alembic** et adapté automatiquement au dialecte de la base de données via `backend/app/utils/db_dialect.py` :

| Dialecte | Mode | Schémas |
|---|---|---|
| **PostgreSQL 16** (dev Docker / VPS) | Multi-tenant | DDL exécuté dans `tenant_<slug>` ; `companies`/`user_index` dans `public` |
| **MySQL 8.0** (PythonAnywhere) | Mono-tenant | Toutes les tables dans `<user>$gescom_bf` — pas de `CREATE SCHEMA`, pas de `SET search_path` |

Le DDL ci-dessous représente la **structure de référence PostgreSQL**. Les différences MySQL notables sont :

- `UUID` → `VARCHAR(36)` (Alembic génère `CHAR(36)` sur MySQL avec SQLAlchemy `String`)
- `TIMESTAMPTZ` → `DATETIME` (MySQL n'a pas de type timezone-aware natif ; les timestamps sont stockés en UTC)
- `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"` → absent (non supporté ; les UUID sont générés en Python via `uuid.uuid4()`)
- `CHECK` contraintes : appliquées seulement depuis MySQL 8.0.16+ (ignorées silencieusement sur versions antérieures — validation assurée au niveau applicatif)
- `BOOLEAN` / `sa.false()` → `TINYINT(1)` avec `DEFAULT 0` sur MySQL

```sql
-- ============================================================
-- Extension utile pour génération d'UUID (PostgreSQL uniquement)
-- Sur MySQL, les UUID sont générés par l'application (uuid.uuid4())
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE : branches
-- ============================================================
CREATE TABLE branches (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(150) NOT NULL,
    type            VARCHAR(20) NOT NULL CHECK (type IN ('DEPOT_CENTRAL','BOUTIQUE')),
    address         VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- RG-01 : un seul dépôt central par schéma tenant
CREATE UNIQUE INDEX uq_branches_depot_central
    ON branches (type) WHERE (type = 'DEPOT_CENTRAL');

-- ============================================================
-- TABLE : roles / permissions
-- ============================================================
CREATE TABLE roles (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(50) NOT NULL UNIQUE,   -- ADMIN, MAGASINIER, VENDEUR
    description VARCHAR(255)
);

CREATE TABLE permissions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code        VARCHAR(100) NOT NULL UNIQUE,  -- ex: sales.create, stock.transfer.approve
    description VARCHAR(255)
);

CREATE TABLE role_permissions (
    role_id        UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id  UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- ============================================================
-- TABLE : users
-- ============================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    branch_id       UUID REFERENCES branches(id) ON DELETE RESTRICT,
    role_id         UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- TABLE : categories / brands
-- ============================================================
CREATE TABLE categories (
    id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE brands (
    id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE
);

-- ============================================================
-- TABLE : products
-- ============================================================
CREATE TABLE products (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id         UUID REFERENCES categories(id) ON DELETE RESTRICT,
    brand_id            UUID REFERENCES brands(id) ON DELETE RESTRICT,
    name                VARCHAR(200) NOT NULL,
    name_moore          VARCHAR(200),
    reference           VARCHAR(100) NOT NULL UNIQUE,
    purchase_price      NUMERIC(12,2) NOT NULL CHECK (purchase_price > 0),
    retail_price        NUMERIC(12,2) NOT NULL CHECK (retail_price >= purchase_price),
    technician_price    NUMERIC(12,2) NOT NULL CHECK (technician_price <= retail_price
                                                        AND technician_price >= purchase_price),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_name_trgm ON products USING gin (name gin_trgm_ops);

-- ============================================================
-- TABLE : stock
-- ============================================================
CREATE TABLE stock (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id  UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    branch_id   UUID NOT NULL REFERENCES branches(id) ON DELETE RESTRICT,
    quantity    INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    min_stock   INTEGER NOT NULL DEFAULT 0 CHECK (min_stock >= 0),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, branch_id)
);
CREATE INDEX idx_stock_branch_product ON stock(branch_id, product_id);

-- ============================================================
-- TABLE : stock_movements
-- ============================================================
CREATE TABLE stock_movements (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id        UUID NOT NULL REFERENCES stock(id) ON DELETE CASCADE,
    type            VARCHAR(30) NOT NULL CHECK (type IN
                       ('RECEPTION','VENTE','TRANSFERT_SORTANT','TRANSFERT_ENTRANT',
                        'AJUSTEMENT_INVENTAIRE')),
    quantity        INTEGER NOT NULL,             -- positif ou négatif selon type
    reference_id    UUID,                          -- id de la vente / transfert / inventaire
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_stock_movements_stock ON stock_movements(stock_id, created_at);

-- ============================================================
-- TABLE : suppliers / supplier_receptions / lines
-- ============================================================
CREATE TABLE suppliers (
    id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name      VARCHAR(150) NOT NULL,
    phone     VARCHAR(30),
    address   VARCHAR(255)
);

CREATE TABLE supplier_receptions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id     UUID NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    branch_id       UUID NOT NULL REFERENCES branches(id) ON DELETE RESTRICT, -- toujours DEPOT_CENTRAL (RG-14)
    reference_bon   VARCHAR(100),
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE supplier_reception_lines (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reception_id         UUID NOT NULL REFERENCES supplier_receptions(id) ON DELETE CASCADE,
    product_id           UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity_received    INTEGER NOT NULL CHECK (quantity_received > 0),
    purchase_unit_price  NUMERIC(12,2) NOT NULL CHECK (purchase_unit_price > 0)
);

-- ============================================================
-- TABLE : customers
-- ============================================================
CREATE TABLE customers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(150) NOT NULL,
    phone           VARCHAR(30),
    type_client     VARCHAR(20) NOT NULL DEFAULT 'SIMPLE' CHECK (type_client IN ('SIMPLE','TECHNICIEN')),
    solde_du        NUMERIC(12,2) NOT NULL DEFAULT 0,
    credit_score    NUMERIC(5,2),               -- 0-100, NULL si jamais calculé
    score_updated_at TIMESTAMPTZ
);

-- ============================================================
-- TABLE : transfers / transfer_lines
-- ============================================================
CREATE TABLE transfers (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_branch_id    UUID NOT NULL REFERENCES branches(id),
    dest_branch_id      UUID NOT NULL REFERENCES branches(id) CHECK (dest_branch_id <> source_branch_id),
    status              VARCHAR(20) NOT NULL DEFAULT 'BROUILLON'
                          CHECK (status IN ('BROUILLON','EN_TRANSIT','RECU','ANNULE')),
    created_by          UUID NOT NULL REFERENCES users(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    received_at         TIMESTAMPTZ
);

CREATE TABLE transfer_lines (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transfer_id     UUID NOT NULL REFERENCES transfers(id) ON DELETE CASCADE,
    product_id      UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity        INTEGER NOT NULL CHECK (quantity > 0)
);

-- ============================================================
-- TABLE : sales / sale_lines / discounts
-- ============================================================
CREATE TABLE sales (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    branch_id       UUID NOT NULL REFERENCES branches(id),
    seller_id       UUID NOT NULL REFERENCES users(id),
    customer_id     UUID REFERENCES customers(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'VALIDEE'
                       CHECK (status IN ('VALIDEE','EN_ATTENTE_SYNC','EN_CONFLIT','ANNULEE','AVOIR_EMIS')),
    channel         VARCHAR(10) NOT NULL DEFAULT 'ONLINE' CHECK (channel IN ('ONLINE','OFFLINE')),
    offline_uuid    UUID UNIQUE,                 -- idempotence sync (RG-28)
    total_amount    NUMERIC(14,2) NOT NULL CHECK (total_amount >= 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    client_created_at TIMESTAMPTZ                -- horodatage côté client (offline)
);
CREATE INDEX idx_sales_branch_date ON sales(branch_id, created_at);
CREATE INDEX idx_sales_seller ON sales(seller_id);

CREATE TABLE sale_lines (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sale_id                 UUID NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id              UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity                INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_applied      NUMERIC(12,2) NOT NULL CHECK (unit_price_applied > 0),
    price_type              VARCHAR(15) NOT NULL CHECK (price_type IN ('SIMPLE','TECHNICIEN'))
);

CREATE TABLE discounts (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sale_id                 UUID NOT NULL UNIQUE REFERENCES sales(id) ON DELETE CASCADE,
    rate                    NUMERIC(4,2) NOT NULL CHECK (rate IN (5,10,15,20)),
    approved_by_user_id     UUID NOT NULL REFERENCES users(id),
    approval_note           VARCHAR(255)
);

-- ============================================================
-- TABLE : inventories / inventory_lines
-- ============================================================
CREATE TABLE inventories (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    branch_id       UUID NOT NULL REFERENCES branches(id),
    status          VARCHAR(15) NOT NULL DEFAULT 'EN_COURS' CHECK (status IN ('EN_COURS','VALIDE')),
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    validated_at    TIMESTAMPTZ
);

CREATE TABLE inventory_lines (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    inventory_id        UUID NOT NULL REFERENCES inventories(id) ON DELETE CASCADE,
    product_id          UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    theoretical_qty     INTEGER NOT NULL,
    counted_qty         INTEGER NOT NULL,
    justification       VARCHAR(255)
    -- RG-33 : justification obligatoire si |écart| > 5%, vérifié au niveau applicatif
);

-- ============================================================
-- TABLE : audit_logs (append-only)
-- ============================================================
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id),
    event_type      VARCHAR(50) NOT NULL,
    entity          VARCHAR(50) NOT NULL,
    entity_id       UUID,
    before_data     JSONB,
    after_data      JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

-- Partitions mensuelles créées par tâche planifiée (cf. 25-DEPLOIEMENT-CICD.md)
CREATE TABLE audit_logs_2026_06 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

-- ============================================================
-- TABLE : ml_models / predictions
-- ============================================================
CREATE TABLE ml_models (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type            VARCHAR(50) NOT NULL,   -- PROPHET_STOCK, XGBOOST_STOCK, CREDIT_SCORING, ISOLATION_FOREST, ABC_XYZ
    version         VARCHAR(50) NOT NULL,
    trained_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    metrics         JSONB,                  -- RMSE, MAE, precision, recall, etc.
    artifact_path   VARCHAR(255),
    UNIQUE (type, version)
);

CREATE TABLE predictions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id        UUID NOT NULL REFERENCES ml_models(id),
    product_id      UUID REFERENCES products(id),
    branch_id       UUID REFERENCES branches(id),
    type            VARCHAR(50) NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_predictions_product_branch ON predictions(product_id, branch_id, created_at);
```

## 14.2 Table globale `companies` (schéma `public`)

```sql
-- Schéma public — registre des tenants
CREATE TABLE public.companies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(150) NOT NULL,
    schema_name     VARCHAR(63) NOT NULL UNIQUE,  -- ex: tenant_quincaillerie_ouaga
    subscription_plan VARCHAR(20) NOT NULL DEFAULT 'FREEMIUM'
                        CHECK (subscription_plan IN ('FREEMIUM','STANDARD','PREMIUM')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 14.3 Notes d'implémentation

- L'extension `pg_trgm` (utilisée pour `idx_products_name_trgm`) doit être activée : `CREATE EXTENSION IF NOT EXISTS pg_trgm;` — elle permet la recherche tolérante aux fautes (RF-08) via similarité trigramme, en complément de la recherche côté client (Fuse.js, mode offline).
- Le partitionnement de `audit_logs` (et optionnellement `sales`, `stock_movements` au-delà de 500k lignes) est géré par une tâche Celery mensuelle qui crée la partition du mois suivant.
- Toutes les tables utilisent `UUID` comme clé primaire (génération `uuid_generate_v4()`) pour faciliter la synchronisation offline (les UUID générés côté client ne collisionnent pas avec le serveur).
