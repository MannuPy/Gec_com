# Plan du Rapport de Fin d'Études
## UVBF — Licence en Génie Logiciel, Option : Analyse de Données
### Projet : GesCom-BF — Système SaaS de Gestion Commerciale Multi-Sites

---

> **Dernière mise à jour :** 1er juillet 2026 — conformité code v2 post-corrections soutenance.

---

> **Conventions UVBF observées dans les rapports de référence :**
> - Chaque chapitre s'ouvre par une **Introduction** et se ferme par une **Conclusion**
> - Le pronom **« Nous »** est utilisé (style académique collectif)
> - La présentation de l'**UVBF** et de la **structure d'accueil** est obligatoire en chapitre 1
> - Les diagrammes UML sont requis en conception (Use Case, Séquence, Classes)
> - Un chapitre dédié à la **méthodologie d'analyse de données** est attendu (spécialité)
> - Un chapitre **Présentation, Analyse et Interprétation des Résultats** valorise la spécialité
> - Volume cible : **50–80 pages** hors annexes (format licence, plus court que master)

---

## PAGES LIMINAIRES

| Élément | Détail |
|---|---|
| **Page de garde** | Logo UVBF + Ministère, titre du mémoire, filière/spécialité, nom de l'étudiant, directeur de mémoire, maître de stage, jury, année académique 2024-2025 |
| **Dédicace** | 1 page |
| **Remerciements** | UVBF (administration, coordinateur filière), directeur de mémoire, maître de stage, membres du jury, famille |
| **Résumé** | 150–200 mots en français — problème, solution, technologies, résultats clés. Mots-clés (5–7) |
| **Abstract** | Traduction anglaise du résumé. Keywords |
| **Liste des sigles et abréviations** | API, SaaS, JWT, RBAC, ORM, ML, RFM, CLV, ABC/XYZ, UML, MVC, SGBD… |
| **Liste des figures** | Toutes les captures, diagrammes, graphiques numérotés |
| **Liste des tableaux** | Tableaux de comparaison, de résultats, de métriques |
| **Table des matières** | Générée automatiquement |

---

## INTRODUCTION GÉNÉRALE
*(2–3 pages)*

- **Contexte** : la transformation numérique des PME et commerces au Burkina Faso ; besoins en outils de pilotage multi-sites
- **Problématique** : Comment concevoir un système de gestion commerciale SaaS intégrant des fonctionnalités avancées d'analyse de données pour aider les gestionnaires burkinabè à prendre de meilleures décisions ?
- **Objectifs du projet** :
  - Développer une application web SaaS de gestion commerciale multi-sites
  - Intégrer un module d'analyse de données et d'intelligence artificielle actionnable
- **Organisation du rapport** : brève présentation de chaque chapitre

---

## CHAPITRE 1 : GENERALITES
*(8–12 pages)*

**Introduction**

### 1.1. Présentation de l'Université Virtuelle du Burkina Faso (UVBF)
- Création, statut, mission
- Cycles de formation : BTS, Licence, Master
- Filières des Sciences du Numérique (Génie logiciel, Cybersécurité, IA)
- Engagement pour l'innovation et l'enseignement à distance

### 1.2. Présentation de la structure d'accueil
- **1.2.1. Historique et création** : présentation de l'entreprise/structure qui a accueilli le stage
- **1.2.2. Missions et services proposés** : activités, clientèle cible
- **1.2.3. Organisation interne** : organigramme, services, équipe technique

**Conclusion**

---

## CHAPITRE 2 : CONTEXTE GENERAL ET PROBLEMATIQUE
*(10–14 pages)*

**Introduction**

### 2.1. Présentation du projet GesCom-BF
- **2.1.1. Contexte** : gestion commerciale manuelle ou fragmentée dans les PME burkinabè ; multiplication des points de vente ; besoin de visibilité temps réel
- **2.1.2. Problématique** : absence d'outil centralisé multi-sites intégrant ventes, stocks, crédits, comptabilité et analyse de données
- **2.1.3. Objectifs du système** :
  - Centraliser la gestion de tous les modules commerciaux
  - Permettre le contrôle multi-sites et multi-rôles
  - Fournir des tableaux de bord et des analyses prédictives actionnables
- **2.1.4. Acteurs du projet** : directeur de mémoire, maître de stage, étudiant stagiaire

### 2.2. Analyse des besoins

**2.2.1. Besoins fonctionnels** — par module :

| Module | Fonctionnalités principales |
|---|---|
| Authentification & RBAC | Connexion sécurisée, gestion des rôles (Super Admin, Admin, Manager, Vendeur, Comptable) |
| Ventes | Enregistrement, historique, remises, reçus |
| Stocks | Suivi temps réel, alertes seuil minimum, mouvements |
| Crédits clients | Octroi, suivi du remboursement, historique des paiements |
| Remboursements | Workflow approbation/rejet, suivi des avoirs |
| Comptabilité | Journal de caisse, bilan recettes/dépenses par période |
| Rapports & Exports | Tableaux de bord, exports PDF/XLSX, streaming temps réel |
| Analytique & IA | Prévision demande, scoring crédit, anomalies, RFM, ABC/XYZ, CLV, cohortes |

**2.2.2. Besoins non fonctionnels** :
- Disponibilité SaaS (accès web 24/7)
- Performance : temps de réponse < 500 ms sur les endpoints courants
- Sécurité : authentification JWT, chiffrement, RBAC par rôle et par branche
- Portabilité : déploiement sur hébergement mutualisé (PythonAnywhere)
- Maintenabilité : architecture modulaire (Blueprints Flask)

### 2.3. Démarche méthodologique

**2.3.1. Méthodologie de développement** : approche itérative — analyse des besoins → conception UML → développement par modules → tests → déploiement

**2.3.2. Langage de modélisation** : UML 2.x — diagrammes de cas d'utilisation, de séquence et de classes pour structurer la conception

**2.3.3. Planning prévisionnel** (Diagramme de Gantt) :

| Phase | Durée |
|---|---|
| Analyse des besoins | Semaine 1–2 |
| Conception UML et architecture | Semaine 3–4 |
| Développement backend (Flask/API) | Semaine 5–8 |
| Développement frontend (React) | Semaine 7–10 |
| Intégration des modules ML | Semaine 9–11 |
| Tests, corrections, déploiement | Semaine 12–13 |
| Rédaction du rapport | Semaine 11–14 |

**Conclusion**

---

## CHAPITRE 3 : ANALYSE ET CONCEPTION DU SYSTEME
*(12–18 pages)*

**Introduction**

### 3.1. Étude de l'existant
- **3.1.1. Solutions existantes** : analyse comparative des outils disponibles (Odoo, QuickBooks, Sage, solutions locales)

| Outil | Type | Points forts | Limites pour le contexte local |
|---|---|---|---|
| Odoo | ERP open-source | Complet, modulaire | Lourd, coûteux, pas de ML intégré |
| QuickBooks | SaaS propriétaire | Simple d'utilisation | Non adapté à l'Afrique de l'Ouest |
| Sage | ERP propriétaire | Standard africain | Licence onéreuse, pas d'analytique |
| Gestion manuelle (Excel) | — | Faible coût | Pas de temps réel, pas de multi-sites |

- **3.1.2. Critique de l'existant** : lacunes en multi-sites, absence d'analytique, manque de contrôle des accès par rôle
- **3.1.3. Solution proposée** : GesCom-BF — SaaS léger, modulaire, avec couche analytique ML

### 3.2. Architecture globale du système
- **3.2.1. Architecture de déploiement** : navigateur React (SPA) ↔ API Flask REST ↔ MySQL (PythonAnywhere)
- **3.2.2. Architecture logique** : séparation en couches — Routes (Blueprint) / Services / Modèles (ORM) / ML
- Schéma d'architecture global

### 3.3. Diagrammes UML

**3.3.1. Diagramme de cas d'utilisation global**
- Acteurs : Super Admin, Admin, Manager, Vendeur, Comptable
- Cas d'utilisation principaux par module
- Description détaillée d'un cas d'utilisation (ex. : « Enregistrer une vente »)

**3.3.2. Diagramme de séquence**
- Description d'un flux de bout en bout (ex. : authentification JWT ou enregistrement d'une vente)
- Interactions : Navigateur → API Flask → SQLAlchemy → MySQL

**3.3.3. Diagramme de classes**
- Classes principales : `User`, `Branch`, `Product`, `Sale`, `SaleItem`, `Credit`, `Refund`, `MLModel`, `Prediction`
- Relations, attributs clés, multiplicités

### 3.4. Conception de la base de données
- Schéma Entité-Association (E/A) simplifié
- Tables principales et leurs rôles
- Feature Store : `fs_customer_rfm`, `fs_customer_credit_features`, `fs_transaction_features` — principe et utilité
- Indexation pour les performances (colonnes de jointure, filtres temporels)

### 3.5. Conception de l'API REST
- Convention de nommage : `/api/v1/<module>/<ressource>`
- Authentification : JWT (access token + refresh token)
- Contrôle d'accès : décorateur `@require_permission` avec matrice RBAC
- Sérialisation : schémas marshmallow (validation + transformation)

**Conclusion**

---

## CHAPITRE 4 : REALISATION ET IMPLEMENTATION
*(12–16 pages)*

**Introduction**

### 4.1. Environnement de travail
**4.1.1. Frameworks et langages utilisés** :

| Couche | Technologie | Rôle |
|---|---|---|
| Backend | Python 3.11 + Flask 3.0.3 | Serveur API REST |
| ORM | SQLAlchemy 2.x + marshmallow | Accès BD + sérialisation |
| Frontend | React 18 + TypeScript + Vite | Interface utilisateur SPA |
| Gestion d'état | TanStack Query + Zustand | Cache serveur + état client |
| Visualisation | Recharts | Graphiques et tableaux de bord |
| Style | Tailwind CSS | Design responsive |
| Base de données | MySQL 8 | Persistance des données |
| ML | scikit-learn + mlxtend + shap | Modèles d'apprentissage automatique + Market Basket + Explicabilité |

**4.1.2. Environnement logiciel** : VS Code, Git/GitHub, Postman, pytest

**4.1.3. Environnement matériel** : tableau récapitulatif (poste de développement, serveur de production)

### 4.2. Implémentation des modules fonctionnels
Pour chaque module clé : endpoint principal, logique de traitement, capture d'écran.

- **4.2.1. Authentification et sécurité** : JWT, hachage bcrypt, protection CORS, révocation via table SQL `token_blocklist` (pas Redis), `must_change_password` (RF-05 ✅ validé serveur : 403 `PASSWORD_CHANGE_REQUIRED`), rate-limiting Flask-Limiter 3.8.0 `memory://`
- **4.2.2. Module Ventes** : enregistrement transactionnel, mise à jour stock en temps réel, `approved_by_id` obligatoire si `discount_rate > 0` (RF-16/RG-23 ✅ validé serveur : 422)
- **4.2.3. Module Stocks** : suivi par branche, alertes seuil minimum
- **4.2.4. Module Crédits** : octroi, suivi du remboursement, workflow de paiement
- **4.2.5. Module Rapports** : exports PDF/XLSX, tableau de bord (SSE désactivé sur PythonAnywhere — `DISABLE_SSE=true` — fallback polling)

### 4.3. Politique de sécurité
- Sécurité du serveur : HTTPS, variables d'environnement, clés secrètes
- Sécurité de l'application : RBAC, validation des entrées, protection contre l'injection SQL (ORM)

### 4.4. Présentation de quelques captures de l'application
- Page de connexion, tableau de bord principal, module ventes, module stocks, page analytique

### 4.5. Estimation du coût de réalisation

| Ressource | Coût estimé |
|---|---|
| Hébergement PythonAnywhere (annuel) | X FCFA |
| Nom de domaine | X FCFA |
| Outils de développement (open-source) | 0 FCFA |
| Temps de développement (valorisé) | X FCFA |
| **Total** | **X FCFA** |

**Conclusion**

---

## CHAPITRE 5 : METHODOLOGIE D'ANALYSE DE DONNEES
*(10–14 pages — spécialité Analyse de Données)*

**Introduction**

> Ce chapitre présente la démarche analytique adoptée pour transformer les données commerciales brutes en informations actionnables.

### 5.1. Cadre de l'analyse de données dans GesCom-BF
- Problématique analytique : comment extraire de la valeur décisionnelle des données transactionnelles ?
- Pipeline général : Collecte → Stockage → Feature Engineering → Modélisation → Présentation

### 5.2. Sources et nature des données
- **5.2.1. Données transactionnelles** : ventes, stocks, crédits, remboursements, caisse
- **5.2.2. Feature Store** : tables matérialisées `fs_customer_rfm`, `fs_customer_credit_features`, `fs_transaction_features` — rôle et mode de mise à jour
- **5.2.3. Variables d'analyse** :

| Variable | Type | Source | Utilisation |
|---|---|---|---|
| montant_total | Quantitative continue | Table `sales` | Tendances CA, anomalies |
| quantite_vendue | Quantitative discrète | Table `sale_items` | Prévision demande, ABC |
| taux_remboursement | Quantitative continue | Table `credits` | Scoring crédit |
| recency / frequency / monetary | Quantitatives | Feature Store RFM | Segmentation clients |
| heure_vente | Quantitative discrète | Table `sales` | Détection anomalies |

### 5.3. Méthodes et algorithmes utilisés
- **5.3.1. Prévision de la demande** : Régression Linéaire (trend + variables dummy jour-de-semaine) ; fallback naïf saisonnier ; `data_confidence` inclus dans la réponse ✅
- **5.3.2. Segmentation RFM** : K-Means avec K-optimal déterminé par méthode Silhouette/Elbow (`/analytics/rfm-segments/evaluate-k`) ✅
- **5.3.3. Scoring crédit** : Random Forest Classifier (100 arbres, 8 features) ; fallback règles déterministes ; SHAP explicabilité (`shap.TreeExplainer`) endpoint `/analytics/credit-scores/<id>/explain` ✅
- **5.3.4. Détection d'anomalies** : Isolation Forest (contamination = 2 %) ; fallback Z-Score
- **5.3.5. Classification ABC/XYZ** : cumsum Pareto (ABC) + coefficient de variation hebdomadaire (XYZ) — méthodes statistiques pures (pas de ML)
- **5.3.6. Analyse de cohortes** : taux de rétention mensuel par cohorte de première transaction
- **5.3.7. Valeur Vie Client (CLV)** : modèle simplifié `panier_moyen × fréquence_mensuelle × durée_vie_estimée`
- **5.3.8. Market Basket Analysis** ✅ : algorithme Apriori (mlxtend), endpoint `/analytics/basket`
- **5.3.9. Price Elasticity** ✅ : pandas, endpoint `/analytics/price-elasticity`
- **5.3.10. Churn Probability** ✅ : Logistic Regression, endpoint `/analytics/churn-risk`
- **5.3.11. African Context Indicators** ✅ : saisonnalité BF (Tabaski, saison des pluies, rentrée scolaire…), endpoint `/analytics/african-context`

### 5.4. Métriques d'évaluation des modèles

| Modèle | Métriques d'évaluation |
|---|---|
| Prévision de la demande | MAE (erreur absolue moyenne), RMSE |
| Scoring crédit | Accuracy, F1-score, AUC-ROC |
| Détection d'anomalies | Taux de contamination, précision estimée |
| Segmentation K-Means | Inertie, score de silhouette |

### 5.5. Stratégie de dégradation gracieuse
- Condition d'activation des modèles ML : données suffisantes + scikit-learn disponible
- Fallback automatique si conditions non remplies : algorithmes déterministes ou statistiques simples
- Avantage : système toujours opérationnel même en cas d'insuffisance de données

### 5.6. Gestion du cycle de vie des modèles
- Registre de modèles : table `ml_models` (type, version, algorithme, métriques, is_active)
- Table `predictions` : stockage des prédictions par entité
- Versionning : conservation des 3 dernières versions, purge automatique des anciennes
- Entraînement : threads Python natifs pour l'entraînement ML à la demande + script `scripts/cron_train_all.py` planifié via PythonAnywhere Tasks (pas Celery/Redis)
- 10 migrations Alembic dans `backend/migrations/versions/`

**Conclusion**

---

## CHAPITRE 6 : PRESENTATION, ANALYSE ET INTERPRETATION DES RESULTATS
*(10–14 pages — valorise la spécialité Analyse de Données)*

**Introduction**

### 6.1. Résultats de la prévision de la demande
- Graphique : courbe historique vs courbe prédite (J+7, J+30)
- Tableau : MAE et RMSE par produit / catégorie
- Analyse : produits avec forte saisonnalité vs produits stables
- Alertes générées : `stock_prévu_J7 < 0` → recommandation de réapprovisionnement

### 6.2. Résultats de la segmentation RFM des clients
- Répartition des clients par segment (CHAMPIONS, RÉGULIERS, À RISQUE, OCCASIONNELS)
- Graphique : scatter plot Recency × Monetary coloré par segment
- Tableau : effectif, panier moyen, fréquence moyenne par segment
- Interprétation : identification des clients à risque de churn, actions recommandées

### 6.3. Résultats du scoring crédit
- Distribution des scores de crédit (0–100) par niveau de risque (FAIBLE / MOYEN / ÉLEVÉ)
- Importance des variables (Random Forest feature importance) : quelles features sont les plus prédictives ?
- Tableau : confusion matrix (si données d'évaluation disponibles)
- Utilisation opérationnelle : aide à la décision pour l'octroi de crédit

### 6.4. Résultats de la détection d'anomalies
- Nombre d'anomalies détectées sur la période d'analyse
- Graphique : scatter plot montant × taux de remise, anomalies mis en évidence
- Tableau : top 10 transactions anormales avec verbatim des raisons (remise excessive, heure atypique, écart produit)
- Interprétation : patterns d'anomalie détectés, actions de contrôle suggérées

### 6.5. Résultats de la classification ABC/XYZ
- Matrice 3×3 : répartition des produits par classe (AX, AY, AZ, BX… CZ)
- Tableau : nombre de produits par classe, contribution au CA
- Stock mort identifié : produits sans vente sur la période (classe C/Z, `dead_stock=True`)
- Recommandations de gestion des stocks par classe

### 6.6. Analyse de cohortes et valeur vie client
- Heatmap de rétention : cohortes (mois) × décalage temporel
- Taux de rétention à 1, 3, 6 mois par cohorte
- CLV moyenne par segment de clientèle
- Identification des cohortes à fort taux de churn

### 6.7. Synthèse des résultats analytiques

| Module ML | Algorithme activé | Résultat principal | Valeur opérationnelle |
|---|---|---|---|
| Prévision demande | Régression Linéaire | MAE = X unités | Alerte stock, recommandation réappro |
| Segmentation RFM | K-Means (k=4) | X% clients CHAMPIONS | Ciblage commercial personnalisé |
| Scoring crédit | Random Forest | X% clients risque ÉLEVÉ | Aide à l'octroi de crédit |
| Anomalies | Isolation Forest | X transactions suspectes | Contrôle fraude et erreurs |
| ABC/XYZ | Méthode statistique | X produits classe A | Priorité de réapprovisionnement |
| CLV | Modèle simplifié | CLV moyenne = X FCFA | Priorisation commerciale |

**Conclusion**

---

## CHAPITRE 7 : DISCUSSION, LIMITES ET RECOMMANDATIONS
*(6–8 pages)*

**Introduction**

### 7.1. Discussion des résultats
- Mise en perspective des résultats analytiques avec les objectifs initiaux
- Comparaison avec la littérature : nos résultats RFM / Isolation Forest sont-ils cohérents avec les travaux publiés ?
- Apport de la couche analytique vs gestion commerciale classique sans IA

### 7.2. Limites du système développé
- **Volume de données** : faible historique en phase de démarrage → modèles ML activés sur peu d'observations
- **Hébergement mutualisé** : PythonAnywhere sans WebSockets natifs → SSE désactivé (`DISABLE_SSE=true`), fallback polling ✅ résolu
- **Entraînement ML asynchrone** : remplacé par threads Python natifs + `scripts/cron_train_all.py` PythonAnywhere Tasks ✅ résolu (Celery/Redis supprimés)
- **Absence de labels** pour la détection d'anomalies : évaluation de la précision difficile (apprentissage non supervisé)
- **Biais du fallback crédit** : hachage SHA-256 supprimé — affichage "données insuffisantes" si historique trop court ✅ résolu
- **Données d'entraînement internes** : pas de données externes (marché, météo, événements) intégrées dans les modèles (indicateurs de contexte africain partiellement couverts via `/analytics/african-context`)

### 7.3. Recommandations et perspectives
- **Court terme** : enrichir l'historique de données pour améliorer la précision des modèles ; ajouter l'authentification 2FA ; migration VPS avec PostgreSQL comme cible future
- **Moyen terme** : MLflow pour le tracking d'expériences ; application mobile PWA offline-first
- **Long terme** : modèles de prévision avancés (Prophet avec davantage d'historique déjà `data_confidence` intégré, LSTM) ; recommandation de prix dynamique ; intégration comptabilité SYSCOHADA

**Conclusion**

---

## CONCLUSION GENERALE
*(2–3 pages)*

- **Bilan** : rappel de la problématique et synthèse de ce qui a été accompli (système complet, 11 modules analytiques dont Market Basket/Price Elasticity/Churn/African Context/SHAP, 155 tests — 127 unitaires ML + 17 intégration API + 15 sécurité RBAC + 12 rôles RBAC — pipeline CI bloquant)
- **Contribution** : apport de la double compétence Génie Logiciel + Analyse de Données — un ERP-léger SaaS avec intelligence décisionnelle intégrée
- **Difficultés surmontées** : architecture multi-modules, gestion du multi-sites, intégration ML avec dégradation gracieuse
- **Enseignements personnels** : compétences développées, posture d'ingénieur-analyste
- **Ouverture** : GesCom-BF comme point de départ d'une solution plus large pour la digitalisation des PME burkinabè

---

## BIBLIOGRAPHIE / WEBOGRAPHIE

**Ouvrages de référence**
- Géron, A. (2022). *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow* (3e éd.). O'Reilly Media.
- Martin, R. C. (2017). *Clean Architecture*. Prentice Hall.
- Grinberg, M. (2018). *Flask Web Development* (2e éd.). O'Reilly Media.

**Articles scientifiques**
- Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). Isolation Forest. *Proceedings of ICDM 2008*, IEEE.
- Breiman, L. (2001). Random Forests. *Machine Learning*, 45(1), 5–32.
- Gupta, S. & Zeithaml, V. (2006). Customer Metrics and Their Impact on Financial Performance. *Marketing Science*, 25(6), 718–739.

**Documentation technique**
- Flask : https://flask.palletsprojects.com
- SQLAlchemy : https://docs.sqlalchemy.org
- React : https://react.dev
- scikit-learn : https://scikit-learn.org
- Recharts : https://recharts.org
- TanStack Query : https://tanstack.com/query

---

## ANNEXES

| Annexe | Contenu |
|---|---|
| A | Schéma complet de la base de données |
| B | Dictionnaire de données |
| C | Catalogue des endpoints API (méthode, URL, paramètres, réponse type) |
| D | Captures d'écran de toutes les pages principales de l'application |
| E | Extraits de code commentés (modules ML, décorateur RBAC, génération exports) |
| F | Résultats des tests — 155 tests (127 unitaires ML + 17 intégration API + 15 sécurité RBAC + 12 rôles RBAC) — rapport pytest, rapport `tsc --noEmit` |
| G | Guide d'installation et de déploiement |

---

## Récapitulatif du volume cible

| Chapitre | Volume estimé |
|---|---|
| Pages liminaires | 5–7 pages |
| Introduction générale | 2–3 pages |
| Chapitre 1 — Généralités | 8–12 pages |
| Chapitre 2 — Contexte et problématique | 10–14 pages |
| Chapitre 3 — Analyse et conception | 12–18 pages |
| Chapitre 4 — Réalisation | 12–16 pages |
| **Chapitre 5 — Méthodologie analyse de données** | **10–14 pages** |
| **Chapitre 6 — Résultats et interprétation** | **10–14 pages** |
| Chapitre 7 — Discussion et recommandations | 6–8 pages |
| Conclusion générale | 2–3 pages |
| Bibliographie + Annexes | 8–15 pages |
| **TOTAL** | **~85–124 pages** |

---

*Plan basé sur les rapports de référence UVBF (Génie Logiciel et Analyse de Données) — GesCom-BF, Année académique 2024-2025*
