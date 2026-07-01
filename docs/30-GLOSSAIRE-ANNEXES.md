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
| **Prophet** | Bibliothèque de prévision de séries temporelles développée par Meta — utilisée pour la prévision de demande avec jours fériés Burkina Faso |
| **Random Forest** | Algorithme d'apprentissage ensembliste à base d'arbres de décision — utilisé pour le scoring crédit |
| **SHAP (SHapley Additive exPlanations)** | Méthode d'explicabilité ML permettant de quantifier la contribution de chaque feature à une prédiction |
| **Isolation Forest** | Algorithme de détection d'anomalies non supervisé |
| **RFM (Récence, Fréquence, Montant)** | Méthode de segmentation client basée sur le comportement d'achat |
| **K-Means** | Algorithme de clustering non supervisé — utilisé pour la segmentation RFM avec k optimal auto-sélectionné (Silhouette/Elbow) |
| **Apriori** | Algorithme de Market Basket Analysis — identifie les associations de produits fréquemment achetés ensemble (support/confiance/lift) |
| **ABC/XYZ** | Méthode de classification analytique BI des produits — règles déterministes (pas de ML) : ABC = contribution CA, XYZ = régularité demande |
| **Élasticité-prix** | Mesure de la sensibilité de la demande au prix — calculée par régression log-log (analytique statistique, pas de ML) |
| **Churn heuristique** | Modèle de probabilité de désengagement client basé sur la décroissance exponentielle P=1-exp(-λ×R) — pas de ML, pas de données labellisées nécessaires |
| **Flask-Limiter** | Extension Flask de rate limiting — protection brute-force, stockage `memory://` sur PythonAnywhere (compteurs remis à zéro au redémarrage) |
| **Sentry** | Plateforme de monitoring d'erreurs applicatives — capture les exceptions non gérées côté backend Flask et frontend React |
| **MLflow** | Plateforme de gestion du cycle de vie des modèles ML (suivi des expériences, registre de modèles) |
| **Great Expectations** | Bibliothèque Python de validation de la qualité des données |
| **Data lineage** | Traçabilité de bout en bout entre les données sources, le modèle entraîné et les prédictions produites |
| **RMSE / MAE / MAPE** | Métriques d'erreur pour les modèles de régression (Root Mean Squared Error, Mean Absolute Error, Mean Absolute Percentage Error) |
| **ROC-AUC** | Aire sous la courbe ROC, métrique d'évaluation pour les modèles de classification |
| **must_change_password** | Champ booléen dans le JWT indiquant que l'utilisateur doit changer son mot de passe avant toute action ; le backend retourne 403 `PASSWORD_CHANGE_REQUIRED` si `True` (RF-05 validé côté serveur) |
| **approved_by_id** | Champ obligatoire sur une vente lorsque `discount_rate > 0` — référence l'identifiant de l'administrateur ayant approuvé la remise (RF-16/RG-23 validé côté serveur) |
| **token_blocklist** | Table SQL persistant les tokens JWT révoqués (logout, changement de mot de passe) — remplace un éventuel stockage Redis non disponible sur PythonAnywhere |
| **DISABLE_SSE** | Variable d'environnement (`true`/`false`) désactivant les Server-Sent Events — à positionner à `true` sur PythonAnywhere qui ne supporte pas les connexions longue durée |
| **PA_SSH_PASSWORD** | Secret GitHub Actions contenant le mot de passe SSH PythonAnywhere, utilisé par `sshpass` pour automatiser le déploiement CI/CD |
| **cron_train_all.py** | Script Python à la racine du dépôt (`scripts/cron_train_all.py`) — déclenché par la tâche planifiée PythonAnywhere pour entraîner tous les modèles ML la nuit ; remplace Celery/Redis |
| **data_confidence** | Indicateur (HIGH/MEDIUM/LOW) reflétant la fiabilité d'une prévision de demande selon la taille de la série historique et l'algorithme utilisé |
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
| RF-25 à RF-36 | Module analytique & IA | `19-ANALYSE-DE-DONNEES.md`, `20-MACHINE-LEARNING.md`, `21-PIPELINE-ETL.md`, `ANALYTIQUE-ML-IA-COMPLET.md` |
| RF-30 à RF-32 | Audit, sécurité, i18n | `18-SECURITE.md`, `10-FRONTEND-REACT.md` |

## 30.5 Annexe B — Hypothèses et limites assumées du projet

| Hypothèse / Limite | Justification | Document de détail |
|---|---|---|
| Jeu de données IA synthétique | Absence de données réelles disponibles au démarrage du projet | `20-MACHINE-LEARNING.md` |
| Calendrier Tabaski approximé par dates fixes | Calendrier lunaire complexe à intégrer en V1 | `ANALYTIQUE-ML-IA-COMPLET.md` |
| Mode offline limité à la vente au comptoir | Compromis de complexité pour la V1 | `26-GESTION-OFFLINE-PWA.md` |
| Stack monitoring complète (Prometheus/Loki/Grafana) non déployée | Périmètre académique PythonAnywhere, priorité aux fonctions métier | `28-MONITORING-OBSERVABILITE.md` |
| Tarification SaaS indicative | Hors périmètre technique du projet | `27-MODELE-SAAS-MULTITENANT.md` |
| Flask-Limiter `memory://` — protection non persistante | PythonAnywhere ne fournit pas Redis ; compteurs remis à zéro au redémarrage | `18-SECURITE.md` |
| Churn = heuristique (pas de ML) | Absence de données labellisées "churné/fidèle" dans les PME cibles | `20-MACHINE-LEARNING.md` |
| ABC/XYZ = analytique BI (pas de ML) | Méthode déterministe suffisante et standard en gestion des stocks | `20-MACHINE-LEARNING.md` |
| Tests E2E et frontend absents | 155 tests couvrent les fonctions ML, l'intégration API et la sécurité RBAC ; les tests frontend (Jest+RTL) et E2E (Playwright) restent des perspectives V2 | `24-PLAN-DE-TESTS.md` |

## 30.6 Annexe C — Outils et bibliothèques (récapitulatif)

| Catégorie | Outils |
|---|---|
| Backend | Python 3.11+, Flask 3.0.3, SQLAlchemy, Alembic, Flask-JWT-Extended, Flask-Limiter 3.8.0 |
| Frontend | React 18, TypeScript, Vite, TanStack Query, Zustand, React Hook Form, Zod, Tailwind CSS, Dexie.js, react-i18next, Recharts |
| Base de données | MySQL (PythonAnywhere production) / PostgreSQL (cible Docker) |
| Machine Learning | scikit-learn, Prophet 1.1.5, shap 0.45.1, mlxtend 0.23.1, numpy, pandas |
| Tests | pytest 9.x — 155 tests (127 unitaires ML + 17 intégration API + 15 sécurité RBAC + 12 RBAC rôles), CI/CD GitHub Actions |
| Infrastructure | PythonAnywhere (production académique) + Docker Compose (cible V2) + GitHub Actions CI/CD |
| Observabilité | Sentry (optionnel, via `SENTRY_DSN`), logs Flask structurés, endpoint `/health` |
| Tâches planifiées | Threads Python (à chaud) + script cron PythonAnywhere `cron_train_all.py` (nuit) |
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
