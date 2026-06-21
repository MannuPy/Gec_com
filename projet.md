 Documentation - Solution SaaS de Gestion Commerciale

## Objectif
Cette documentation décrit la conception complète d'une solution SaaS de gestion commerciale et de stock destinée aux quincailleries et boutiques de pièces détachées du Burkina Faso.

## Technologies
- Backend : Flask
- Frontend : React + TypeScript
- Base de données : PostgreSQL
- ORM : SQLAlchemy
- Auth : JWT
- Cache : Redis
- IA : Scikit-learn, Prophet/XGBoost



# Préface

Ce référentiel constitue la documentation de conception du projet.

## Public visé
- Développeurs
- Architectes
- Encadreurs
- Jury
- Futurs mainteneurs

## Vision
Créer une solution SaaS simple, robuste et adaptée aux réalités des quincailleries et boutiques de pièces détachées du Burkina Faso.

Introduction  
# Introduction

## Contexte

Les commerces ciblés utilisent principalement des cahiers et Excel.

Le projet vise à offrir une plateforme SaaS permettant :

- Gestion du dépôt central
- Gestion des boutiques
- Gestion des ventes
- Gestion des stocks
- Rapports décisionnels
- Analyse de données
- Intelligence artificielle

## Utilisateurs

- Administrateur
- Magasinier
- Vendeur

## Particularités métier

- Un seul dépôt central
- Plusieurs boutiques
- Pas de scanner obligatoire
- Deux tarifs de vente :
  - Client simple
  - Technicien
- Remises fixes : 5 %, 10 %, 15 %, 20 %
- Validation des remises par accord verbal de l'administrateur

2 Architecture-fonctionnelle 


# Architecture fonctionnelle

```text
Entreprise
    |
    +-- Dépôt Central
            |
            +-- Boutique 1
            +-- Boutique 2
            +-- Boutique N
```

## Modules

1. Authentification
2. Utilisateurs
3. Produits
4. Fournisseurs
5. Dépôt
6. Transferts
7. Ventes
8. Inventaires
9. Rapports
10. Analytics
11. IA
12. Audit

## Cycle métier

Fournisseur
→ Réception
→ Dépôt
→ Transfert
→ Boutique
→ Vente
→ Rapport


3 -- Architecture --Technique 


# Architecture technique

## Backend

- Flask
- SQLAlchemy
- Alembic
- JWT
- Celery
- Redis

## Frontend

- React
- TypeScript
- Vite
- React Query

## Base

PostgreSQL

## Déploiement

Docker
Nginx
Gunicorn

## Blueprints

auth/
users/
products/
suppliers/
inventory/
sales/
reports/
analytics/
audit/


4 -- Base de données md 
# Base de données

## Tables principales

- companies
- branches
- users
- roles
- permissions
- suppliers
- customers
- categories
- brands
- products
- stock
- stock_movements
- transfers
- transfer_lines
- sales
- sale_lines
- discounts
- inventory
- inventory_lines
- audit_logs

## Exemple : table products

| Champ | Type | Contraintes |
|-------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(200) | NOT NULL |
| reference | VARCHAR(100) | UNIQUE |
| category_id | UUID | FK |
| brand_id | UUID | FK |
| purchase_price | NUMERIC | CHECK > 0 |
| retail_price | NUMERIC | CHECK > 0 |
| technician_price | NUMERIC | CHECK > 0 |
| min_stock | INTEGER | DEFAULT 0 |

Contraintes :
- reference UNIQUE
- purchase_price > 0
- retail_price >= purchase_price
- technician_price <= retail_price
- ON DELETE RESTRICT sur category_id

5--Machine Learning 

# Module Analyse de données

## ETL

Transactions
→ PostgreSQL
→ Nettoyage
→ Features
→ Modèles
→ Dashboard

## Cas d'usage

- Prévision des ventes
- Détection des anomalies
- Clustering clients
- Analyse ABC
- Rotation des stocks
- Recommandation de réapprovisionnement

## Technologies

- pandas
- scikit-learn
- Prophet
- XGBoost
