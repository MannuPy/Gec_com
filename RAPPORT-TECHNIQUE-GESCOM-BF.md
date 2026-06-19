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
      quantite_recommandee = MAX(0, prevision_demande_30j 