# 15. Dictionnaire des données

Légende : **PK** = clé primaire, **FK** = clé étrangère, **NN** = NOT NULL, **U** = UNIQUE.

## 15.1 `companies` (schéma `public`)

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| id | UUID | PK | Identifiant du tenant |
| name | VARCHAR(150) | NN | Nom de l'entreprise cliente |
| schema_name | VARCHAR(63) | NN, U | Nom du schéma PostgreSQL dédié |
| subscription_plan | VARCHAR(20) | NN, défaut FREEMIUM | Plan tarifaire (cf. `27-MODELE-SAAS-MULTITENANT.md`) |
| is_active | BOOLEAN | NN, défaut TRUE | Tenant actif / suspendu |
| created_at | TIMESTAMPTZ | NN | Date de création |

## 15.2 `branches`

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| id | UUID | PK | Identifiant du site |
| name | VARCHAR(150) | NN | Nom du site (ex. "Dépôt Central", "Boutique Tanghin") |
| type | VARCHAR(20) | NN, CHECK IN (DEPOT_CENTRAL, BOUTIQUE) | Type de site |
| address | VARCHAR(255) | - | Adresse physique |
| created_at | TIMESTAMPTZ | NN | Date de création |

Contrainte additionnelle : un seul enregistrement `type='DEPOT_CENTRAL'` par tenant (RG-01).

## 15.3 `roles` / `permissions` / `role_permissions`

| Table | Champ | Type | Contraintes | Description |
|---|---|---|---|---|
| roles | id | UUID | PK | Identifiant rôle |
| roles | name | VARCHAR(50) | NN, U | ADMIN / MAGASINIER / VENDEUR |
| roles | description | VARCHAR(255) | - | Description |
| permissions | id | UUID | PK | Identifiant permission |
| permissions | code | VARCHAR(100) | NN, U | Code (ex. `sales.create`, `discounts.approve`) |
| permissions | description | VARCHAR(255) | - | Description |
| role_permissions | role_id | UUID | PK(1/2), FK→roles | - |
| role_permissions | permission_id | UUID | PK(2/2), FK→permissions | - |

## 15.4 `users`

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| id | UUID | PK | Identifiant utilisateur |
| branch_id | UUID | FK→branches, nullable | Site de rattachement (NULL pour Admin multi-sites) |
| role_id | UUID | NN, FK→roles | Rôle de l'utilisateur |
| full_name | VARCHAR(150) | NN | Nom complet |
| email | VARCHAR(150) | NN, U | Identifiant de connexion |
| password_hash | VARCHAR(255) | NN | Hash bcrypt/argon2 du mot de passe |
| is_active | BOOLEAN | NN, défaut TRUE | Compte actif |
| must_change_password | BOOLEAN | NN, défaut TRUE | Forcer changement (RF-05) |
| last_login | TIMESTAMPTZ | - | Dernière connexion |
| created_at | TIMESTAMPTZ | NN | Date de création |

## 15.5 `categories` / `brands`

| Table | Champ | Type | Contraintes | Description |
|---|---|---|---|---|
| categories | id | UUID | PK | Identifiant |
| categories | name | VARCHAR(100) | NN, U | Nom de catégorie (ex. "Quincaillerie", "Peinture") |
| brands | id | UUID | PK | Identifiant |
| brands | name | VARCHAR(100) | NN, U | Nom de marque |

## 15.6 `products`

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| id | UUID | PK | Identifiant produit |
| category_id | UUID | FK→categories | Catégorie |
| brand_id | UUID | FK→brands | Marque |
| name | VARCHAR(200) | NN | Désignation (français) |
| name_moore | VARCHAR(200) | - | Désignation en mooré (RF-09) |
| reference | VARCHAR(100) | NN, U | Référence interne unique (RG-07) |
| purchase_price | NUMERIC(12,2) | NN, CHECK > 0 | Prix d'achat (RG-08) |
| retail_price | NUMERIC(12,2) | NN, CHECK >= purchase_price | Prix client simple (RG-09) |
| technician_price | NUMERIC(12,2) | NN, CHECK <= retail_price et >= purchase_price | Prix technicien (RG-10) |
| is_active | BOOLEAN | NN, défaut TRUE | Soft-delete (RG-11) |
| created_at | TIMESTAMPTZ | NN | Date de création |

## 15.7 `stock` / `stock_movements`

| Table | Champ | Type | Contraintes | Description |
|---|---|---|---|---|
| stock | id | UUID | PK | Identifiant ligne de stock |
| stock | product_id | UUID | NN, FK→products | Produit concerné |
| stock | branch_id | UUID | NN, FK→branches | Site concerné (RG-13) |
| stock | quantity | INTEGER | NN, CHECK >= 0, défaut 0 | Quantité disponible |
| stock | min_stock | INTEGER | NN, CHECK >= 0 | Seuil d'alerte (RG-12, par produit ET par site) |
| stock | updated_at | TIMESTAMPTZ | NN | Dernière mise à jour |
| stock | (product_id, branch_id) | - | UNIQUE | Un seul enregistrement par couple |
| stock_movements | id | UUID | PK | Identifiant mouvement |
| stock_movements | stock_id | UUID | NN, FK→stock | Ligne de stock concernée |
| stock_movements | type | VARCHAR(30) | NN, CHECK IN (...) | RECEPTION, VENTE, TRANSFERT_SORTANT, TRANSFERT_ENTRANT, AJUSTEMENT_INVENTAIRE (RG-19) |
| stock_movements | quantity | INTEGER | NN | Quantité (signée) |
| stock_movements | reference_id | UUID | - | Référence vers vente/transfert/inventaire/réception |
| stock_movements | created_at | TIMESTAMPTZ | NN | Horodatage |

## 15.8 `suppliers` / `supplier_receptions` / `supplier_reception_lines`

| Table | Champ | Type | Contraintes | Description |
|---|---|---|---|---|
| suppliers | id | UUID | PK | Identifiant |
| suppliers | name | VARCHAR(150) | NN | Nom du fournisseur |
| suppliers | phone | VARCHAR(30) | - | Téléphone |
| suppliers | address | VARCHAR(255) | - | Adresse |
| supplier_receptions | id | UUID | PK | Identifiant réception |
| supplier_receptions | supplier_id | UUID | NN, FK→suppliers | Fournisseur |
| supplier_receptions | branch_id | UUID | NN, FK→branches | Toujours le dépôt central (RG-14) |
| supplier_receptions | reference_bon | VARCHAR(100) | - | Référence bon de livraison |
| supplier_receptions | created_by | UUID | NN, FK→users | Magasinier ayant saisi |
| supplier_receptions | created_at | TIMESTAMPTZ | NN | Date de réception |
| supplier_reception_lines | id | UUID | PK | Identifiant ligne |
| supplier_reception_lines | reception_id | UUID | NN, FK→supplier_receptions | Réception parente |
| supplier_reception_lines | product_id | UUID | NN, FK→products | Produit reçu |
| supplier_reception_lines | quantity_received | INTEGER | NN, CHECK > 0 | Quantité reçue |
| supplier_reception_lines | purchase_unit_price | NUMERIC(12,2) | NN, CHECK > 0 | Prix d'achat unitaire constaté |

## 15.9 `customers`

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| id | UUID | PK | Identifiant client |
| name | VARCHAR(150) | NN | Nom du client |
| phone | VARCHAR(30) | - | Téléphone |
| type_client | VARCHAR(20) | NN, CHECK IN (SIMPLE, TECHNICIEN), défaut SIMPLE | Détermine le tarif appliqué (RG-21) |
| solde_du | NUMERIC(12,2) | NN, défaut 0 | Solde dû en cas de vente à crédit (RG-26) |
| credit_score | NUMERIC(5,2) | nullable, 0-100 | Score de solvabilité (RG-39, cf. `20-MACHINE-LEARNING.md`) |
| score_updated_at | TIMESTAMPTZ | - | Date de dernier calcul du score |

## 15.10 `transfers` / `transfer_lines`

| Table | Champ | Type | Contraintes | Description |
|---|---|---|---|---|
| transfers | id | UUID | PK | Identifiant transfert |
| transfers | source_branch_id | UUID | NN, FK→branches | Site source (RG-15) |
| transfers | dest_branch_id | UUID | NN, FK→branches, CHECK ≠ source | Site destination |
| transfers | status | VARCHAR(20) | NN, CHECK IN (...), défaut BROUILLON | Cycle de vie (RG-16, cf. diagramme état 7.6) |
| transfers | created_by | UUID | NN, FK→users | Créateur |
| transfers | created_at | TIMESTAMPTZ | NN | Date de création |
| transfers | received_at | TIMESTAMPTZ | nullable | Date de réception confirmée |
| transfer_lines | id | UUID | PK | Identifiant ligne |
| transfer_lines | transfer_id | UUID | NN, FK→transfers | Transfert parent |
| transfer_lines | product_id | UUID | NN, FK→products | Produit transféré |
| transfer_lines | quantity | INTEGER | NN, CHECK > 0 | Quantité transférée |

## 15.11 `sales` / `sale_lines` / `discounts`

| Table | Champ | Type | Contraintes | Description |
|---|---|---|---|---|
| sales | id | UUID | PK | Identifiant vente |
| sales | branch_id | UUID | NN, FK→branches | Boutique de vente (RG-20) |
| sales | seller_id | UUID | NN, FK→users | Vendeur (RG-20) |
| sales | customer_id | UUID | FK→customers, nullable | Client (obligatoire si crédit — RG-26) |
| sales | status | VARCHAR(20) | NN, CHECK IN (...) | VALIDEE / EN_ATTENTE_SYNC / EN_CONFLIT / ANNULEE / AVOIR_EMIS |
| sales | channel | VARCHAR(10) | NN, CHECK IN (ONLINE, OFFLINE) | Canal de saisie |
| sales | offline_uuid | UUID | U, nullable | UUID généré côté client pour idempotence (RG-28) |
| sales | total_amount | NUMERIC(14,2) | NN, CHECK >= 0 | Montant total (RG-25) |
| sales | created_at | TIMESTAMPTZ | NN | Date d'enregistrement serveur |
| sales | client_created_at | TIMESTAMPTZ | nullable | Horodatage de saisie côté client (offline) |
| sale_lines | id | UUID | PK | Identifiant ligne |
| sale_lines | sale_id | UUID | NN, FK→sales | Vente parente |
| sale_lines | product_id | UUID | NN, FK→products | Produit vendu |
| sale_lines | quantity | INTEGER | NN, CHECK > 0 | Quantité vendue |
| sale_lines | unit_price_applied | NUMERIC(12,2) | NN, CHECK > 0 | Prix unitaire appliqué (historisé, RG-27) |
| sale_lines | price_type | VARCHAR(15) | NN, CHECK IN (SIMPLE, TECHNICIEN) | Type de tarif appliqué |
| discounts | id | UUID | PK | Identifiant remise |
| discounts | sale_id | UUID | NN, U, FK→sales | Vente concernée (1 remise max par vente) |
| discounts | rate | NUMERIC(4,2) | NN, CHECK IN (5,10,15,20) | Taux de remise (RG-22) |
| discounts | approved_by_user_id | UUID | NN, FK→users | Administrateur ayant donné son accord (RG-23) |
| discounts | approval_note | VARCHAR(255) | - | Note libre |

## 15.12 `inventories` / `inventory_lines`

| Table | Champ | Type | Contraintes | Description |
|---|---|---|---|---|
| inventories | id | UUID | PK | Identifiant inventaire |
| inventories | branch_id | UUID | NN, FK→branches | Site concerné (RG-31) |
| inventories | status | VARCHAR(15) | NN, CHECK IN (EN_COURS, VALIDE) | État |
| inventories | created_by | UUID | NN, FK→users | Créateur |
| inventories | created_at | TIMESTAMPTZ | NN | Date de lancement |
| inventories | validated_at | TIMESTAMPTZ | nullable | Date de validation |
| inventory_lines | id | UUID | PK | Identifiant ligne |
| inventory_lines | inventory_id | UUID | NN, FK→inventories | Inventaire parent |
| inventory_lines | product_id | UUID | NN, FK→products | Produit compté |
| inventory_lines | theoretical_qty | INTEGER | NN | Quantité théorique au lancement |
| inventory_lines | counted_qty | INTEGER | NN | Quantité physiquement comptée |
| inventory_lines | justification | VARCHAR(255) | conditionnelle (RG-33) | Obligatoire si \|écart\| > 5 % |

## 15.13 `audit_logs`

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| id | UUID | PK | Identifiant log |
| user_id | UUID | FK→users, nullable | Utilisateur à l'origine (NULL si système) |
| event_type | VARCHAR(50) | NN | Ex. LOGIN_SUCCESS, SALE_CREATED, DISCOUNT_APPLIED, TRANSFER_RECEIVED, SALE_CONFLICT |
| entity | VARCHAR(50) | NN | Type d'entité concernée (sale, transfer, user, ...) |
| entity_id | UUID | nullable | Identifiant de l'entité |
| before_data | JSONB | nullable | État avant modification |
| after_data | JSONB | nullable | État après modification |
| created_at | TIMESTAMPTZ | NN | Horodatage UTC (RG-34) |

Table partitionnée par mois (`created_at`), rétention 1 an (RNF-18, RG-35).

## 15.14 `ml_models` / `predictions`

| Table | Champ | Type | Contraintes | Description |
|---|---|---|---|---|
| ml_models | id | UUID | PK | Identifiant modèle |
| ml_models | type | VARCHAR(50) | NN | PROPHET_STOCK / XGBOOST_STOCK / CREDIT_SCORING / ISOLATION_FOREST / ABC_XYZ |
| ml_models | version | VARCHAR(50) | NN | Version sémantique (ex. `2026.06.1`) |
| ml_models | trained_at | TIMESTAMPTZ | NN | Date d'entraînement |
| ml_models | metrics | JSONB | - | RMSE, MAE, précision, rappel, etc. (cf. `20-MACHINE-LEARNING.md`) |
| ml_models | artifact_path | VARCHAR(255) | - | Chemin de l'artefact (MLflow) |
| ml_models | (type, version) | - | UNIQUE | - |
| predictions | id | UUID | PK | Identifiant prédiction |
| predictions | model_id | UUID | NN, FK→ml_models | Modèle utilisé (RG-40, lineage) |
| predictions | product_id | UUID | FK→products, nullable | Produit concerné |
| predictions | branch_id | UUID | FK→branches, nullable | Site concerné |
| predictions | type | VARCHAR(50) | NN | RUPTURE_STOCK / CREDIT_SCORE / ANOMALIE / ABC_XYZ |
| predictions | payload | JSONB | NN | Contenu de la prédiction (valeurs, intervalles de confiance, recommandations) |
| predictions | created_at | TIMESTAMPTZ | NN | Date de génération |
