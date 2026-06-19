<<<<<<< HEAD
# Smart_trade
Une plateforme qui permet au commercant de suivre les ventes en temps réel et les tendances analytiques de leur bussiness
=======
# GesCom-BF — Gestion commerciale pour quincailleries (V1)

Application de gestion commerciale et de stock pour les quincailleries au
Burkina Faso : authentification & RBAC, catalogue produits, stock multi-sites,
fournisseurs/réceptions, transferts inter-sites, et caisse (ventes avec
remises encadrées et crédit client).

La documentation complète (besoins, règles métier, architecture, modèle de
données, API, sécurité, plan de tests, etc.) se trouve dans [`docs/`](docs/)
(31 documents + sommaire dans `docs/README.md`).

## Périmètre de cette version (V1)

Conformément au cadrage retenu ("Socle + module Ventes", mono-tenant) :

| Inclus dans le code livré | Différé (cf. `docs/23-PLAN-DE-DEVELOPPEMENT.md`) |
| --- | --- |
| Authentification JWT + RBAC (rôles ADMIN / MAGASINIER / VENDEUR) | Multi-tenant SaaS |
| Sites (dépôt + boutiques), catalogue produits, catégories, marques | PWA hors-ligne |
| Stock par site + mouvements | Module Machine Learning / prévisions |
| Fournisseurs, réceptions, transferts inter-sites (backend) | Internationalisation (mooré) |
| Ventes (caisse) : remises encadrées (RG-22/23), crédit client (RG-26), immutabilité (RG-27) | Écrans Fournisseurs/Réceptions/Transferts côté frontend |
| Tableau de bord (indicateurs du jour) | |
| Frontend : Connexion, Tableau de bord, Produits, Caisse | |

## Architecture & stack

- **Backend** : Python 3.12 / Flask 3, Flask-SQLAlchemy, Flask-Migrate (Alembic), Flask-JWT-Extended, Marshmallow.
- **Base de données** : PostgreSQL 16 (développement Docker) · **MySQL 8.0** (production PythonAnywhere — driver PyMySQL, mono-tenant). La détection du dialecte est automatique via `DATABASE_URL` (cf. `backend/app/utils/db_dialect.py`).
- **Frontend** : React 18 + TypeScript (strict) + Vite, Tailwind CSS, TanStack Query, Zustand, React Hook Form + Zod, Axios.
- **Design** : palette Adobe Color — `#011140` (primary-dark), `#0439D9` (primary), `#5086F2` (accent), `#758EBF` (muted), `#F2F2F2` (surface).
- **Dev local** : Docker Compose (PostgreSQL, Redis, API Flask, frontend Vite).
- **Production** : PythonAnywhere (plan Developer · MySQL managé · 20 tâches planifiées · SSH).

## Démarrage rapide (Docker Compose)

Prérequis : Docker et Docker Compose installés.

```bash
# 1. Copier le fichier d'environnement et l'adapter si besoin
cp .env.example .env

# 2. Démarrer toute la stack (DB, Redis, API, frontend)
docker compose up --build
```

Au démarrage, le conteneur `api` exécute automatiquement les migrations
(`flask db upgrade`) puis le script de seed (`python -m app.seed`), qui crée :

- les rôles/permissions RBAC,
- 3 sites (1 dépôt + 2 boutiques),
- 3 comptes de démonstration,
- un catalogue de 7 produits de quincaillerie avec stock initial par site,
- 2 clients de démonstration (dont un client "technicien" avec encours de crédit).

Une fois démarré :

- Frontend : http://localhost:5173
- API : http://localhost:5000/api/v1

### Comptes de démonstration

| Rôle | Email | Mot de passe | Site |
| --- | --- | --- | --- |
| ADMIN | `admin@gescom-bf.bf` | `Admin#2026` | — (tous sites) |
| MAGASINIER | `magasinier@gescom-bf.bf` | `Magasinier#2026` | Dépôt Central |
| VENDEUR | `vendeur@gescom-bf.bf` | `Vendeur#2026` | Boutique Tanghin |

> Ces identifiants sont définis dans `backend/app/seed.py` (et surchargeables
> via `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`). À changer impérativement
> avant toute mise en production (cf. `docs/18-SECURITE.md`).

## Développement sans Docker

**Backend (PostgreSQL — défaut)**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://gescom:gescom_dev_password@localhost:5432/gescom_bf
flask db upgrade
python -m app.seed
flask run --port 5000
```

**Backend (MySQL — alternative sans Docker)**

```bash
# MySQL doit être installé localement (ou utiliser une instance distante)
export DATABASE_URL=mysql+pymysql://gescom:gescom_dev_password@localhost:3306/gescom_bf?charset=utf8mb4
flask db upgrade   # génère les tables en DDL MySQL pur (pas de CREATE SCHEMA)
python -m app.seed
flask run --port 5000
```

> Le dialecte est détecté automatiquement via `DATABASE_URL` — aucune modification de code nécessaire. Cf. `backend/app/utils/db_dialect.py`.

**Frontend**
