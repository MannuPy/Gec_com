> **Dernière mise à jour :** 1er juillet 2026 — mise à jour conformité code v2.

# Préface

## À propos de ce document

Ce référentiel constitue la documentation complète de conception, d'architecture et de soutenance du projet **GesCom-BF** : une solution SaaS de gestion commerciale et de stock destinée aux quincailleries et boutiques de pièces détachées du Burkina Faso.

Il a été conçu pour répondre aux exigences d'un mémoire de fin de cycle en génie logiciel / analyse de données, et couvre l'ensemble du cycle de vie du projet : étude de l'existant, analyse des besoins, modélisation UML, architecture technique, base de données, APIs, sécurité, intelligence artificielle, tests, déploiement et perspectives.

## Public visé

| Public | Usage de la documentation |
|---|---|
| **Jury de soutenance** | Évaluation de la rigueur méthodologique, de la modélisation et de l'innovation |
| **Encadreurs académiques et professionnels** | Suivi de l'avancement et validation des choix techniques |
| **Équipe de développement** | Référence pour l'implémentation (backend, frontend, IA) |
| **Architectes / DevOps** | Spécifications d'infrastructure, de déploiement et de sécurité |
| **Futurs mainteneurs** | Compréhension du système, des règles métier et des choix de conception |
| **Clients potentiels (quincailleries)** | Compréhension fonctionnelle du produit |

## Périmètre couvert

Cette documentation est organisée en **8 grandes parties** (cf. `01-INTRODUCTION.md` pour le sommaire détaillé) :

1. Introduction & Contexte
2. Analyse & Modélisation (UML)
3. Architecture technique
4. Base de données & APIs
5. Module Analyse de données & Intelligence Artificielle
6. Implémentation & Tests
7. Déploiement & Exploitation
8. Conclusion & Perspectives

## Conventions utilisées dans ce document

- Les exigences fonctionnelles sont identifiées par le préfixe **RF-XX**.
- Les exigences non-fonctionnelles sont identifiées par le préfixe **RNF-XX**.
- Les cas d'utilisation sont identifiés par le préfixe **UC-XX**.
- Les règles de gestion sont identifiées par le préfixe **RG-XX**.
- Les diagrammes UML sont fournis au format **Mermaid** (rendu natif sur GitHub/GitLab et la majorité des éditeurs Markdown).
- Les spécifications API suivent la norme **OpenAPI 3.0**.
- Les termes métier spécifiques au Burkina Faso sont expliqués dans `30-GLOSSAIRE-ANNEXES.md`.

## Vision du projet

Créer une solution SaaS **simple, robuste, abordable et résiliente** (tolérante aux coupures réseau), adaptée aux réalités opérationnelles des quincailleries et boutiques de pièces détachées du Burkina Faso, tout en démontrant une **maîtrise complète du cycle de développement logiciel** et une **valeur ajoutée par l'analyse de données et l'intelligence artificielle**.

## Mise à jour et versioning de la documentation

| Version | Date | Description |
|---|---|---|
| 0.1 | - | Première version (notes de travail) |
| 1.0 | 2026-06-14 | Refonte complète : ajout UML, API REST, sécurité, ML, tests, offline, multi-tenant, glossaire |
| 1.1 | 2026-06-24 | Corrections pré-soutenance : Market Basket (Apriori), Élasticité prix, Contexte africain BF, /health, Sentry, tests unitaires (93 pytest), CI/CD actif, honnêteté sur ABC/XYZ (BI) et Churn (heuristique) |
| 2.0 | 2026-07-01 | Mise à jour conformité code v2 : 155 tests (127 ML unitaires + 17 API + 15 sécurité RBAC + 12 rôles RBAC), Celery/Redis supprimés → threads Python natifs + cron PythonAnywhere (`scripts/cron_train_all.py`), MySQL en production (PythonAnywhere), RF-05 `must_change_password` côté serveur, RF-16/RG-23 `approved_by_id` obligatoire (422), token_blocklist SQL, Flask-Limiter 3.8.0 `memory://`, SSE désactivé sur PythonAnywhere (fallback polling), 10 migrations Alembic, CI/CD GitHub Actions avec `sshpass` |

## Sommaire général du dossier `docs/`

| Fichier | Contenu |
|---|---|
| `00-PREFACE.md` | Ce document |
| `01-INTRODUCTION.md` | Contexte, problématique, objectifs SMART |
| `02-ETUDE-DU-MARCHE.md` | Analyse concurrentielle, justification technologique |
| `03-ANALYSE-DES-BESOINS.md` | Exigences fonctionnelles et non-fonctionnelles |
| `04-REGLES-METIER.md` | Règles de gestion détaillées |
| `05-ARCHITECTURE-FONCTIONNELLE.md` | Modules, cycle métier |
| `06-CAS-DUTILISATION.md` | Cas d'utilisation détaillés |
| `07-DIAGRAMMES-UML.md` | Diagrammes de classes, séquence, activité |
| `08-ARCHITECTURE-TECHNIQUE.md` | Architecture globale, NFR, offline, sécurité |
| `09-BACKEND-FLASK.md` | Structure backend, blueprints |
| `10-FRONTEND-REACT.md` | Structure frontend, PWA |
| `11-BASE-DE-DONNEES.md` | Vue d'ensemble des données |
| `12-MCD.md` | Modèle Conceptuel de Données |
| `13-MLD.md` | Modèle Logique de Données |
| `14-MPD.md` | Modèle Physique de Données (DDL) |
| `15-DICTIONNAIRE-DES-DONNEES.md` | Dictionnaire complet des données |
| `16-CONTRAINTES-SQL.md` | Contraintes, triggers, index |
| `17-API-REST.md` | Spécification OpenAPI |
| `18-SECURITE.md` | RBAC, JWT, chiffrement, OWASP |
| `19-ANALYSE-DE-DONNEES.md` | Pipeline d'analyse |
| `20-MACHINE-LEARNING.md` | Modèles IA, métriques |
| `21-PIPELINE-ETL.md` | ETL et data lineage |
| `22-DASHBOARD-BI.md` | Tableaux de bord décisionnels |
| `23-PLAN-DE-DEVELOPPEMENT.md` | Méthodologie Agile, sprints |
| `24-PLAN-DE-TESTS.md` | Stratégie de tests |
| `25-DEPLOIEMENT-CICD.md` | Docker, CI/CD, backup |
| `26-GESTION-OFFLINE-PWA.md` | Mode offline-first |
| `27-MODELE-SAAS-MULTITENANT.md` | Architecture multi-tenant, pricing |
| `28-MONITORING-OBSERVABILITE.md` | Logs, audit, alerting |
| `29-WIREFRAMES-UI.md` | Maquettes des écrans clés |
| `30-GLOSSAIRE-ANNEXES.md` | Glossaire et annexes techniques |
| `31-CONCLUSION-PERSPECTIVES.md` | Bilan et évolutions futures |
| `32-GUIDE-DEPLOIEMENT-PYTHONANYWHERE.md` | Guide de déploiement PythonAnywhere |
| `33-GUIDE-COMPLET-MISE-EN-LIGNE-PYTHONANYWHERE.md` | Guide complet mise en ligne |
| `ANALYTIQUE-ML-IA-COMPLET.md` | Document de référence complet — tous les modules analytiques/ML/IA |
