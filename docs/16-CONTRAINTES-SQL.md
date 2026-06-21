# 16. Contraintes SQL, Triggers et Index

## 16.1 Récapitulatif des contraintes CHECK

| Table | Contrainte | Règle de gestion |
|---|---|---|
| `branches` | index unique partiel `type='DEPOT_CENTRAL'` | RG-01 : un seul dépôt central |
| `products` | `purchase_price > 0` | RG-08 |
| `products` | `retail_price >= purchase_price` | RG-09 |
| `products` | `technician_price <= retail_price AND technician_price >= purchase_price` | RG-10 |
| `products` | `reference` UNIQUE | RG-07 |
| `stock` | `quantity >= 0` | RG-13 (sauf gestion conflit offline en applicatif) |
| `stock` | UNIQUE `(product_id, branch_id)` | RG-13 |
| `transfers` | `dest_branch_id <> source_branch_id` | RG-15 |
| `transfers` | `status IN ('BROUILLON','EN_TRANSIT','RECU','ANNULE')` | RG-16 |
| `sales` | `total_amount >= 0` | RG-25 |
| `sales` | `status IN (...)` | Diagramme d'état 7.7 |
| `sales` | `offline_uuid` UNIQUE | RG-28 (idempotence) |
| `sale_lines` | `quantity > 0`, `unit_price_applied > 0` | RG-25 |
| `discounts` | `rate IN (5,10,15,20)` | RG-22 |
| `discounts` | `sale_id` UNIQUE | 1 remise par vente |
| `discounts` | `approved_by_user_id` NOT NULL | RG-23 |

## 16.2 Triggers PL/pgSQL

### Trigger 1 — Mise à jour automatique du stock après mouvement

```sql
CREATE OR REPLACE FUNCTION trg_apply_stock_movement()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE stock
    SET quantity = quantity + NEW.quantity,   -- NEW.quantity signé (+/-)
        updated_at = now()
    WHERE id = NEW.stock_id;

    -- Garde-fou : empêcher un stock négatif hors contexte offline
    IF (SELECT quantity FROM stock WHERE id = NEW.stock_id) < 0 THEN
        RAISE EXCEPTION 'STOCK_NEGATIVE_NOT_ALLOWED (stock_id=%)', NEW.stock_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_stock_movement_apply
AFTER INSERT ON stock_movements
FOR EACH ROW EXECUTE FUNCTION trg_apply_stock_movement();
```

> Pour les ventes synchronisées en conflit (`EN_CONFLIT`), l'application insère le mouvement via une fonction dédiée qui **bypass** temporairement la contrainte (`SET session_replication_role` ou flag applicatif), le stock négatif étant alors corrigé manuellement par l'administrateur.

### Trigger 2 — Interdiction de modification d'une vente validée (RG-27)

```sql
CREATE OR REPLACE FUNCTION trg_prevent_sale_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'VALIDEE' AND NEW.status NOT IN ('AVOIR_EMIS') THEN
        RAISE EXCEPTION 'SALE_IMMUTABLE: a validated sale cannot be modified (id=%)', OLD.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_sales_immutable
BEFORE UPDATE ON sales
FOR EACH ROW EXECUTE FUNCTION trg_prevent_sale_update();
```

### Trigger 3 — Journalisation automatique des changements de prix produit

```sql
CREATE OR REPLACE FUNCTION trg_audit_product_price_change()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.retail_price <> OLD.retail_price
       OR NEW.technician_price <> OLD.technician_price
       OR NEW.purchase_price <> OLD.purchase_price THEN
        INSERT INTO audit_logs (event_type, entity, entity_id, before_data, after_data)
        VALUES (
            'PRODUCT_PRICE_CHANGED', 'product', NEW.id,
            jsonb_build_object('purchase_price', OLD.purchase_price,
                                'retail_price', OLD.retail_price,
                                'technician_price', OLD.technician_price),
            jsonb_build_object('purchase_price', NEW.purchase_price,
                                'retail_price', NEW.retail_price,
                                'technician_price', NEW.technician_price)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_products_audit_price
AFTER UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION trg_audit_product_price_change();
```

### Trigger 4 — Mise à jour du solde client à la vente à crédit

```sql
CREATE OR REPLACE FUNCTION trg_update_customer_balance()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.customer_id IS NOT NULL AND NEW.status = 'VALIDEE' THEN
        UPDATE customers
        SET solde_du = solde_du + NEW.total_amount
        WHERE id = NEW.customer_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_sales_update_customer_balance
AFTER INSERT ON sales
FOR EACH ROW EXECUTE FUNCTION trg_update_customer_balance();
```

## 16.3 Index — synthèse et justification

| Index | Table | Colonnes | Justification (RNF-01 — latence < 200 ms) |
|---|---|---|---|
| `idx_products_category` | products | category_id | Filtrage catalogue par catégorie |
| `idx_products_name_trgm` | products | name (GIN trigram) | Recherche tolérante aux fautes (RF-08) |
| `idx_stock_branch_product` | stock | (branch_id, product_id) | Lecture stock boutique (écran caisse, très fréquent) |
| `idx_stock_movements_stock` | stock_movements | (stock_id, created_at) | Historique de mouvements, graphiques |
| `idx_sales_branch_date` | sales | (branch_id, created_at) | Rapports par boutique et période |
| `idx_sales_seller` | sales | seller_id | Filtrage par vendeur |
| `idx_predictions_product_branch` | predictions | (product_id, branch_id, created_at) | Lecture dernière prédiction par couple produit/site |
| `uq_branches_depot_central` | branches | type (partiel) | RG-01 |

## 16.4 Politique de verrouillage et transactions

- Toute opération de vente (`INSERT sale + sale_lines + stock_movements + discounts`) est exécutée dans **une transaction unique** avec niveau d'isolation `READ COMMITTED` et verrou `SELECT ... FOR UPDATE` sur la ligne `stock` concernée, afin d'éviter les conditions de concurrence (deux ventes simultanées sur le dernier exemplaire d'un produit).
- Les transferts suivent le même principe : verrouillage de la ligne `stock` source lors du passage en `EN_TRANSIT`.

## 16.5 Politique de purge / archivage

| Table | Politique |
|---|---|
| `audit_logs` | Partitions mensuelles ; partition > 12 mois exportée (JSON) vers stockage froid puis détachée (`DETACH PARTITION`) — RNF-18 |
| `predictions` | Purge des prédictions > 90 jours (sauf échantillon conservé pour évaluation des modèles) |
| `stock_movements` | Partitionnement annuel recommandé au-delà de 500k lignes (RNF-04) |
