# 30. Glossaire & Annexes

## 30.1 Glossaire métier

| Terme | Définition |
|---|---|
| **Quincaillerie** | Commerce de détail spécialisé dans la vente de matériaux de construction, outillage, peinture, visserie, etc. |
| **Dépôt central** | Site unique de stockage principal d'où sont approvisionnées les boutiques (RG-13) |
| **Boutique** | Point de vente au détail rattaché à l'entreprise, recevant son stock du dépôt central |
| **Prix simple** | Tarif standard appliqué au grand public |
| **Prix technicien** | Tarif préférentiel appliqué aux clients professionnels identifiés (maçons, électriciens, etc.) (RG-21) |
| **Remise encadrée** | Réduction de prix limitée à une liste fermée de taux autorisés (0/5/10/15/20 %), avec approbation au-delà d'un seuil (RG-22, RG-23) |
| **Vente à crédit** | Vente enregistrée sans paiement immédiat, avec créance sur le client (RG-26) |
| **Rupture de stock** | Situation où le stock disponible d'un produit atteint zéro, empêchant la vente |
| **Inventaire** | Opération de comptage physique du stock, comparée au stock théorique informatique (UC-10, RG-33) |
| **Mode hors-ligne (offline-first)** | Capacité de l'application à fonctionner sans connexion réseau, avec synchronisation différée (RF-20) |
| **Tenant** | Entreprise cliente disposant d'un espace de données isolé dans l'application SaaS (`27-MODELE-SAAS-MULTITENANT.md`) |
| **Mooré** | Langue locale majoritairement parlée au Burkina Faso, proposée en option d'interface (RF-32) |
| **Tabaski** | Fête religieuse (Aïd al-Adha) à date mobile, prise en compte dans la saisonnalité des prévisions (`20-MACHINE-LEARNING.md`) |

## 30.2 Glossaire technique

| Terme / Sigle | Définition |
|---|---|
| **MCD / MLD / MPD** | Modèle Conceptuel / Logique / Physique de Données — méthodologie Merise de modélisation de bases de données |
| **UML** | Unified Modeling Language — langage de modélisation orienté objet (diagrammes de classes, cas d'utilisation, séquence, états) |
| **API REST** | Interface de programmation respectant les principes REST (ressources, verbes HTTP, statuts) |
| **OpenAPI** | Spécification standardisée pour décrire une API REST (`17-API-REST.md`) |
| **JWT (JSON Web Token)** | Jeton signé utilisé pour l'authentification sans état (RG-36) |
| **RBAC (Role-Based Access Control)** | Contrôle d'accès basé sur les rôles (`18-SECURITE.md`) |
| **ORM (Object-Relational Mapping)** | Technique de mapping objet-relationnel (ici SQLAlchemy) |
| **PWA (Progressive Web App)** | Application web pouvant fonctionner comme une application native, avec mode hors-ligne (`26-GESTION-OFFLINE-PWA.md`) |
| **IndexedDB** | Base de données clé-valeur intégrée au navigateur, utilisée pour le stockage offline (Dexie.js) |
| **Service Worker** | Script exécuté en arrière-plan par le navigateur, permettant le cache et la synchronisation différée |
| **Schema-per-tenant** | Stratégie d'isolation multi-tenant où chaque client dispose de son propre schéma PostgreSQL (`27-MODELE-SAAS-MULTITENANT.md`) |
| **Celery / Celery Beat** | Système de tâches asynchrones et planifiées en Python, basé sur Redis comme broker |
| **Prophet** | Bibliothèque de prévision de séries temporelles développée par Meta |
| **XGBoost** | Algorithme de boosting de gradient pour la régression/classification |
| **Random Forest** | Algorithme d'apprentissage ensembliste à base d'arbres de décision |
| **Isolation Forest** | Algorithme de détection d'anomalies non supervisé |
| **RFM (Récence, Fréquence, Montant)** | Méthode de segmentation client basée sur le comportement d'achat |
| **K-Means** | Algorithme de clustering non supervisé |
| **ABC/XYZ** | Méthode de classification des produits combinant valeur (ABC) et variabilité de la demande (XYZ) |
| **MLflow** | Plateforme de gestion du cycle de vie des modèles ML (suivi des expériences, registre de modèles) |
| **Great Expectations** | Bibliothèque Python de validation de la qualité des données |
| **Data lineage** | Traçabilité de bout en bout entre les données sources, le modèle entraîné et les prédictions produites |
| **RMSE / MAE / MAPE** | Métriques d'erreur pour les modèles de régression (Root Mean Squared Error, Mean Absolute Error, Mean Absolute Percentage Error) |
| **ROC-AUC** | Aire sous la courbe ROC, métrique d'évaluation pour les modèles de classification |
| **RTO / RPO** | Recovery Time Objective / Recovery Point Objective — indicateurs de plan de reprise d'activité (`25-DEPLOIEMENT-CICD.md`) |
| **CI/CD** | Intégration Continue / Déploiement Continu |
| **OWASP Top 10** | Référentiel des 10 risques de sécurité les plus critiques pour les applications web |

## 30.3 Index des conventions de référencement

| Préfixe | Signification | Référence principale |
|---|---|---|
| **RF-XX** | Exigence Fonctionnelle | `03-ANALYSE-DES-BESOINS.md` |
| **RNF-XX** | Exigence Non Fonctionnelle | `03-ANALYSE-DES-BESOINS.md` |
| **RG-XX** | Règle de Gestion | `04-REGLES-METIER.md` |
| **UC-XX** | Cas d'utilisation (Use Case) | `06-CAS-DUTILISATION.md` |

## 30.4 Annexe A — Table de correspondance RF ↔ Modules ↔ Documents

| RF | Module | Document(s) de référence |
|---|---|---|
| RF-01 à RF-05 | Authentification & utilisateurs | `09-BACKEND-FLASK.md`, `18-SECURITE.md` |
| RF-06 à RF-10 | Catalogue produits | `09-BACKEND-FLASK.md`, `15-DICTIONNAIRE-DES-DONNEES.md` |
| RF-11 à RF-14 | Stock, dépôt, transferts | `06-CAS-DUTILISATION.md` (UC-08, UC-09), `16-CONTRAINTES-SQL.md` |
| RF-15 à RF-19 | Ventes | `06-CAS-DUTILISATION.md` (UC-11 à UC-13), `09-BACKEND-FLASK.md` |
| RF-20 | Mode offline | `26-GESTION-OFFLINE-PWA.md` |
| RF-21 à RF-23 | Inventaires | `06-CAS-DUTILISATION.md` (UC-10) |
| RF-24, RF-29 | Rapports & dashboard | `22-DASHBOARD-BI.md` |
| RF-25 à RF-28 | Module IA | `19-ANALYSE-DE-DONNEES.md`, `20-MACHINE-LEARNING.md`, `21-PIPELINE-ETL.md` |
| RF-30 à RF-32 | Audit, sécurité, i18n | `18-SECURITE.md`, `10-FRONTEND-REACT.md` |

## 30.5 Annexe B — Hypothèses et limites assumées du projet

| Hypothèse / Limite | Justification | Document de détail |
|---|---|---|
| Jeu de données IA synthétique | Absence de données réelles disponibles au démarrage du projet | `20-MACHINE-LEARNING.md` §20.6 |
| Calendrier Tabaski approximé par dates fixes | Calendrier lunaire complexe à intégrer en V1 | `20-MACHINE-LEARNING.md` §20.6.2 |
| Mode offline limité à la vente au comptoir | Compromis de complexité pour la V1 | `26-GESTION-OFFLINE-PWA.md` §26.10 |
| Stack monitoring complète (Prometheus/Loki/Grafana) non déployée en V1 | Périmètre académique, priorité aux fonctions métier | `28-MONITORING-OBSERVABILITE.md` §28.2 |
| Tarification SaaS indicative, non validée par étude de marché complète | Hors périmètre technique du projet | `27-MODELE-SAAS-MULTITENANT.md` §27.5 |

## 30.6 Annexe C — Outils et bibliothèques (récapitulatif)

| Catégorie | Outils |
|---|---|
| Backend | Python 3.12, Flask, SQLAlchemy, Alembic, Flask-JWT-Extended, Celery, Redis, Gunicorn |
| Frontend | React 18, TypeScript, Vite, TanStack Query, Zustand, React Hook Form, Zod, Tailwind CSS, Dexie.js, react-i18next, Recharts, D3.js |
| Base de données | PostgreSQL 16 (extensions : pg_trgm) |
| Machine Learning | scikit-learn, Prophet, XGBoost, MLflow, Great Expectations |
| Tests | pytest, pytest-cov, Jest, React Testing Library, Playwright, Locust |
| Infrastructure | Docker, Docker Compose, Nginx, GitHub Actions |
| Observabilité | Sentry, Prometheus, Loki, Grafana (cibles recommandées) |
| Documents | WeasyPrint (export PDF) |

## 30.7 Annexe D — Calendrier de référence (jours fériés Burkina Faso, exemples)

| Date (approx.) | Fête | Impact saisonnier modélisé |
|---|---|---|
| 1er janvier | Nouvel An | Hausse ventes peinture/décoration (`is_holiday`) |
| 8 mars | Journée internationale de la femme | Impact modéré |
| Date mobile (lunaire) | Tabaski (Aïd al-Adha) | Hausse marquée (+50 % approximé), cf. limite §20.6.2 |
| 5 août | Fête de l'Indépendance | Impact modéré |
| 25 décembre | Noël | Hausse ventes peinture/décoration |
| Juin à octobre | Saison des pluies | Hausse matériaux de construction (`is_rainy_season`, +40 %) |

> Source à confirmer/compléter auprès du calendrier officiel du Burkina Faso pour l'année d'exploitation réelle.
