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

C'est le **cœur différenciant** du projet. Il transforme les données opérationnelles en aide à la décision via 5 modèles/techniques complémentaires.

### 10.1 Vue d'ensemble des modèles

| Modèle | Algorithme | Type | Granularité | Fréquence |
|---|---|---|---|---|
| Prévision de demande | **Prophet + XGBoost** | Série temporelle | (produit, boutique) | Hebdomadaire |
| Scoring de solvabilité | **Random Forest + Régression Logistique** | Classification binaire | Client | Quotidienne |
| Détection d'anomalies | **Isolation Forest** | Non-supervisé | Transaction | Horaire |
| Classification ABC/XYZ | Règles statistiques (pandas) | Déterministe | Produit | Hebdomadaire |
| Segmentation clients | **K-Means (RFM)** | Clustering | Client | Mensuelle |

### 10.2 Prévision de rupture de stock (Prophet + XGBoost)

**Objectif :** Prédire, pour chaque couple (produit, boutique), la demande journalière sur 7 à 30 jours et calculer la date probable de rupture.

**Features d'entrée :**

| Feature | Source | Type |
|---|---|---|
| `y` (quantité vendue/jour) | `SUM(sale_lines.quantity)` | Variable cible |
| `is_holiday` | Référentiel jours fériés BF | Booléen |
| `is_rainy_season` | Juin-octobre = 1 | Booléen |
| `day_of_week` | Dérivé de la date | Catégoriel |
| `promotion_active` | Remises actives sur le produit | Booléen |
| `stock_level_lag7` | Stock J-7 | Numérique (XGBoost uniquement) |

**Architecture du modèle hybride :**

```python
# Étape 1 : Modèle Prophet (saisonnalité)
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    seasonality_mode="multiplicative"
)
model.add_country_holidays(country_name="BF")  # Jours fériés Burkina Faso
model.add_seasonality("rainy_season", period=365.25, fourier_order=5,
                       condition_name="is_rainy_season")
model.fit(df_train)
prophet_forecast = model.predict(future)

# Étape 2 : XGBoost affine les résidus Prophet
residual = y_train - prophet_forecast_train["yhat"]
xgb = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05)
xgb.fit(X_exogenous_train, residual)

# Prévision finale = Prophet + correction XGBoost
final_forecast = prophet_forecast_test["yhat"] + xgb.predict(X_exogenous_test)
```

**Métriques de performance (jeu synthétique — 200 produits, 5 boutiques, 24 mois) :**

| Métrique | Prophet seul | Prophet + XGBoost | Cible projet |
|---|---|---|---|
| RMSE (unités/jour) | 4,8 | **3,6** | < 5,0 |
| MAE (unités/jour) | 3,5 | **2,7** | < 4,0 |
| MAPE | 22 % | **15 %** | < 20 % |
| Couverture intervalle 80 % | 78 % | 81 % | ≥ 75 % |

**Règle d'alerte automatique :**
```
SI stock_disponible(produit, boutique) < seuil_min_stock
   OU stock_prévu_J+7 < 0
ALORS → alerte RUPTURE_STOCK → notification administrateur
```

### 10.3 Scoring de solvabilité client (crédit informel)

**Problème métier :** Les commerçants accordent du crédit informellement. Le système calcule automatiquement un score de risque pour chaque client.

**Features client (Feature Store `fs_customer_credit_features`) :**

| Feature | Description |
|---|---|
| `total_credit_amount` | Encours de crédit total |
| `nb_late_payments` | Nombre de paiements en retard |
| `avg_days_to_pay` | Délai moyen de remboursement (jours) |
| `payment_reliability_score` | Ratio (paiements à temps / total paiements) |
| `total_purchases` | Volume d'achat total (ancienneté client) |
| `last_purchase_days_ago` | Récence du dernier achat (RFM — Recency) |

**Modèle :** Ensemble Random Forest + Régression Logistique, comparatif sur validation croisée k-fold. Sortie : score [0–1] et classe binaire (bon/mauvais payeur). Seuil optimisé sur le F1-score pondéré (pénalisation asymétrique des faux négatifs).

### 10.4 Détection d'anomalies (Isolation Forest)

**Objectif :** Détecter automatiquement les comportements suspects : remises inhabituelles, écarts de stock inexpliqués, ventes atypiques (possible fraude).

```python
from sklearn.ensemble import IsolationForest

model = IsolationForest(
    n_estimators=200,
    contamination=0.02,    # 2 % de transactions supposées anormales
    random_state=42
)
model.fit(X_train_transactions)
scores = model.decision_function(X_new)
# Score < seuil_anomalie → alerte générée
```

**Types d'anomalies détectés :**
- Vente avec remise > 20 % non autorisée
- Quantité vendue hors de la plage historique (3σ)
- Mouvement de stock sans vente/transfert associé
- Vente au-delà des heures d'ouverture habituelles

### 10.5 Classification ABC/XYZ

| Axe | Critère | Classe |
|---|---|---|
| **ABC** (valeur) | Part dans le CA total | A = 80 %, B = 15 %, C = 5 % |
| **XYZ** (régularité) | Coefficient de variation de la demande | X = CV < 50 %, Y = 50–100 %, Z = > 100 % |

La combinaison donne 9 catégories (AX, AY, AZ... CZ) guidant la politique de réapprovisionnement : les produits **AX** (forte valeur, demande régulière) bénéficient d'un réapprovisionnement automatisé.

### 10.6 Pipeline ETL et traçabilité (MLflow)

```
PostgreSQL/MySQL (données opérationnelles)
    ↓ Extraction incrémentale (cron quotidien)
    ↓ Nettoyage + validation (Great Expectations)
    ↓ Feature Engineering → Feature Store (tables fs_*)
    ↓ Entraînement modèles → MLflow (métriques, artefacts, versions)
    ↓ Stockage prédictions → table predictions
    ↓ Dashboard temps réel (SSE) + Alertes
```

Chaque expérience ML est tracée dans MLflow avec : les hyperparamètres, les métriques de validation, le chemin des données d'entraînement (data lineage), et le numéro de version du modèle déployé.

### 10.7 Dashboard BI temps réel

Le tableau de bord de l'administrateur utilise **Server-Sent Events (SSE)** pour pousser les métriques en temps réel sans polling :

```
GET /api/v1/reports/dashboard/stream
    → Flux SSE toutes les 5 secondes
    → Métriques : CA du jour, ventes en cours, alertes actives, top produits
    → Limite : 60 événements par connexion → client se reconnecte automatiquement
```

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

*Document généré le 18 juin 2026 — Version 1.0*  
*GesCom-BF — Système de Gestion Commerciale SaaS · Burkina Faso*
