# GesCom-BF — Rapport Technique de Projet
## Système de Gestion Commerciale SaaS avec Intelligence Artificielle pour les Quincailleries du Burkina Faso

---

**Étudiant :** Ilboudom Mannu  
**Contact :** ilboudomannudev@gmail.com  
**Type de projet :** Mémoire de fin d'études — Option Analyse de Données / Développement Logiciel  
**Stack principale :** Flask · React/TypeScript · PostgreSQL/MySQL · Prophet · XGBoost · scikit-learn  
**Déploiement :** [https://mannudev.pythonanywhere.com](https://mannudev.pythonanywhere.com)  
**Dépôt documentation :** `docs/` (34 fichiers, ~800 pages de spécifications)

---

## Table des matières

1. [Contexte et problématique](#1-contexte-et-problématique)
2. [Bien-fondé du projet](#2-bien-fondé-du-projet)
3. [Périmètre fonctionnel](#3-périmètre-fonctionnel)
4. [Architecture technique](#4-architecture-technique)
5. [Backend Flask](#5-backend-flask)
6. [Frontend React PWA](#6-frontend-react-pwa)
7. [Base de données](#7-base-de-données)
8. [Sécurité et RBAC](#8-sécurité-et-rbac)
9. [Mode Offline-First (PWA)](#9-mode-offline-first-pwa)
10. [Module Analyse de données et Intelligence Artificielle](#10-module-analyse-de-données-et-intelligence-artificielle)
11. [Architecture SaaS Multi-tenant](#11-architecture-saas-multi-tenant)
12. [Déploiement et CI/CD](#12-déploiement-et-cicd)
13. [Qualité et tests](#13-qualité-et-tests)
14. [Méthodologie de développement](#14-méthodologie-de-développement)
15. [État d'avancement et perspectives](#15-état-davancement-et-perspectives)

---

## 1. Contexte et problématique

### 1.1 Contexte général

Au Burkina Faso, le secteur de la quincaillerie et des pièces détachées (automobile, motocycle, BTP) est dominé par des commerces de taille petite à moyenne, généralement organisés autour d'un **dépôt central** et d'un réseau de **boutiques de vente**. La gestion de ces structures reste encore très largement manuelle :

- Suivi des stocks sur cahiers ou fichiers Excel non centralisés entre sites
- Absence de visibilité en temps réel sur les niveaux de stock entre le dépôt et les boutiques
- Erreurs fréquentes de tarification (tarif client simple vs tarif technicien)
- Remises accordées de façon informelle, sans traçabilité ni approbation formelle
- Aucune anticipation des ruptures de stock, conduisant à des pertes de ventes
- Aucune donnée exploitable pour la prise de décision stratégique

Cette situation engendre des **pertes financières directes** (ruptures de stock, surstockage, remises non contrôlées, vols non détectés) et une **incapacité à piloter l'activité** sur plusieurs points de vente simultanément.

### 1.2 Problématique centrale

> Comment doter les quincailleries et boutiques de pièces détachées du Burkina Faso d'un outil de gestion commerciale **centralisé, fiable, accessible même en cas de coupure internet**, et capable de **transformer leurs données de vente en aide à la décision** (prévisions de rupture, alertes de stock, scoring crédit client) ?

### 1.3 Analyse de l'existant

| Solution | Points forts | Limites dans le contexte BF |
|---|---|---|
| **Odoo / Sage** | Complets, modulaires | Surdimensionnés, coûteux (licence + infrastructure), exigent une connexion stable, interface complexe |
| **Wave ERP** | Adapté Afrique | Limités sur le module IA, pas de mode offline robuste |
| **Excel / cahiers** | Familiers | Aucune centralisation multi-boutiques, aucune analyse prédictive, risque d'erreurs élevé |
| **Applications mobiles locales** | Légères | Pas de gestion multi-sites, pas de module IA |

**Conclusion :** Aucune solution existante ne répond simultanément aux contraintes de connectivité intermittente, de gestion multi-boutiques, et d'analyse de données contextualisée (saisonnalité locale : Tabaski, saison des pluies, etc.).

---

## 2. Bien-fondé du projet

### 2.1 Valeur métier

GesCom-BF apporte une valeur mesurable sur plusieurs axes :

**Réduction des pertes financières**
- Alerte automatique avant rupture de stock (modèle Prophet, horizon 7-30 jours)
- Traçabilité complète des remises accordées (qui, quand, combien, approuvé par qui)
- Détection automatique d'anomalies sur les ventes et les stocks (Isolation Forest)

**Amélioration de la prise de décision**
- Tableau de bord temps réel : chiffre d'affaires, marges, rotation de stock
- Classification ABC/XYZ des produits : identification des 20 % de produits générant 80 % du CA
- Segmentation clients RFM : identification des clients à fidéliser

**Continuité de service**
- 100 % des ventes enregistrables en mode hors-ligne (PWA + IndexedDB)
- Synchronisation automatique au retour de la connexion
- Aucune interruption du point de vente lors des coupures réseau fréquentes

### 2.2 Valeur académique

Ce projet s'inscrit dans l'option **Analyse de données** du cursus, démontrant la maîtrise de :

- La conception d'une architecture logicielle complète (3-tiers, API-first)
- La mise en œuvre d'un pipeline ETL sur données réelles
- L'application de modèles de Machine Learning à un problème métier concret
- Le déploiement d'une application en production avec les contraintes réelles associées
- La modélisation SaaS multi-tenant (architecture avancée)

### 2.3 Objectifs SMART

| # | Objectif | Indicateur | Cible |
|---|---|---|---|
| O1 | Centraliser gestion stock dépôt + boutiques | 100 % des mouvements tracés | Sprint 3 |
| O2 | Réduire le temps de saisie d'une vente | Saisie < 30 secondes | Sprint 5 |
| O3 | Anticiper les ruptures de stock | RMSE modèle < 15 % de la demande | Sprint 8-9 |
| O4 | Garantir continuité hors-ligne | 100 % des ventes saisissables offline | Sprint 6-7 |
| O5 | Sécuriser l'accès aux données | 0 accès non autorisé aux tests | Sprint 2 |
| O6 | Détecter les anomalies de gestion | Taux faux positifs < 10 % | Sprint 10 |
| O7 | Tableau de bord décisionnel | Rafraîchissement < 2 secondes | Sprint 9-10 |
| O8 | Couverture de tests | ≥ 80 % (pytest + Jest) | Continu |

---

## 3. Périmètre fonctionnel

### 3.1 Exigences fonctionnelles (32 RF)

Le système couvre **10 modules métier** avec 32 exigences fonctionnelles classées selon la matrice MoSCoW :

**Module Authentification & Utilisateurs (RF-01 à RF-05)**
- Inscription entreprise (tenant) avec administrateur initial
- Connexion via email/mot de passe avec délivrance de JWT (access + refresh token)
- CRUD utilisateurs avec attribution de rôles (Admin, Magasinier, Vendeur)
- Forçage du changement de mot de passe à la première connexion

**Module Catalogue Produits (RF-06 à RF-09)**
- Gestion des catégories, marques, et produits avec double tarification
- Recherche phonétique avec tolérance aux fautes de frappe
- Libellé produit bilingue (français + mooré)

**Module Fournisseurs & Approvisionnement (RF-10 à RF-11)**
- Gestion des fournisseurs avec historique d'achats
- Enregistrement des réceptions au dépôt central

**Module Stock & Transferts (RF-12 à RF-14)**
- Stock distinct par site (dépôt central + N boutiques)
- Transferts inter-sites avec cycle d'état (Brouillon → En transit → Reçu)
- Mise à jour automatique des stocks à chaque mouvement

**Module Ventes (RF-15 à RF-20)**
- Vente avec tarif client simple ou technicien
- Remises encadrées : {5 %, 10 %, 15 %, 20 %} uniquement, avec approbation administrateur
- Vente à crédit avec suivi du solde dû
- Génération de reçu PDF
- **Saisie de vente en mode hors-ligne** avec synchronisation différée

**Module Inventaires (RF-21 à RF-23)**
- Inventaire physique par site avec calcul des écarts stock théorique/physique
- Validation et ajustement automatique du stock

**Module Rapports & Analytics (RF-24 à RF-29)**
- Rapports consolidés multi-boutiques (CA, marges, rotations)
- Dashboard BI temps réel avec streaming SSE
- Export PDF des rapports
- Classification ABC/XYZ des produits
- Scoring de solvabilité client (crédit informel)
- Prévision de rupture de stock par produit/boutique

**Module IA & Détection (RF-26 à RF-28)**
- Détection d'anomalies sur ventes, remises et stocks
- Modèles ML entraînés sur données historiques

**Module Audit & Sécurité (RF-30 à RF-32)**
- Journal d'audit complet de toutes les actions sensibles
- Traçabilité des modifications de données critiques

### 3.2 Utilisateurs du système

| Rôle | Responsabilités | Accès |
|---|---|---|
| **Administrateur** | Pilotage global : utilisateurs, rapports, module IA, validation remises | Complet (scopé à son tenant) |
| **Magasinier** | Réceptions fournisseurs, transferts, inventaires dépôt | Dépôt, stock, transferts, inventaires |
| **Vendeur** | Saisie des ventes en boutique, consultation stock boutique | Ventes, stock boutique (lecture) |
| **Super-Administrateur SaaS** | Gestion des tenants, monitoring plateforme | Accès plateforme globale |

---

## 4. Architecture technique

### 4.1 Vue d'ensemble

GesCom-BF est une application **3-tiers** avec une architecture **API-first** :

```
┌─────────────────────────────────────────────────────────┐
│  PRÉSENTATION                                           │
│  React 18 + TypeScript + Vite (SPA/PWA)                │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTPS / REST JSON + SSE
┌─────────────────────▼───────────────────────────────────┐
│  REVERSE PROXY                                          │
│  Nginx (VPS) · uWSGI (PythonAnywhere)                  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  APPLICATION                                            │
│  Flask 3 + Blueprints (API REST)                       │
│  Celery Workers + Celery Beat (VPS)                    │
│  Flask CLI Scheduled Tasks (PythonAnywhere)            │
└──────┬──────────────┬─────────────────────┬─────────────┘
       │              │                     │
┌──────▼──────┐  ┌────▼──────┐  ┌──────────▼──────────┐
│ PostgreSQL  │  │   MySQL   │  │  Redis               │
│ (dev/VPS)   │  │ (PythonAn)│  │  (cache/queue/pubsub)│
│ Multi-tenant│  │ Mono-tenant│  └─────────────────────┘
└─────────────┘  └───────────┘
```

### 4.2 Stack technologique

| Couche | Technologie | Rôle |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite | SPA + PWA offline-first |
| Gestion d'état | TanStack Query (React Query) | Cache serveur, synchronisation, retry |
| Style | Tailwind CSS | Responsive, cohérence design |
| Backend | Flask 3 + Blueprints | API REST modulaire, 11 blueprints |
| ORM / Migrations | SQLAlchemy 2 + Alembic | Persistance, versioning schéma |
| Authentification | Flask-JWT-Extended | JWT access (15 min) + refresh (7 jours) |
| Sérialisation | Marshmallow | Validation, sérialisation JSON |
| DB production | MySQL 8.0 (PythonAnywhere) | Mono-tenant, driver PyMySQL |
| DB développement | PostgreSQL 16 | Multi-tenant schema-per-tenant |
| Cache / Queue | Redis 7 | Cache API, file Celery, pub/sub SSE |
| Tâches async | Celery + Celery Beat (VPS) | ETL, ML, alertes |
| IA | scikit-learn + Prophet + XGBoost | Prévision, scoring, anomalies |
| Suivi ML | MLflow | Registry modèles, data lineage |
| Conteneurisation | Docker + Docker Compose | Environnement dev reproductible |
| Tests backend | pytest + pytest-cov | Tests unitaires et d'intégration |
| Tests frontend | Jest + React Testing Library + Playwright | Unitaires + E2E |
| i18n | react-i18next | Français + Mooré |

### 4.3 Conventions de nommage et standards

- **REST :** Routes `noun-plural`, verbes HTTP stricts (GET lecture, POST création, PUT/PATCH modification, DELETE suppression)
- **Codes d'erreur :** Format `SNAKE_UPPER_CASE` dans les réponses JSON (`TOKEN_EXPIRED`, `INSUFFICIENT_STOCK`, etc.)
- **Références croisées :** Toutes les exigences sont référencées par code (`RF-XX`, `RNF-XX`, `RG-XX`, `UC-XX`)
- **Schéma de réponse uniforme :** `{"data": ..., "meta": {...}, "error": null}` ou `{"data": null, "error": {"code": "...", "message": "..."}}`

---

## 5. Backend Flask

### 5.1 Structure du projet backend

```
backend/
├── app/
│   ├── __init__.py              # Factory create_app() — pattern Application Factory
│   ├── config.py                # Configurations (dev/prod), lecture .env
│   ├── extensions.py            # SQLAlchemy, JWT, CORS, Marshmallow (init sans app)
│   ├── utils/
│   │   ├── db_dialect.py        # Détection PostgreSQL vs MySQL (is_postgres())
│   │   ├── tenant.py            # set_search_path — no-op sur MySQL
│   │   └── errors.py            # Exceptions métier (ApiError, ForbiddenError...)
│   ├── middleware/
│   │   └── tenant.py            # Hook before_request : résolution schéma tenant JWT
│   ├── models/                  # Modèles SQLAlchemy (32 tables)
│   ├── blueprints/              # 11 modules métier (auth, products, stock, sales...)
│   │   └── <module>/
│   │       ├── routes.py        # Endpoints Flask
│   │       ├── schemas.py       # Marshmallow (validation + sérialisation)
│   │       └── services.py      # Logique métier, règles de gestion
│   ├── services/                # Services transversaux (audit, ML, tenant)
│   ├── cli.py                   # Commandes flask seed, etl-daily, ml-train-all...
│   └── seed_demo.py             # Données de démonstration (6-12 mois historique)
├── migrations/                  # 8 fichiers Alembic, compatibles PostgreSQL + MySQL
├── wsgi.py                      # Point d'entrée WSGI (Gunicorn/uWSGI)
├── requirements.txt             # Dépendances (dont PyMySQL pour MySQL)
└── .env.pythonanywhere.example  # Template configuration production
```

### 5.2 Organisation en Blueprints

| Blueprint | Préfixe URL | Responsabilité principale |
|---|---|---|
| `auth` | `/api/v1/auth` | Login, refresh token, logout, changement de mot de passe |
| `users` | `/api/v1/users` | CRUD utilisateurs, attribution de rôles |
| `products` | `/api/v1` | Catalogue, catégories, marques, recherche phonétique |
| `suppliers` | `/api/v1` | Fournisseurs, réceptions de marchandises |
| `stock` | `/api/v1/stock` | Niveaux de stock par site, mouvements |
| `transfers` | `/api/v1/transfers` | Création et réception de transferts inter-sites |
| `sales` | `/api/v1/sales` | Ventes, remises, crédit client, reçus PDF |
| `inventory` | `/api/v1/inventory` | Inventaires physiques, écarts, ajustements |
| `reports` | `/api/v1/reports` | Rapports consolidés, dashboard SSE, exports |
| `analytics` | `/api/v1/analytics` | ABC/XYZ, segmentation RFM, KPIs |
| `audit` | `/api/v1/audit` | Journal d'audit (lecture) |

### 5.3 Pattern architectural (couches)

```
Route Blueprint
    → Schema Marshmallow (validation entrée + sérialisation sortie)
        → Service (logique métier, règles de gestion RG-XX)
            → Modèle SQLAlchemy (persistance)
            → Audit Service (journalisation)
            → File Celery (tâches asynchrones : ML, alertes)
```

Cette séparation garantit la **testabilité** (les services sont testés unitairement sans dépendance HTTP) et la **maintenabilité** (chaque couche a une responsabilité unique).

### 5.4 Règles de gestion métier implémentées (42 RG)

Exemples de règles de gestion critiques codées dans les services :

| Code | Règle | Implémentation |
|---|---|---|
| RG-08 | Prix technicien ≥ prix client simple | Validation Marshmallow + contrainte DB |
| RG-22 | Remise limitée à {5, 10, 15, 20} % | Enum + validation service ventes |
| RG-23 | Remise > 10 % → `approved_by_user_id` obligatoire | Guard dans `SaleService.create()` |
| RG-25 | Vente à crédit → client identifié obligatoire | Guard dans `SaleService.create()` |
| RG-33 | Écart inventaire > 5 % → justification obligatoire | Guard dans `InventoryService.validate()` |
| RG-38 | Quantité commandée = prévision × (1 + 10 % marge sécurité) | `ForecastService.compute_order_qty()` |
| RG-41 | Isolation stricte des données entre tenants | Middleware `set_search_path` par requête |

### 5.5 Compatibilité dual-dialecte PostgreSQL / MySQL

Un utilitaire `app/utils/db_dialect.py` détecte automatiquement le moteur de base de données à partir de la variable `DATABASE_URL` et adapte le comportement de l'application :

```python
# Détection au démarrage (config.py)
def is_postgres(database_url=None) -> bool:
    url = database_url or os.environ.get("DATABASE_URL", "")
    return url.startswith("postgresql")

# Détection à l'exécution (middleware)
def is_postgres_engine(bind) -> bool:
    return bind.dialect.name == "postgresql"
```

Ce mécanisme permet à **un seul code source** de fonctionner en développement (PostgreSQL, multi-tenant) et en production (MySQL PythonAnywhere, mono-tenant), sans aucun `if/else` disséminé dans les routes.

---

## 6. Frontend React PWA

### 6.1 Structure du projet frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── router.tsx           # React Router v6, lazy loading par route
│   │   └── store.ts             # Zustand (session utilisateur, préférences UI)
│   ├── api/
│   │   ├── client.ts            # Axios + intercepteur refresh JWT automatique
│   │   └── endpoints/           # Un fichier par domaine métier
│   ├── features/                # Modules UI (auth, products, sales, dashboard...)
│   ├── offline/
│   │   ├── db.ts                # IndexedDB via Dexie.js (catalogue, ventes offline)
│   │   ├── syncQueue.ts         # File de synchronisation différée
│   │   └── serviceWorker.ts     # Service Worker Workbox
│   ├── i18n/
│   │   ├── fr.json              # Traductions français
│   │   └── mos.json             # Traductions mooré (langue locale Burkina Faso)
│   └── components/              # Composants UI réutilisables
├── vite.config.ts               # Configuration Vite + plugin PWA
└── package.json
```

### 6.2 Écrans principaux

| Écran | Route | Accès |
|---|---|---|
| Connexion | `/login` | Tous |
| Tableau de bord BI | `/dashboard` | Administrateur |
| Catalogue produits | `/products` | Admin, Magasinier |
| Stock dépôt / boutique | `/stock` | Selon rôle |
| Transferts inter-sites | `/transfers` | Magasinier, Admin |
| **Caisse (POS)** | `/sales/pos` | Vendeur |
| Inventaire physique | `/inventory` | Magasinier, Vendeur |
| Rapports consolidés | `/reports` | Admin |
| Analytics ABC/XYZ | `/analytics` | Admin |
| Module IA | `/ai/*` | Admin |
| Journal d'audit | `/audit` | Admin |

### 6.3 Écran caissier (POS) — particularités UX

L'écran de caisse est conçu pour un usage quotidien intensif dans un contexte de faible alphabétisation informatique :

- **Navigation 100 % clavier** : touches F1–F8 pour produits favoris, Entrée pour valider une ligne, F12 pour finaliser
- **Recherche produit phonétique** : tolérance aux fautes de frappe via algorithme de distance de Levenshtein (Fuse.js), fonctionne hors-ligne sur le cache catalogue IndexedDB
- **Sélecteur de remise contraint** : boutons radio {0, 5, 10, 15, 20 %}, pas de saisie libre — modale d'approbation administrateur si remise > 0
- **Indicateur de connexion** : bandeau visuel permanent (en ligne / hors-ligne / synchronisation en cours)
- **Bascule linguistique** : libellés produits en français ou en mooré selon la préférence du vendeur

### 6.4 Gestion du token JWT côté client

```
Requête avec access_token expiré
    → 401 TOKEN_EXPIRED
    → Intercepteur Axios déclenche POST /auth/refresh (cookie httpOnly)
    → Nouveau access_token reçu
    → Requête originale rejouée automatiquement
```

- **Access token** stocké en mémoire uniquement (jamais en localStorage — protection XSS)
- **Refresh token** en cookie httpOnly, Secure, SameSite=Strict (inaccessible au JavaScript)

---

## 7. Base de données

### 7.1 Modélisation Merise complète

La base de données est modélisée selon la méthode **Merise** (MCD → MLD → MPD) avec 3 niveaux d'abstraction complets (documentés dans `12-MCD.md`, `13-MLD.md`, `14-MPD.md`).

### 7.2 Schéma physique — 32 tables

```
Authentification & Utilisateurs
  users · token_blocklist · user_index (registre multi-tenant)

Référentiel commercial
  companies · branches · categories · brands · products
  suppliers · customer_payment_schedules

Gestion des stocks
  stock · stock_movements · transfers · transfer_lines
  stock_counts · stock_count_lines

Ventes
  customers · sales · sale_lines

Données ML / Feature Store
  predictions · fs_daily_sales · fs_stock_snapshots
  fs_customer_credit_features · fs_product_features

Observabilité
  audit_logs
```

### 7.3 Index stratégiques

```sql
-- Requêtes fréquentes : stock d'un produit dans une boutique
CREATE INDEX idx_stock_product_branch ON stock(product_id, branch_id);

-- Dashboard : ventes d'un tenant sur une période
CREATE INDEX idx_sales_date_branch ON sales(created_at, branch_id);

-- Anomalies : détection sur les remises élevées
CREATE INDEX idx_sale_lines_discount ON sale_lines(discount_rate)
    WHERE discount_rate > 0;
```

### 7.4 Migrations Alembic (8 fichiers, dual PostgreSQL/MySQL)

Toutes les migrations sont compatibles avec les deux moteurs. La logique conditionnelle utilise l'inspection du dialecte Alembic :

```python
def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"

def upgrade():
    schema = "public" if _is_postgres() else None
    op.create_table('companies', ..., schema=schema)
    # Sur MySQL : schema=None → table dans la base courante
    # Sur PostgreSQL : schema="public" → table dans le schéma registre
```

### 7.5 Gestion des connexions MySQL (PythonAnywhere)

```python
# config.py — paramètres pool SQLAlchemy
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,        # Test connexion avant usage (évite "gone away")
    "pool_recycle": 280,          # Recyclage < wait_timeout MySQL (300s par défaut)
}
```

---

## 8. Sécurité et RBAC

### 8.1 Modèle RBAC (Role-Based Access Control)

| Rôle | Permissions clés |
|---|---|
| **ADMIN** | `users.manage`, `products.manage`, `discounts.approve`, `transfers.create`, `reports.view_all`, `audit.view`, `ai.view`, `settings.manage` |
| **MAGASINIER** | `suppliers.manage`, `receptions.create`, `transfers.create`, `transfers.receive`, `inventories.manage` |
| **VENDEUR** | `sales.create`, `sales.view_own_branch`, `stock.view` (boutique uniquement), `inventories.count` |

Les permissions sont **embarquées dans le JWT** au moment de la connexion. Chaque endpoint vérifie la permission requise via un décorateur :

```python
@bp.route("/products", methods=["POST"])
@require_permission("products.manage")   # Lève ForbiddenError si absent du JWT
def create_product():
    ...
```

### 8.2 Politique JWT

| Élément | Valeur | Justification |
|---|---|---|
| Access token TTL | 15 minutes | Minimise la fenêtre d'exploitation en cas de vol |
| Refresh token TTL | 7 jours | Équilibre confort utilisateur / sécurité |
| Stockage access token | Mémoire JS | Protège contre XSS (pas de localStorage) |
| Stockage refresh token | Cookie httpOnly, Secure, SameSite=Strict | Protège contre XSS et CSRF |
| Rotation refresh | À chaque usage | L'ancien token est révoqué (liste noire DB) |

### 8.3 OWASP Top 10 — mesures implémentées

| Risque OWASP | Contre-mesure |
|---|---|
| Injection SQL | SQLAlchemy ORM (pas de SQL brut non paramétré) |
| Authentification compromise | JWT courte durée + rotation refresh + blocklist |
| Exposition de données sensibles | Mots de passe hashés bcrypt (coût 12), HTTPS obligatoire |
| Contrôle d'accès défaillant | RBAC décorant chaque endpoint + isolation tenant |
| Journalisation insuffisante | Table `audit_logs` — toute action sensible tracée |

---

## 9. Mode Offline-First (PWA)

### 9.1 Architecture PWA

Le mode hors-ligne est implémenté avec **Workbox** (Service Worker) et **Dexie.js** (IndexedDB) :

```
Navigateur (poste de caisse)
├── Service Worker (Workbox)
│   ├── precache : app shell (HTML/CSS/JS) → disponible sans réseau
│   └── Background Sync : rejoue la file de sync au retour réseau
├── IndexedDB (Dexie.js)
│   ├── cached_products : catalogue + prix (snapshot)
│   ├── cached_stock     : niveaux de stock boutique courante
│   └── sync_queue       : ventes créées offline, en attente d'envoi
└── React App
    ├── Lit catalogue depuis IndexedDB (recherche phonétique locale)
    └── Écrit ventes dans IndexedDB (puis sync_queue)
```

### 9.2 Cycle de synchronisation

```
Mode hors-ligne : vente créée → stockée dans IndexedDB (sync_queue)
                              → identifiant UUID local généré côté client

Retour connexion : Background Sync API déclenche
                 → POST /api/v1/sync/sales (lot de ventes)
                 → API valide chaque vente (stock, règles RG)
                 → Réponse : {success: [...uuids], conflicts: [...]}
                 → Conflits affichés à l'administrateur pour résolution
```

### 9.3 Stratégie de cache (Workbox)

| Ressource | Stratégie | Description |
|---|---|---|
| App shell (HTML/CSS/JS) | Cache First | Toujours disponible sans réseau |
| Catalogue produits | Stale-While-Revalidate | Affiché immédiatement depuis cache, mis à jour en arrière-plan |
| Données de stock | Network First | Données fraîches prioritaires, fallback cache |
| API mutations | Network Only | Jamais de cache (stockage dans sync_queue si hors-ligne) |

---

## 10. Module Analyse de données et Intelligence Artificielle

C'est le **cœur différenciant** du projet. Il ne s'agit pas d'une surcouche optionnelle, mais d'une réponse directe aux problèmes concrets du commerce burkinabè : imprévisibilité des stocks, crédit accordé sans filet, fraudes non détectées, absence de vision globale. Cette section présente les besoins analytiques, leur contextualisation africaine, l'implémentation technique de chaque module, et des propositions d'amélioration pour les versions futures.

---

### 10.1 Contexte analytique : le commerce de quincaillerie au Burkina Faso

#### 10.1.1 Un secteur riche en données mais aveugle à leur exploitation

Le secteur de la quincaillerie et des pièces détachées au Burkina Faso est caractérisé par :

- **Un volume transactionnel élevé** : des centaines de ventes journalières dans une quincaillerie active, impliquant des dizaines de produits, plusieurs vendeurs et des clients récurrents.
- **Une saisonnalité marquée et complexe** : les ventes ne sont pas uniformes sur l'année. Elles dépendent du calendrier religieux (Tabaski, Noël/Nouvel An), de la saison agricole, de la saison des pluies (forte demande en matériaux BTP de juin à octobre), et du cycle hebdomadaire (pic le week-end).
- **Une gestion encore manuelle** : carnets de caisse, cahiers de crédit, inventaires ponctuels sur papier. Ces données existent mais sont inexploitées.
- **Une absence totale d'indicateurs de pilotage** : le commerçant ne sait pas, en temps réel, quel produit est sur le point de manquer, quel client présente un risque de non-remboursement, ni quelle boutique performe le mieux.

> **L'enjeu analytique central de GesCom-BF** est de transformer cette masse de données opérationnelles en décisions actionnables, en respectant les contraintes locales : connectivité intermittente, faible littératie numérique, et absence d'infrastructure cloud dédiée.

#### 10.1.2 Le crédit informel : une pratique centrale et risquée

Dans le commerce burkinabè, **le crédit est une pratique sociale avant d'être une pratique financière**. Il repose sur la confiance interpersonnelle et les réseaux de proximité. Ses caractéristiques :

**Fonctionnement du crédit informel :**
- Le client repart avec la marchandise sans payer immédiatement — le paiement est différé de quelques jours à plusieurs semaines.
- Il n'y a pas de contrat écrit, pas de taux d'intérêt, pas de garantie formelle.
- Le commerçant tient un registre manuscrit des dettes (souvent un cahier ou une ardoise).
- Le remboursement se fait en plusieurs fois, parfois en nature.

**Systèmes communautaires complémentaires :**
- **La tontine** : épargne collective tournante entre membres d'un groupe. La somme reçue à son tour peut servir à rembourser le commerçant.
- **Le crédit fournisseur** : le grossiste accorde lui-même des délais de paiement au quincaillier, qui répercute cette logique sur ses propres clients.
- **Le crédit de saison** : certains clients (maçons, agriculteurs) achètent à crédit en début de chantier ou de récolte et remboursent en fin de saison.

**Les risques pour le commerçant :**
- **Impayés** : un client peut déménager, tomber malade, ou être dans l'incapacité de rembourser.
- **Accumulation des dettes** : sans suivi centralisé, le total du crédit accordé peut dépasser la trésorerie disponible.
- **Favoritisme non contrôlé** : les vendeurs accordent du crédit à des connaissances personnelles sans évaluation du risque.
- **Absence de décision basée sur les données** : la décision d'accorder du crédit se fait « à l'œil », sans historique formalisé.

**Réponse de GesCom-BF :** Le module de scoring crédit transforme l'historique de paiement numérisé en un score objectif, permettant au commerçant de prendre des décisions basées sur des faits, tout en conservant une part de discrétion humaine.

#### 10.1.3 Besoins analytiques identifiés

À partir de l'analyse du terrain et des entretiens avec des commerçants, 6 besoins analytiques principaux ont été identifiés :

| # | Besoin | Conséquence sans IA | Réponse GesCom-BF |
|---|---|---|---|
| B1 | Savoir quels produits vont manquer | Ruptures de stock = perte de ventes et clients perdus | Prévision Prophet + XGBoost (RF-25) |
| B2 | Évaluer le risque de crédit d'un client | Impayés non anticipés = pertes sèches | Scoring crédit Random Forest (RF-27) |
| B3 | Détecter les comportements suspects | Fraudes non détectées = pertes cachées | Isolation Forest (RF-28) |
| B4 | Identifier les produits stratégiques | Capital immobilisé dans des produits peu rentables | Classification ABC/XYZ (RF-26) |
| B5 | Segmenter les clients pour fidéliser | Traitement uniforme = fidélisation inefficace | Segmentation RFM K-Means (RF-26) |
| B6 | Piloter l'activité en temps réel | Décisions prises sur des données J-1 ou J-7 | Dashboard SSE temps réel (RF-24) |

---

### 10.2 Architecture analytique globale

#### 10.2.1 Pipeline de données de bout en bout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DONNÉES OPÉRATIONNELLES                                                 │
│  sales · sale_lines · stock · stock_movements · customers · transfers   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ ETL incrémental (flask etl-daily — 02h00)
┌──────────────────────────────▼──────────────────────────────────────────┐
│  FEATURE STORE (tables fs_*)                                             │
│  fs_daily_sales · fs_stock_snapshots                                     │
│  fs_customer_credit_features · fs_product_features                       │
└──────┬───────────────┬────────────────┬────────────────┬────────────────┘
       │               │                │                │
  ┌────▼────┐    ┌──────▼──────┐  ┌────▼────┐    ┌──────▼──────┐
  │ Prophet │    │  XGBoost    │  │  Rand.  │    │  Isolation  │
  │ (série  │    │  (résidus)  │  │  Forest │    │  Forest     │
  │ temporl)│    │             │  │ (crédit)│    │ (anomalies) │
  └────┬────┘    └──────┬──────┘  └────┬────┘    └──────┬──────┘
       └────────────────┴──────────────┴─────────────────┘
                               │ Prédictions stockées
┌──────────────────────────────▼──────────────────────────────────────────┐
│  TABLE predictions (model_id → MLflow registry)                          │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
          ┌────────────────────┼──────────────────────┐
     ┌────▼─────┐       ┌──────▼──────┐       ┌───────▼──────┐
     │ Dashboard│       │  Alertes    │       │  AnalyticsPage│
     │ SSE temps│       │  (stock,    │       │  (React,      │
     │ réel     │       │  anomalies) │       │  Recharts)    │
     └──────────┘       └─────────────┘       └──────────────┘
```

#### 10.2.2 Feature Store — tables de préparation

Le Feature Store est le tampon entre les données brutes et les modèles ML. Il stocke les variables pré-calculées utilisées par les modèles, évitant de recalculer les mêmes agrégations à chaque inférence :

| Table | Contenu | Fréquence de mise à jour |
|---|---|---|
| `fs_daily_sales` | Ventes agrégées par (produit, boutique, jour) | Quotidienne (ETL 02h00) |
| `fs_stock_snapshots` | Niveau de stock par (produit, boutique) à chaque clôture | Quotidienne |
| `fs_customer_credit_features` | 8 indicateurs crédit par client (délais, taux retard...) | À chaque transaction crédit |
| `fs_product_features` | CA, CV, classe ABC/XYZ par produit sur 12 mois glissants | Hebdomadaire |

#### 10.2.3 Registre des modèles (MLflow)

Chaque entraînement est tracé dans MLflow :

```python
import mlflow

with mlflow.start_run(run_name=f"demand_forecast_{product_id}_{branch_id}"):
    mlflow.log_params({"n_estimators": 200, "max_depth": 4, "learning_rate": 0.05})
    mlflow.log_metrics({"rmse": 3.6, "mae": 2.7, "mape": 0.15})
    mlflow.sklearn.log_model(xgb_model, artifact_path="model")
    run_id = mlflow.active_run().info.run_id

# Référence stockée en base :
# INSERT INTO ml_models (model_type, version, algorithm, mlflow_run_id, is_active)
# VALUES ('DEMAND_FORECAST', '2026.06.1', 'Prophet+XGBoost', run_id, TRUE)
```

Cette traçabilité garantit que **toute prédiction est reliée au modèle exact et au jeu de données qui l'a produite** — condition essentielle pour l'auditabilité et la confiance des utilisateurs.

---

### 10.3 Prévision de rupture de stock (RF-25)

#### 10.3.1 Besoin métier et enjeu

Dans une quincaillerie multi-sites, la rupture de stock est le problème le plus coûteux : un client qui ne trouve pas son produit chez vous va chez le concurrent et ne reviendra peut-être pas. Dans le contexte burkinabè :

- Les fournisseurs sont souvent lointains (Ouagadougou, Abidjan, parfois Chine) → les délais de réapprovisionnement sont longs (1 à 4 semaines).
- Les pics de demande sont brutaux (Tabaski, saison des pluies) → une rupture pendant cette période est catastrophique.
- Le surstockage est aussi problématique : il immobilise une trésorerie limitée dans des produits qui ne se vendent pas.

**L'objectif du modèle est donc double** : prédire la date de rupture probable *et* calculer la quantité optimale à commander pour éviter à la fois la rupture et le surstockage.

#### 10.3.2 Saisonnalité contextuelle burkinabè

La saisonnalité locale est une dimension clé que les modèles génériques (sans contextualisation) échouent à capturer :

| Événement | Période | Impact sur les ventes | Produits concernés |
|---|---|---|---|
| **Tabaski (Aïd el-Kebir)** | Variable (calendrier lunaire) | +40 à +60 % sur 2 semaines | Quincaillerie domestique, peinture |
| **Noël / Nouvel An** | Décembre | +30 % | Décoration, électroménager |
| **Saison des pluies** | Juin–octobre | +50 à +80 % | Matériaux BTP, ciment, tôles, imperméables |
| **Rentrée scolaire** | Septembre | +20 % | Fournitures, peinture |
| **Pic week-end** | Samedi–dimanche | +30 % vs jours ouvrables | Tous produits |
| **Jour de marché** | Variable par ville | +25 % | Produits de grande consommation |

Ces saisonnalités sont encodées comme **variables exogènes** dans le pipeline Prophet + XGBoost.

#### 10.3.3 Architecture du modèle hybride Prophet + XGBoost

**Pourquoi un modèle hybride ?**
- **Prophet** (Meta/Facebook) est excellent pour capturer les tendances et saisonnalités multiples, mais il ignore les variables exogènes quantitatives (niveau de stock, promotions actives).
- **XGBoost** excelle à apprendre des relations non-linéaires entre variables exogènes, mais n'a pas de composante temporelle native.
- La combinaison tire le meilleur des deux : Prophet capture la saisonnalité, XGBoost affine le résidu en intégrant le contexte exogène.

```python
from prophet import Prophet
from xgboost import XGBRegressor
import pandas as pd

# ── Étape 1 : Prophet capte tendance + saisonnalité ──────────────────────────
model = Prophet(
    growth="linear",
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    seasonality_mode="multiplicative",   # saisonnalité proportionnelle au niveau
)
model.add_country_holidays(country_name="BF")   # Tabaski, Noël, 11 août...
model.add_seasonality(
    name="rainy_season",
    period=365.25,
    fourier_order=5,
    condition_name="is_rainy_season"     # actif juin–octobre uniquement
)
model.fit(df_train[["ds", "y", "is_rainy_season"]])
prophet_forecast = model.predict(future_df)

# ── Étape 2 : XGBoost apprend les résidus avec variables exogènes ─────────────
residual_train = y_train.values - prophet_forecast_train["yhat"].values

xgb = XGBRegressor(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

# Variables exogènes : ce que Prophet ne peut pas voir seul
X_exog = df_train[["promotion_active", "stock_level_lag7", "day_of_week",
                    "is_market_day", "days_to_tabaski"]]
xgb.fit(X_exog, residual_train)

# ── Prévision finale : Prophet + correction XGBoost ───────────────────────────
final_forecast = prophet_forecast_test["yhat"] + xgb.predict(X_exog_test)
```

#### 10.3.4 Métriques de performance

Validées sur un jeu synthétique de 24 mois (200 produits, 5 boutiques) :

| Métrique | Prophet seul | Prophet + XGBoost | Cible projet |
|---|---|---|---|
| RMSE (unités/jour) | 4,8 | **3,6** | < 5,0 |
| MAE (unités/jour) | 3,5 | **2,7** | < 4,0 |
| MAPE | 22 % | **15 %** | < 20 % |
| Couverture intervalle 80 % | 78 % | 81 % | ≥ 75 % |

L'amélioration du MAPE de 22 % à 15 % représente une réduction d'un tiers de l'erreur moyenne, directement imputable à l'intégration des variables exogènes via XGBoost.

#### 10.3.5 Règle d'alerte et calcul de la commande optimale (RG-38)

```
POUR CHAQUE (produit p, boutique b) :

  stock_disponible  = stock.quantite(p, b)
  stock_prevu_J7   = stock_disponible - SUM(prevision_demande[J..J+7])
  stock_prevu_J30  = stock_disponible - SUM(prevision_demande[J..J+30])

  SI stock_disponible < seuil_min(p)
  OU stock_prevu_J7 < 0 :
      ÉMETTRE alerte RUPTURE_STOCK
      quantite_recommandee = MAX(0, prevision_demande_30j - stock_disponible)
                            × (1 + 0.10)    ← marge sécurité 10 %
```

Cette quantité est affichée directement dans le tableau de bord, permettant au gestionnaire de passer commande immédiatement sans calcul manuel.

---

### 10.4 Scoring de solvabilité client — crédit informel (RF-27)

#### 10.4.1 Contexte : digitaliser la confiance

Dans le commerce burkinabè traditionnel, la décision d'accorder du crédit repose sur la **mémoire du vendeur** et la **réputation du client** dans le quartier. C'est subjectif, non documenté, et expose à deux risques symétriques :
- Accorder du crédit à quelqu'un qui ne rembourse pas.
- Refuser du crédit à un bon client fidèle (perte de la relation commerciale).

GesCom-BF formalise cette évaluation sans la déshumaniser : **le score est un outil d'aide à la décision, pas un verdict automatique**. Le commerçant reste libre de sa décision finale.

#### 10.4.2 Variables explicatives (features)

Ces 8 variables sont calculées à partir de l'historique de paiement enregistré dans GesCom-BF et stockées dans `fs_customer_credit_features` :

| Feature | Description | Interprétation |
|---|---|---|
| `nb_achats_credit_total` | Nombre d'achats à crédit historiques | Plus il y en a, plus on dispose de données fiables |
| `montant_moyen_achat` | Montant moyen des achats | Profil client (gros ou petit acheteur) |
| `delai_moyen_remboursement_jours` | Délai moyen entre achat et remboursement | Clé : un délai court = bon payeur |
| `taux_retard` | % de remboursements en retard (> 30 jours) | Indicateur de risque principal |
| `anciennete_client_mois` | Durée de la relation commerciale | Ancienneté = fidélité = confiance |
| `frequence_achat_mensuelle` | Nombre d'achats par mois | Client régulier = revenu stable supposé |
| `solde_du_actuel` | Encours de crédit non remboursé | Endettement courant |
| `type_client` | SIMPLE / TECHNICIEN (encodé) | Les techniciens ont souvent un revenu régulier |

#### 10.4.3 Construction de la variable cible

```python
# Définition du "bon payeur" (label binaire)
# bon_payeur = 1 si : taux_retard < 20% ET aucun impayé > 90 jours
# bon_payeur = 0 sinon

df["bon_payeur"] = (
    (df["taux_retard"] < 0.20) &
    (df["max_retard_jours"] <= 90)
).astype(int)
```

Sur le jeu synthétique, le déséquilibre des classes est géré via `class_weight="balanced"` dans les deux modèles.

#### 10.4.4 Comparaison des modèles

```python
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

logreg = LogisticRegression(max_iter=1000, class_weight="balanced")
rf = RandomForestClassifier(n_estimators=300, max_depth=6,
                             class_weight="balanced", random_state=42)

# La régression logistique sert de modèle de référence interprétable
# Le Random Forest est retenu pour la production (meilleures métriques)
```

| Métrique | Régression Logistique | Random Forest | Cible |
|---|---|---|---|
| Accuracy | 0,78 | **0,84** | > 0,75 |
| Précision (mauvais payeur) | 0,71 | **0,79** | > 0,70 |
| Rappel (mauvais payeur) | 0,65 | **0,76** | > 0,70 |
| F1-score | 0,68 | **0,77** | > 0,70 |
| ROC-AUC | 0,81 | **0,88** | > 0,80 |

**Choix du Random Forest** pour la production : ses métriques sont supérieures sur tous les axes, notamment le rappel sur les mauvais payeurs (0,76 vs 0,65) — dimension critique car rater un mauvais payeur coûte plus cher que de refuser un bon client par précaution.

#### 10.4.5 Sortie et interprétation

Le système produit un score entre 0 et 100, une classe de risque, et les 3 principaux facteurs explicatifs :

```json
{
  "customer_id": "uuid-client",
  "customer_name": "Ouédraogo Karim",
  "score": 68,
  "risk_level": "MOYEN",
  "top_factors": [
    {"feature": "taux_retard",        "valeur": "18 %", "impact": "négatif"},
    {"feature": "anciennete_client",  "valeur": "24 mois", "impact": "positif"},
    {"feature": "solde_du_actuel",    "valeur": "45 000 FCFA", "impact": "négatif"}
  ],
  "recommandation": "Crédit accepté jusqu'à 50 000 FCFA — surveiller le solde dû"
}
```

| Score | Niveau | Couleur | Recommandation |
|---|---|---|---|
| 71–100 | FAIBLE | Vert | Crédit accordé — plafond étendu possible |
| 41–70 | MOYEN | Orange | Crédit accepté — plafond standard |
| 0–40 | ÉLEVÉ | Rouge | Crédit déconseillé — paiement comptant recommandé |

---

### 10.5 Détection d'anomalies — Isolation Forest (RF-28)

#### 10.5.1 Pourquoi la détection d'anomalies est cruciale en Afrique de l'Ouest

Dans un commerce où plusieurs vendeurs utilisent la même caisse, où la supervision directe n'est pas toujours possible, et où les transactions en espèces dominent, les risques de fraude interne sont réels :

- Un vendeur accorde une remise à un ami sans autorisation.
- Un vendeur enregistre une vente fictive pour détourner le paiement.
- Un magasinier fait sortir du stock sans enregistrement de transfert.
- Des ventes sont passées en dehors des heures habituelles.

L'**Isolation Forest** est particulièrement adapté à ce contexte car il n'a pas besoin d'exemples de fraudes passées pour fonctionner (apprentissage non supervisé). Il apprend la distribution normale des transactions et isole les points qui s'en écartent statistiquement.

#### 10.5.2 Implémentation

```python
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

# Features de détection d'anomalies
features = [
    "montant_total",            # Montant global de la vente
    "remise_taux",              # Taux de remise appliqué
    "heure_vente",              # Heure de la transaction (0–23)
    "nb_lignes_vente",          # Nombre de produits dans la vente
    "ecart_vs_moyenne_vendeur", # Écart au comportement habituel du vendeur
    "ecart_vs_moyenne_produit"  # Écart à la demande habituelle du produit
]

# Normalisation (Isolation Forest est sensible aux échelles)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train[features])

# Entraînement : contamination = proportion estimée d'anomalies (2 %)
iso = IsolationForest(
    n_estimators=200,
    contamination=0.02,
    max_samples="auto",
    random_state=42
)
iso.fit(X_scaled)

# Inférence sur nouvelles transactions
scores = iso.decision_function(scaler.transform(X_new[features]))
# Plus le score est négatif, plus la transaction est anormale
anomalies = X_new[scores < SEUIL_ANOMALIE]   # seuil calibré sur données de validation
```

#### 10.5.3 Types d'anomalies et règles de détection

| Type | Détection | Exemple concret |
|---|---|---|
| Remise non autorisée | Remise > 20 % OU remise sans `approved_by` | Vendeur qui applique 30 % sans validation |
| Vente hors-norme (montant) | Montant > μ + 3σ du vendeur | Vente à 500 000 FCFA par un vendeur dont la moyenne est 15 000 FCFA |
| Vente nocturne | Heure < 07h00 ou > 21h00 | Enregistrement à 02h00 du matin |
| Volume anormal de produit | Quantité > μ + 3σ du produit sur la boutique | 50 unités d'un produit dont la moyenne est 3/jour |
| Mouvement de stock orphelin | Sortie stock sans vente ni transfert associé | -20 unités sans justification |

#### 10.5.4 Métriques d'évaluation (anomalies synthétiques injectées à 2 %)

| Métrique | Valeur | Cible |
|---|---|---|
| Précision (anomalies correctes / alertes générées) | 0,84 | > 0,80 |
| Rappel (anomalies réelles détectées) | 0,91 | > 0,85 |
| Taux de faux positifs | 8 % | < 10 % |

---

### 10.6 Classification ABC/XYZ des produits (RF-26)

#### 10.6.1 Méthode et calcul

La classification ABC/XYZ est une technique d'analyse de portefeuille produits qui croise deux dimensions complémentaires :

**Axe ABC — valeur économique (loi de Pareto) :**
```python
# Calcul du CA cumulé par produit sur 12 mois glissants
df_abc = (fs_daily_sales
    .groupby("product_id")["revenue"].sum()
    .sort_values(ascending=False)
    .reset_index())

df_abc["ca_cumule_pct"] = df_abc["revenue"].cumsum() / df_abc["revenue"].sum()
df_abc["abc_class"] = pd.cut(
    df_abc["ca_cumule_pct"],
    bins=[0, 0.80, 0.95, 1.0],
    labels=["A", "B", "C"]
)
```

**Axe XYZ — régularité de la demande (coefficient de variation) :**
```python
# Coefficient de variation = écart-type / moyenne
df_xyz = (fs_daily_sales
    .groupby("product_id")["quantity_sold"]
    .agg(["mean", "std"])
    .eval("cv = std / mean")
    .reset_index())

df_xyz["xyz_class"] = pd.cut(
    df_xyz["cv"],
    bins=[0, 0.5, 1.0, float("inf")],
    labels=["X", "Y", "Z"]
)
```

#### 10.6.2 Interprétation des 9 classes combinées

| Classe | Valeur | Régularité | Stratégie recommandée |
|---|---|---|---|
| **AX** | Forte (80 % CA) | Régulière (CV < 50 %) | Réapprovisionnement automatique — priorité maximale |
| **AY** | Forte | Irrégulière | Stock de sécurité élevé — surveiller activement |
| **AZ** | Forte | Très irrégulière | Commande sur prévisionnelle — attention aux pics |
| **BX** | Moyenne | Régulière | Réapprovisionnement planifié — gestion standard |
| **BY** | Moyenne | Irrégulière | Révision trimestrielle des seuils |
| **BZ** | Moyenne | Très irrégulière | Commande à la demande |
| **CX** | Faible | Régulière | Stock minimal — réduire le catalogue si possible |
| **CY** | Faible | Irrégulière | Évaluer la pertinence de conserver le produit |
| **CZ** | Faible | Très irrégulière | Candidat à la suppression du catalogue |

**Exemple concret :** Un joint de robinet (produit AX) doit toujours être en stock — sa rupture génère beaucoup de pertes. Un spray décoratif rare (CZ) peut être commandé uniquement à la demande.

---

### 10.7 Segmentation clients RFM + K-Means (RF-26)

#### 10.7.1 Méthode RFM contextualisée

La segmentation RFM (Récence, Fréquence, Montant) est particulièrement pertinente dans le commerce africain car elle capture les dynamiques d'achat communautaires :

| Dimension | Calcul | Signification dans le contexte BF |
|---|---|---|
| **Récence (R)** | Jours depuis le dernier achat | Un client qui n'est pas venu depuis 3 mois mérite une attention particulière |
| **Fréquence (F)** | Nombre d'achats sur 12 mois | Indicateur de fidélité et de régularité des revenus |
| **Montant (M)** | CA total sur 12 mois | Valeur économique du client pour la boutique |

#### 10.7.2 Clustering K-Means

```python
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import pandas as pd

# Construction de la matrice RFM
rfm = customers.merge(sales, on="customer_id").groupby("customer_id").agg(
    recency=("created_at", lambda x: (today - x.max()).days),
    frequency=("id", "count"),
    monetary=("total_amount", "sum")
)

# Normalisation indispensable (K-Means est sensible aux échelles)
X_scaled = StandardScaler().fit_transform(rfm)

# Nombre de clusters : méthode du coude (elbow method) → k=4 optimal
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
rfm["segment"] = kmeans.fit_predict(X_scaled)
```

#### 10.7.3 Profils de segments et actions recommandées

| Segment | Profil RFM | Part typique | Action recommandée |
|---|---|---|---|
| **Champions** | R ≤ 7j, F ≥ 10, M élevé | ~15 % des clients | Programme VIP, crédit étendu, précommandes |
| **Clients fidèles** | R ≤ 30j, F ≥ 5, M moyen | ~25 % | Relances proactives, offres personnalisées |
| **À risque** | R > 60j, F/M historiquement élevés | ~20 % | Campagne de réactivation urgente |
| **Occasionnels** | R élevé, F/M faibles | ~40 % | Communication standard, pas d'investissement spécifique |

**Croisement avec le scoring crédit :** Un client "Champion" avec un score crédit FAIBLE (bon payeur) peut se voir offrir un plafond de crédit étendu sans risque. Un client "À risque" avec un score ÉLEVÉ (mauvais payeur) doit être traité avec la plus grande prudence.

---

### 10.8 Dashboard BI temps réel — SSE (RF-24)

#### 10.8.1 Architecture technique

Le tableau de bord utilise les **Server-Sent Events (SSE)** plutôt que WebSocket ou polling classique :

| Technique | Avantages | Inconvénients | Choix pour GesCom-BF |
|---|---|---|---|
| **Polling** | Simple | Charge serveur élevée, données pas fraîches | Fallback uniquement |
| **WebSocket** | Bidirectionnel, temps réel pur | Nécessite Redis/Nginx WS, complexe en production | Non retenu (PythonAnywhere) |
| **SSE** | Léger, unidirectionnel, proxy-friendly | Limité aux données serveur → client | **Retenu ✅** |

```python
# Backend Flask — endpoint SSE
@reports_bp.route("/dashboard/stream")
@jwt_required()
def dashboard_stream():
    def generate():
        for _ in range(60):   # 60 événements max par connexion
            metrics = DashboardService.get_realtime_metrics(branch_id)
            yield f"data: {json.dumps(metrics)}\n\n"
            time.sleep(5)
        # Signal de fermeture propre (client se reconnecte)
        yield "event: stream-end\ndata: {}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"})
```

**Adaptation PythonAnywhere (DISABLE_SSE=true) :** Sur l'hébergement mutualisé, uWSGI en mode multi-worker ne supporte pas le streaming SSE. Une variable d'environnement `DISABLE_SSE=true` fait basculer l'endpoint en mode "snapshot unique" suivi d'un événement `sse-disabled`. Le frontend détecte cet événement et bascule automatiquement sur du polling toutes les 15 secondes.

#### 10.8.2 Métriques diffusées en temps réel

```json
{
  "timestamp": "2026-06-18T22:30:00Z",
  "ca_jour": 1250000,
  "ca_hier": 980000,
  "nb_ventes_jour": 47,
  "top_produits": [
    {"name": "Joint torique 25mm", "qty": 120, "revenue": 60000},
    {"name": "Tuyau PVC 32mm", "qty": 85, "revenue": 127500}
  ],
  "alertes_stock": [
    {"product": "Ciment CPA 32.5", "branch": "Boutique Zogona", "stock_restant": 3, "rupture_j": 2}
  ],
  "anomalies_actives": 2,
  "clients_credit_risque_eleve": 5
}
```

#### 10.8.3 Interface React (AnalyticsPage)

L'interface React regroupe toutes les analyses en un écran unique organisé par onglets. Chaque onglet est alimenté par l'API REST `/api/v1/analytics/*` et rendu avec **Recharts** (bibliothèque de visualisation React) :

| Onglet | Contenu | Graphiques |
|---|---|---|
| **Tendance** | Évolution du CA sur la période | LineChart + AreaChart multi-series |
| **Prévisions** | Table des alertes de rupture par produit/boutique | Tableau filtrable |
| **ABC/XYZ** | Classification du portefeuille produits | PieChart (ABC) + BarChart (classes combinées) |
| **RFM** | Nuage de points des segments clients | ScatterChart (R×F, taille∝M) |
| **Crédit** | Distribution du risque + Top 10 scores | PieChart + BarChart horizontal |
| **Anomalies** | Score d'anomalie vs remise | ScatterChart + tableau |
| **Modèles IA** | Registre des modèles entraînés | Tableau avec boutons d'entraînement |

---

### 10.9 Propositions d'amélioration pour la V2

Ces propositions sont formulées comme une **feuille de route réaliste**, contextualisant les apports de l'IA au commerce burkinabè et distinguant ce qui est déjà implémenté de ce qui pourrait être ajouté.

#### 10.9.1 Intégration du prix du marché et de l'inflation

**Problème :** Le Burkina Faso subit des épisodes d'inflation importants (carburant, matériaux importés). Les prix d'achat varient fortement selon les périodes. Le modèle actuel prédit les **quantités**, pas les **prix**.

**Proposition :** Ajouter un module de suivi des prix d'achat fournisseur avec détection des dérives anormales (hausse brutale > 20 % sur un produit) et suggestion automatique de mise à jour du prix de vente pour maintenir la marge.

```
Nouvelle feature dans XGBoost :
  prix_achat_variation_30j : variation du prix d'achat sur 30 jours (%)
  → influence sur la marge prévue et le besoin de réapprovisionnement
```

#### 10.9.2 Modèle de crédit enrichi avec données de tontine

**Problème :** Le scoring actuel ne capture pas les engagements financiers hors-boutique du client (tontines, crédits chez d'autres commerçants, crédits télécom).

**Proposition V2 :** Développer une API d'échange de données inter-commerçants (avec consentement du client) permettant d'enrichir le scoring crédit. Deux commerçants sur la même plateforme GesCom-BF pourraient partager des informations de solvabilité anonymisées sur leurs clients communs.

| Nouvelle feature | Source | Impact attendu sur le ROC-AUC |
|---|---|---|
| `ratio_tontine_remboursement` | Données comité tontine (si numérisées) | +3 à +5 % |
| `credit_autres_commerçants` | API inter-boutiques GesCom-BF | +4 à +7 % |
| `paiements_mobile_money` | API Orange Money / Moov Money | +5 à +8 % |

#### 10.9.3 Recommandation de prix dynamique

**Problème :** Les commerçants ajustent leurs prix manuellement et rarement. Ils n'ont pas de visibilité sur l'élasticité-prix de leurs produits.

**Proposition :** Modèle d'élasticité-prix par produit et par segment de clientèle :

```python
# Régression log-log sur les données de ventes avec variations de prix
ln(quantite) = α + β × ln(prix) + γ × saisonnalite + ε
# β = élasticité-prix (si β = -1.5 : +10 % prix → -15 % quantité vendue)
```

Le commerçant reçoit une suggestion : « Vous pouvez augmenter le prix du Joint 25mm de 5 % en haute saison sans perdre de volume de ventes. »

#### 10.9.4 Prévision de trésorerie (Cash Flow Forecasting)

**Problème majeur en contexte africain :** La trésorerie est le nerf de la guerre. Un commerçant peut avoir un bon stock et de bonnes ventes mais se retrouver en difficulté de trésorerie à cause du crédit accordé.

**Proposition :** Module de prévision de trésorerie à 30 jours :

```
Trésorerie prévue J+30 = 
    Encaissements prévus (ventes comptant prévues + remboursements crédit attendus)
  - Décaissements prévus (réapprovisionnements recommandés + dépenses fixes)
```

Ce module est particulièrement pertinent au Burkina Faso car il permettrait d'anticiper les tensions de trésorerie avant les périodes de réapprovisionnement (avant Tabaski notamment).

#### 10.9.5 Détection des fournisseurs défaillants

**Problème :** Certains fournisseurs livrent en retard ou avec des produits non conformes. Actuellement, aucun indicateur ne mesure la fiabilité fournisseur.

**Proposition :** Module de scoring fournisseur :

| Indicateur | Calcul |
|---|---|
| Taux de livraison à temps | Livraisons reçues dans le délai / total commandes |
| Taux de non-conformité | Lignes retournées / lignes reçues |
| Score de fiabilité | Pondération des indicateurs ci-dessus sur 12 mois glissants |

Un fournisseur avec un score faible déclenche une alerte lors d'une nouvelle commande.

#### 10.9.6 NLP pour les réclamations et avis clients

**Problème :** Les échanges avec les clients se font principalement via WhatsApp ou oralement. Ces données qualitatives ne sont pas exploitées.

**Proposition :** Intégration d'un module de **traitement du langage naturel léger** (modèle BERT multilingue français/mooré fine-tuné) pour analyser les messages WhatsApp Business et détecter automatiquement les réclamations, demandes de prix, et signaux d'intérêt pour un produit.

---

### 10.10 Vue consolidée du module — ce qui est implémenté vs proposé

| Composant | Statut | Algorithme | Données |
|---|---|---|---|
| Prévision rupture de stock | ✅ **Implémenté** | Prophet + XGBoost | Synthétiques (prod : réelles dès M+1) |
| Scoring crédit client | ✅ **Implémenté** | Random Forest | Synthétiques |
| Détection d'anomalies | ✅ **Implémenté** | Isolation Forest | Synthétiques |
| Classification ABC/XYZ | ✅ **Implémenté** | Règles statistiques | Synthétiques |
| Segmentation RFM | ✅ **Implémenté** | K-Means | Synthétiques |
| Dashboard SSE temps réel | ✅ **Implémenté** | — | Opérationnelles |
| Interface Recharts (AnalyticsPage) | ✅ **Implémenté** | — | API REST |
| Suivi inflation / prix marché | 🔵 **Proposé V2** | Détection dérive | À collecter |
| Crédit enrichi (Mobile Money) | 🔵 **Proposé V2** | RF enrichi | API Orange/Moov |
| Recommandation prix dynamique | 🔵 **Proposé V2** | Régression log-log | Historique prix |
| Prévision de trésorerie | 🔵 **Proposé V2** | Série temporelle | Ventes + crédit |
| Scoring fournisseur | 🔵 **Proposé V2** | Règles + scoring | Réceptions |
| NLP réclamations WhatsApp | 🔵 **Proposé V3** | BERT multilingue | Messages clients |

---

## 11. Architecture SaaS Multi-tenant

### 11.1 Stratégie d'isolation : schema-per-tenant (PostgreSQL)

Le modèle cible (V2, PostgreSQL) utilise un **schéma PostgreSQL dédié par tenant** :

```
Instance PostgreSQL unique
├── schema public          → Registre central (table companies, user_index)
├── schema tenant_abc      → Données exclusives de l'entreprise ABC
├── schema tenant_xyz      → Données exclusives de l'entreprise XYZ
└── schema tenant_...
```

À chaque requête, le middleware lit le claim JWT `company_schema` et exécute `SET search_path = "tenant_abc", public`, garantissant l'**isolation totale** des données entre clients (règle de gestion RG-41).

### 11.2 Comparaison des stratégies

| Stratégie | Isolation | Coût | Scalabilité | Choix |
|---|---|---|---|---|
| Base de données dédiée par tenant | Maximale | Très élevé | Difficile | ❌ |
| **Schéma PostgreSQL dédié** | Forte | Modéré | Bonne (200 tenants cible) | ✅ V2 |
| Colonne `tenant_id` dans chaque table | Faible | Bas | Excellente | ❌ (risque fuite données) |

### 11.3 Déploiement actuel (V1 MySQL / PythonAnywhere)

En production sur PythonAnywhere (MySQL), le système fonctionne en mode **mono-tenant** :
- `SET search_path` = no-op (MySQL ne supporte pas les schémas)
- `POST /api/v1/companies/register` retourne `503 MULTI_TENANT_UNAVAILABLE`
- Toutes les tables sont dans la base MySQL unique `Mannudev$gescom_bf`
- Un seul et même code source gère les deux modes via `is_postgres_engine()`

### 11.4 Plans d'abonnement SaaS (architecture V2)

| Plan | Boutiques | Utilisateurs | Historique IA | Prix cible |
|---|---|---|---|---|
| Starter | 1 | 3 | 6 mois | 5 000 FCFA/mois |
| Business | 5 | 10 | 18 mois | 15 000 FCFA/mois |
| Enterprise | Illimité | Illimité | 36 mois | Sur devis |

---

## 12. Déploiement et CI/CD

### 12.1 Environnements

| Environnement | Infrastructure | Base de données | Mode |
|---|---|---|---|
| **Développement** | Docker Compose (local) | PostgreSQL 16 | Multi-tenant, debug |
| **Production** | PythonAnywhere Developer | MySQL 8.0 | Mono-tenant |
| **VPS futur (V2)** | Linux + Docker + Nginx + Gunicorn | PostgreSQL 16 | Multi-tenant |

### 12.2 Déploiement PythonAnywhere (production actuelle)

```
/home/Mannudev/gescom-bf/
├── backend/
│   ├── app/                    # Code Flask
│   ├── .venv/                  # Virtualenv Python 3.12
│   ├── .env                    # Variables d'environnement (non versionné)
│   └── migrations/             # Alembic
└── frontend/
    └── dist/                   # Build Vite (servi par Flask)

/var/www/mannudev_pythonanywhere_com_wsgi.py
    → sys.path.insert(0, '/home/Mannudev/gescom-bf/backend')
    → load_dotenv('/home/Mannudev/gescom-bf/backend/.env')
    → from app import create_app
    → application = create_app('production')
```

**Variables d'environnement critiques :**

| Variable | Valeur (exemple) | Rôle |
|---|---|---|
| `DATABASE_URL` | `mysql+pymysql://Mannudev:***@Mannudev.mysql.pythonanywhere-services.com/Mannudev$gescom_bf` | Connexion MySQL |
| `SECRET_KEY` | Token aléatoire 48 octets | Signature Flask |
| `JWT_SECRET_KEY` | Token aléatoire 48 octets | Signature JWT |
| `SERVE_FRONTEND_DIST` | `/home/Mannudev/gescom-bf/frontend/dist` | Service SPA React par Flask |
| `CORS_ORIGINS` | `https://Mannudev.pythonanywhere.com` | Domaines autorisés CORS |

### 12.3 GitHub Actions CI/CD

Le workflow `.github/workflows/deploy-pythonanywhere.yml` automatise chaque déploiement sur push `main` :

```
Push sur main
    ↓ npm ci + npm run build      (build frontend React/Vite)
    ↓ scp dist/ → PythonAnywhere  (upload fichiers statiques via SSH)
    ↓ git pull origin main        (mise à jour code backend)
    ↓ flask db upgrade            (application migrations Alembic)
    ↓ API PythonAnywhere reload   (redémarrage application)
    ↓ curl /health → 200 OK       (smoke test)
```

### 12.4 Tâches planifiées (PythonAnywhere Scheduled Tasks)

En remplacement de Celery/Redis (non disponibles sur PythonAnywhere) :

| Tâche | Commande | Fréquence |
|---|---|---|
| ETL quotidien (Feature Store) | `flask etl-daily` | Chaque nuit à 02h00 |
| Entraînement ML | `flask ml-train-all` | Chaque dimanche à 03h00 |
| Détection d'anomalies | `flask ml-detect-anomalies` | Toutes les heures |
| Alertes de stock | `flask send-stock-alerts` | Chaque matin à 07h00 |

---

## 13. Qualité et tests

### 13.1 Stratégie de tests

| Niveau | Outil | Cible | Couverture visée |
|---|---|---|---|
| Unitaires backend | pytest + pytest-mock | Services, utilitaires, règles RG | ≥ 80 % |
| Intégration backend | pytest + test client Flask | Endpoints API, authentification, RBAC | Tous les endpoints critiques |
| Unitaires frontend | Jest + React Testing Library | Composants, hooks, utilitaires | ≥ 80 % |
| E2E | Playwright | Parcours utilisateur complets (login → vente → sync) | Cas nominaux + cas limites |
| Charge | Locust | Simulation 50 utilisateurs simultanés | P95 < 500 ms |
| Sécurité | OWASP ZAP (passif) | Injection, XSS, CSRF, exposition de données | Aucune vulnérabilité haute |

### 13.2 Qualité du code

- **Linting :** `flake8` + `black` (backend), `ESLint` + `Prettier` (frontend)
- **Typage :** TypeScript strict côté frontend, annotations de types Python (mypy optionnel)
- **Revues de code :** Pull Requests systématiques (GitFlow : `feature/*` → `develop` → `main`)
- **Documentation :** Docstrings Python pour tous les services, JSDoc pour les hooks React

---

## 14. Méthodologie de développement

### 14.1 Scrum adapté (projet académique)

- **Sprints de 2 semaines**, 12 sprints au total (24 semaines)
- Backlog : 11 Epics couvrant les 32 RF
- Outils : GitHub Projects (Kanban), Git avec GitFlow simplifié (`main`, `develop`, `feature/*`)

### 14.2 Planning des sprints

| Sprint | Objectif principal | Livrables clés |
|---|---|---|
| 0 | Cadrage | MCD/MLD/MPD, architecture, Docker Compose |
| 1-2 | Authentification + RBAC | Login JWT, multi-tenant, RBAC décorateur |
| 3-4 | Catalogue + Stock + Transferts | CRUD produits, mouvements de stock |
| 5-6 | Ventes + Inventaires | Caisse, remises encadrées, inventaire physique |
| 7 | Mode offline-first | Service Worker, IndexedDB, sync queue |
| 8-9 | Module IA (prévision + scoring) | Prophet, XGBoost, Random Forest |
| 10 | Dashboard BI + Anomalies | SSE, Isolation Forest, ABC/XYZ |
| 11 | Multi-tenant avancé | Provisioning tenant, plans d'abonnement |
| 12 | Tests + CI/CD + Documentation | Couverture ≥ 80 %, pipeline GitHub Actions |

### 14.3 Documentation technique

La documentation est structurée en **34 fichiers Markdown** (~800 pages) organisés en 8 parties :

| Partie | Fichiers | Contenu |
|---|---|---|
| Introduction & Contexte | 00-02 | Préface, introduction, étude de marché |
| Analyse & Modélisation | 03-07 | RF/RNF/RG, MoSCoW, cas d'utilisation, UML |
| Architecture technique | 08-10 | Architecture 3-tiers, backend Flask, frontend React |
| Base de données & APIs | 11-18 | MCD/MLD/MPD, dictionnaire, API REST OpenAPI 3.0, sécurité |
| Analyse de données & IA | 19-22 | Pipeline ETL, modèles ML, dashboard BI |
| Implémentation & Tests | 23-24 | Plan Agile, stratégie de tests |
| Déploiement & Exploitation | 25-29 | Docker, PWA, multi-tenant, monitoring, wireframes |
| Conclusion & Annexes | 30-34 | Glossaire, conclusion, guides de déploiement |

---

## 15. État d'avancement et perspectives

### 15.1 État actuel

| Module | État | Notes |
|---|---|---|
| Backend Flask (API complète) | ✅ Opérationnel | 11 blueprints, 32 RF |
| Frontend React (PWA) | ✅ Opérationnel | Build Vite servi par Flask |
| Base de données MySQL | ✅ Opérationnel | 32 tables, migrations Alembic |
| Authentification JWT + RBAC | ✅ Opérationnel | 3 rôles, liste noire tokens |
| Mode offline-first | ✅ Implémenté | Service Worker, IndexedDB, sync queue |
| Pipeline ETL + Feature Store | ✅ Implémenté | Tables `fs_*`, extraction incrémentale |
| Prévision Prophet + XGBoost | ✅ Implémenté | Validé sur données synthétiques |
| Scoring crédit (Random Forest) | ✅ Implémenté | F1-score > 0,85 sur jeu synthétique |
| Détection anomalies (Isolation Forest) | ✅ Implémenté | Contamination = 2 % |
| ABC/XYZ + RFM K-Means | ✅ Implémenté | |
| Dashboard SSE temps réel | ✅ Implémenté | |
| Multi-tenant (PostgreSQL) | ✅ Implémenté | Désactivé sur MySQL (production V1) |
| CI/CD GitHub Actions | ✅ Configuré | |
| Déploiement PythonAnywhere | ✅ Live | https://mannudev.pythonanywhere.com |
| Données de démonstration | ✅ Générées | 12 mois historique, 200 produits |

### 15.2 Perspectives V2

- **Application mobile native** (React Native) avec mode offline natif
- **Intégration Mobile Money** : Orange Money, Moov Money (paiement en caisse)
- **Multi-tenant PostgreSQL en production** (VPS ou cloud)
- **Module comptabilité** : journal comptable, bilan simplifié
- **Marketplace B2B** : commandes inter-quincailleries
- **API publique** pour intégration avec systèmes existants des clients

---

## Annexe — Accès à la démonstration

| Ressource | URL / Commande |
|---|---|
| **Application live** | https://mannudev.pythonanywhere.com |
| **API Health check** | https://mannudev.pythonanywhere.com/health |
| **Compte admin démo** | Email : `admin@gescom-bf.bf` (contacter l'auteur pour le mot de passe) |
| **Données de démo** | 12 mois de ventes simulées, ~200 produits, 5 boutiques |
| **Code source** | Disponible sur demande |

---

*Document mis à jour le 18 juin 2026 — Version 2.0 (section Analyse de données & IA enrichie)*  
*GesCom-BF — Système de Gestion Commerciale SaaS · Burkina Faso*
