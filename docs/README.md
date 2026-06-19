# GesCom-BF — Documentation complète de conception

Solution SaaS de gestion commerciale et de stock pour les quincailleries et boutiques de pièces détachées du Burkina Faso (Flask · React/TypeScript · PostgreSQL/MySQL · IA : Prophet/XGBoost/scikit-learn).

Cette documentation (32 fichiers) couvre l'intégralité du cycle de conception : analyse, modélisation Merise/UML, architecture, base de données, APIs, sécurité, intelligence artificielle, tests, déploiement (Docker Compose + PythonAnywhere MySQL), SaaS multi-tenant et perspectives.

> Conventions de référencement : **RF-XX** (exigence fonctionnelle), **RNF-XX** (exigence non fonctionnelle), **RG-XX** (règle de gestion), **UC-XX** (cas d'utilisation). Voir détails et glossaire en `30-GLOSSAIRE-ANNEXES.md`.

## Partie 1 — Introduction & Contexte

| Fichier | Contenu |
|---|---|
| [00-PREFACE.md](00-PREFACE.md) | Objet du document, public visé, conventions, sommaire |
| [01-INTRODUCTION.md](01-INTRODUCTION.md) | Contexte, problématique, objectifs SMART (O1-O8), utilisateurs |
| [02-ETUDE-DU-MARCHE.md](02-ETUDE-DU-MARCHE.md) | Analyse concurrentielle (Odoo, Sage, Wave, Excel), justification technologique |

## Partie 2 — Analyse & Modélisation

| Fichier | Contenu |
|---|---|
| [03-ANALYSE-DES-BESOINS.md](03-ANALYSE-DES-BESOINS.md) | RF-01 à RF-32, RNF-01 à RNF-18, matrice MoSCoW |
| [04-REGLES-METIER.md](04-REGLES-METIER.md) | RG-01 à RG-42, invariants métier |
| [05-ARCHITECTURE-FONCTIONNELLE.md](05-ARCHITECTURE-FONCTIONNELLE.md) | Modules, cycle métier, flux offline/IA |
| [06-CAS-DUTILISATION.md](06-CAS-DUTILISATION.md) | UC-01 à UC-18, fiches détaillées |
| [07-DIAGRAMMES-UML.md](07-DIAGRAMMES-UML.md) | Classes, séquences, activité, états, composants |

## Partie 3 — Architecture technique

| Fichier | Contenu |
|---|---|
| [08-ARCHITECTURE-TECHNIQUE.md](08-ARCHITECTURE-TECHNIQUE.md) | Architecture 3-tiers, stack, volumétrie, déploiement |
| [09-BACKEND-FLASK.md](09-BACKEND-FLASK.md) | Structure backend, blueprints, services, Celery |
| [10-FRONTEND-REACT.md](10-FRONTEND-REACT.md) | Structure frontend, écrans, PWA, i18n |

## Partie 4 — Base de données & APIs

| Fichier | Contenu |
|---|---|
| [11-BASE-DE-DONNEES.md](11-BASE-DE-DONNEES.md) | Vue d'ensemble, approche MCD/MLD/MPD |
| [12-MCD.md](12-MCD.md) | Modèle Conceptuel de Données (Merise) |
| [13-MLD.md](13-MLD.md) | Modèle Logique de Données |
| [14-MPD.md](14-MPD.md) | Modèle Physique de Données (DDL PostgreSQL) |
| [15-DICTIONNAIRE-DES-DONNEES.md](15-DICTIONNAIRE-DES-DONNEES.md) | Dictionnaire complet des données |
| [16-CONTRAINTES-SQL.md](16-CONTRAINTES-SQL.md) | Contraintes, triggers, index, purge |
| [17-API-REST.md](17-API-REST.md) | Spécification OpenAPI 3.0 |
| [18-SECURITE.md](18-SECURITE.md) | RBAC, JWT, chiffrement, OWASP Top 10 |

## Partie 5 — Analyse de données & Intelligence Artificielle

| Fichier | Contenu |
|---|---|
| [19-ANALYSE-DE-DONNEES.md](19-ANALYSE-DE-DONNEES.md) | Positionnement du module, pipeline global |
| [20-MACHINE-LEARNING.md](20-MACHINE-LEARNING.md) | Prophet/XGBoost, scoring crédit, RFM/K-Means, Isolation Forest |
| [21-PIPELINE-ETL.md](21-PIPELINE-ETL.md) | ETL, Great Expectations, MLflow, data lineage |
| [22-DASHBOARD-BI.md](22-DASHBOARD-BI.md) | Tableau de bord temps réel, exports PDF |

## Partie 6 — Implémentation & Tests

| Fichier | Contenu |
|---|---|
| [23-PLAN-DE-DEVELOPPEMENT.md](23-PLAN-DE-DEVELOPPEMENT.md) | Méthodologie Agile, backlog, 12 sprints |
| [24-PLAN-DE-TESTS.md](24-PLAN-DE-TESTS.md) | Stratégie de tests (unitaires, intégration, E2E, charge, IA) |

## Partie 7 — Déploiement & Exploitation

| Fichier | Contenu |
|---|---|
| [25-DEPLOIEMENT-CICD.md](25-DEPLOIEMENT-CICD.md) | Docker Compose, CI/CD, sauvegardes, PRA/PCA |
| [26-GESTION-OFFLINE-PWA.md](26-GESTION-OFFLINE-PWA.md) | PWA, IndexedDB, synchronisation, gestion des conflits |
| [27-MODELE-SAAS-MULTITENANT.md](27-MODELE-SAAS-MULTITENANT.md) | Schema-per-tenant (PostgreSQL), mono-tenant MySQL, provisioning, plans d'abonnement |
| [28-MONITORING-OBSERVABILITE.md](28-MONITORING-OBSERVABILITE.md) | Logs, métriques, alerting |
| [29-WIREFRAMES-UI.md](29-WIREFRAMES-UI.md) | Maquettes des écrans clés (caisse, dashboard, IA) |
| [32-GUIDE-DEPLOIEMENT-PYTHONANYWHERE.md](32-GUIDE-DEPLOIEMENT-PYTHONANYWHERE.md) | **Guide complet déploiement PythonAnywhere** (MySQL, mono-tenant) — WSGI, migrations, Scheduled Tasks, troubleshooting |

## Partie 8 — Conclusion & Annexes

| Fichier | Contenu |
|---|---|
| [30-GLOSSAIRE-ANNEXES.md](30-GLOSSAIRE-ANNEXES.md) | Glossaire métier/technique, tables de correspondance, hypothèses |
| [31-CONCLUSION-PERSPECTIVES.md](31-CONCLUSION-PERSPECTIVES.md) | Synthèse, réponse aux objectifs, limites, perspectives V2 |

## Comment lire cette documentation

- **Pour une vue d'ensemble rapide** : 00, 01, 31.
- 