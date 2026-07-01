# CONCLUSION GÉNÉRALE ET PERSPECTIVES

---

## Bilan des objectifs atteints

Ce mémoire avait pour ambition de concevoir, développer et déployer un système de gestion commerciale adapté aux réalités des petites et moyennes entreprises burkinabè du secteur de la quincaillerie et des pièces détachées. La question centrale posée en introduction était la suivante :

> *Comment doter les PME commerciales du Burkina Faso d'un outil de gestion centralisé, fiable, accessible hors connexion, et capable de transformer leurs données de vente en aide à la décision ?*

Au terme de ce travail, **GesCom-BF répond concrètement à cette problématique** sur quatre dimensions :

**Centralisation et traçabilité.** Le système gère en temps réel les stocks du dépôt central et de chaque boutique de vente, les transferts inter-sites avec double validation, les ventes avec remises encadrées par rôle, et les réceptions fournisseurs — le tout dans une base de données unique, partagée et cohérente. La dispersion des informations dans des cahiers et des fichiers Excel non synchronisés, identifiée comme le premier problème du secteur, est directement adressée.

**Accessibilité hors connexion.** Le mode PWA (Progressive Web App) avec IndexedDB et Background Sync permet aux vendeurs d'enregistrer des ventes même en l'absence de connexion internet. La réconciliation des données à la reconnexion est gérée automatiquement, avec un mécanisme de résolution des conflits de stock qui maintient l'humain dans la boucle plutôt que d'appliquer des règles automatiques potentiellement erronées.

**Aide à la décision par l'IA.** Sept modules analytiques fournissent aux gérants des informations qu'aucune solution générique ne leur offrait : prévision de la demande avec Prophet (calibré sur les jours fériés burkinabè), détection automatique des ventes anormales, segmentation RFM des clients, scoring crédit avec explication SHAP, associations de produits pour le cross-selling, et indicateurs de contexte propres à l'environnement commercial africain (stress de trésorerie, crédit informel, événements calendriers).

**Qualité et maintenabilité.** Le système est couvert par 93 tests unitaires automatisés, intégrés dans un pipeline CI/CD qui bloque tout déploiement régressif. Les migrations de schéma sont versionnées (23 fichiers Alembic). Le code est structuré en blueprints modulaires côté backend et en composants React typés côté frontend. Cette architecture rend le projet transmissible et évolutif.

Le tableau suivant résume l'atteinte des objectifs SMART définis au chapitre 1 :

**Tableau 15 — Bilan des objectifs SMART**

| Ref. | Objectif | Cible | Résultat | Statut |
|------|----------|-------|----------|--------|
| O1 | Centraliser stock dépôt + boutiques | 100 % des mouvements tracés | Implémenté — audit log complet | ✅ |
| O2 | Mode hors-ligne opérationnel | Ventes enregistrables sans internet | PWA + Background Sync actif | ✅ |
| O3 | Contrôle des accès RBAC | 3 rôles avec permissions granulaires | Admin / Magasinier / Vendeur actifs | ✅ |
| O4 | Double tarification | Prix client / prix technicien | Implémenté par produit | ✅ |
| O5 | Module IA — prévision demande | Fallback si données < 30 j | 3 niveaux de fallback + `data_confidence` | ✅ |
| O6 | Déploiement production | Application accessible en HTTPS | PythonAnywhere actif, HTTPS natif | ✅ |
| O7 | Documentation technique | 34 documents techniques | 34 documents produits | ✅ |
| O8 | Couverture de tests | ≥ 90 tests, 0 échec | **93/93 pytest ✅** | ✅ |

---

## Limites du projet (honnêteté)

Un bilan académique rigoureux impose de nommer clairement ce que le projet ne fait pas, ou fait imparfaitement.

**Données de démonstration.** L'ensemble du système a été développé et testé sur des données générées par un script de seed (`scripts/seed_demo.py`). Aucun client réel n'utilise encore GesCom-BF en production commerciale. Les performances des modèles ML (accuracy, F1-score, MAPE) sont donc cohérentes sur données synthétiques, mais ne peuvent pas être validées sur des comportements d'achat réels. Ce point est la limite la plus significative du projet à ce stade.

**Multi-tenant partiel.** L'architecture SaaS multi-tenant est conçue (colonne `tenant_id` sur toutes les tables, middleware d'isolation) et documentée, mais un seul tenant est déployé pour la démonstration. La bascule vers un déploiement multi-tenant réel — avec isolation forte schema-per-tenant sur PostgreSQL — est prévue pour la V2 mais n'a pas été activée en production.

**Rate limiting sans persistance.** Flask-Limiter est configuré en `memory://` en l'absence de Redis sur PythonAnywhere. Les compteurs de tentatives de connexion se réinitialisent au redémarrage du serveur. Cette configuration est acceptable pour une démonstration, pas pour un déploiement en charge réelle.

**Modèles ML sans labels réels.** Le scoring crédit et la détection d'anomalies sont entraînés sur des données simulées. En production, ces modèles nécessiteraient une phase de collecte de labels réels (quelles ventes étaient effectivement frauduleuses ? quels clients ont effectivement fait défaut ?) pour être calibrés correctement — une démarche qui dépasse le périmètre d'un projet de mémoire.

**Interface non auditée en accessibilité.** L'interface React répond aux critères fonctionnels mais n'a pas fait l'objet d'un audit WCAG (accessibilité web). Dans un contexte d'usage par des opérateurs de terrain en Afrique subsaharienne, l'accessibilité sur petits écrans et faible bande passante mériterait une attention spécifique.

---

## Perspectives V2

GesCom-BF est conçu comme une V1 fonctionnelle, pas comme un produit fini. Les perspectives de V2 sont documentées et priorisées :

### Application mobile native

La PWA couvre le besoin offline pour les vendeurs en boutique sur smartphone. Elle ne couvre pas les cas d'usage terrain : commerciaux en déplacement chez des clients, livraisons avec scan de codes-barres, prise de commande en déplacement. Une application React Native (partageant la couche API et les types TypeScript avec le frontend web) permettrait de couvrir ces scénarios avec une expérience utilisateur native (caméra, notifications push, géolocalisation).

### Intégration Mobile Money (Orange Money / Moov Money)

Au Burkina Faso, les paiements par Mobile Money (Orange Money, Moov Money) sont massivement utilisés pour les transactions commerciales. L'intégration de ces APIs de paiement — Orange Money API (USSD push), Moov Money API — permettrait d'enregistrer automatiquement les paiements reçus, de réconcilier les encaissements avec les ventes, et de générer des reçus de paiement numériques. Cette fonctionnalité est la plus demandée lors des présentations du projet aux professionnels du secteur.

### Multi-tenant complet (schema-per-tenant)

La V2 prévoit une migration vers PostgreSQL avec isolation schema-per-tenant : chaque entreprise cliente obtient un schéma dédié dans la base de données, garantissant une isolation forte des données et la possibilité de personnaliser le schéma par tenant (catégories produits spécifiques, règles de remise propres à chaque entreprise). Le déploiement VPS avec Docker Compose (Nginx + Gunicorn + PostgreSQL + Redis + Celery) est déjà documenté dans les documents d'architecture du projet.

### Amélioration des modèles ML avec données réelles

Une fois le système en production réelle (3 à 6 mois de données), plusieurs améliorations ML deviennent possibles : remplacement du modèle de churn heuristique par un vrai modèle supervisé (Pareto/NBD ou BG/NBD) une fois les labels disponibles ; calibration du scoring crédit sur des historiques de remboursement réels ; optimisation des paramètres Apriori (min_support, min_confidence) sur les véritables paniers du secteur ; et extension de Prophet à d'autres granularités temporelles (prévision hebdomadaire, mensuelle).

### Module de comptabilité simplifiée

Hors périmètre en V1, un module de comptabilité simplifiée (journal des encaissements, état des dettes fournisseurs, tableau de trésorerie) est envisageable comme extension V2. Il ne s'agit pas de concurrencer un logiciel comptable dédié (Sage Comptabilité, QuickBooks), mais de fournir aux gérants une vision trésorerie directement liée à leurs données de vente et d'achat déjà dans GesCom-BF.

---

## Mot de clôture

GesCom-BF illustre qu'il est possible, dans le cadre d'un projet académique individuel de niveau Master, de produire un système logiciel complet, déployé, testé et documenté — à condition de faire des choix techniques justifiés, de respecter une architecture modulaire depuis le début, et d'être honnête sur ce qui fonctionne et ce qui reste à faire.

La valeur de ce projet ne réside pas dans sa complexité algorithmique, mais dans sa cohérence d'ensemble : une analyse des besoins ancrée dans la réalité du terrain burkinabè, une architecture qui répond aux contraintes d'infrastructure locales (connectivité intermittente, budget limité, pas de Redis), des modules IA contextualisés plutôt que génériques, et une démarche de qualité qui rend le système transmissible.

---

# BIBLIOGRAPHIE

---

## Ouvrages et manuels

[1] **Sommerville, I.** (2016). *Software Engineering* (10e éd.). Pearson Education. — Référence pour l'ingénierie logicielle, les processus de développement et la gestion de la qualité.

[2] **Pressman, R. S., & Maxim, B. R.** (2020). *Software Engineering: A Practitioner's Approach* (9e éd.). McGraw-Hill. — Méthodologie de développement, gestion des exigences, tests.

[3] **Fowler, M.** (2018). *Refactoring: Improving the Design of Existing Code* (2e éd.). Addison-Wesley. — Principes de refactorisation et de maintenabilité du code.

[4] **Géron, A.** (2023). *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow* (3e éd.). O'Reilly Media. — Référence pratique pour les algorithmes ML utilisés : Random Forest, Isolation Forest, K-Means.

[5] **Molnar, C.** (2022). *Interpretable Machine Learning: A Guide for Making Black Box Models Explainable* (2e éd.). Disponible en ligne : https://christophm.github.io/interpretable-ml-book/ — Référence théorique pour l'explicabilité SHAP et les modèles interprétables.

[6] **Taylor, S. J., & Letham, B.** (2018). Forecasting at scale. *The American Statistician*, 72(1), 37–45. — Article fondateur de Prophet, modèle de prévision utilisé dans GesCom-BF.

[7] **Agrawal, R., & Srikant, R.** (1994). Fast algorithms for mining association rules. *Proceedings of the 20th VLDB Conference*, 487–499. — Article fondateur de l'algorithme Apriori utilisé dans le module Market Basket.

[8] **Liu, F. T., Ting, K. M., & Zhou, Z.-H.** (2008). Isolation Forest. *Proceedings of the 8th IEEE International Conference on Data Mining (ICDM)*, 413–422. — Article fondateur d'Isolation Forest, utilisé pour la détection d'anomalies.

[9] **Breiman, L.** (2001). Random Forests. *Machine Learning*, 45(1), 5–32. — Article fondateur de Random Forest, utilisé pour le scoring crédit.

[10] **Lundberg, S. M., & Lee, S.-I.** (2017). A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems (NIPS)*, 30. — Papier fondateur de SHAP (SHapley Additive exPlanations).

---

## Articles et rapports sectoriels

[11] **Banque Mondiale.** (2022). *Doing Business 2022 : Burkina Faso*. Washington D.C. : Groupe de la Banque Mondiale. — Données sur l'environnement des affaires au Burkina Faso (accès au crédit, formalisation des PME).

[12] **OCDE / SWAC.** (2020). *Dynamiques du développement en Afrique de l'Ouest : Numérique, commerce et développement*. OCDE Publishing. — Contexte de la transformation numérique des PME en Afrique subsaharienne.

[13] **Institut National de la Statistique et de la Démographie (INSD).** (2021). *Enquête sur les technologies de l'information et de la communication dans les entreprises burkinabè*. Ouagadougou : INSD. — Données sur la pénétration des outils numériques dans les PME du Burkina Faso.

[14] **GSMA Intelligence.** (2023). *The Mobile Economy Sub-Saharan Africa 2023*. GSMA. — Données sur la pénétration mobile et le Mobile Money en Afrique subsaharienne.

---

## Documentation technique officielle

[15] **Pallets Projects.** (2024). *Flask Documentation* (v3.0). https://flask.palletsprojects.com/ — Documentation officielle du framework web Flask utilisé côté backend.

[16] **SQLAlchemy Authors.** (2024). *SQLAlchemy Documentation* (v2.0). https://docs.sqlalchemy.org/ — ORM et couche d'accès aux données du projet.

[17] **React Team.** (2024). *React Documentation* (v18). https://react.dev/ — Documentation officielle du framework frontend.

[18] **Meta Open Source.** (2024). *Prophet Documentation*. https://facebook.github.io/prophet/ — Documentation officielle de la librairie Prophet.

[19] **scikit-learn Developers.** (2024). *scikit-learn: Machine Learning in Python* (v1.5). https://scikit-learn.org/ — Documentation de Random Forest, Isolation Forest, K-Means, métriques.

[20] **SHAP Developers.** (2024). *SHAP Documentation* (v0.45). https://shap.readthedocs.io/ — Documentation officielle de la librairie SHAP.

[21] **Rasbt, S. & Contributors.** (2024). *mlxtend Documentation* (v0.23). https://rasbt.github.io/mlxtend/ — Documentation de l'implémentation Apriori utilisée.

[22] **MLflow Authors.** (2024). *MLflow Documentation* (v2.14). https://mlflow.org/docs/latest/ — Documentation du système de tracking et versioning des modèles ML.

[23] **Google Developers.** (2024). *Progressive Web Apps*. https://web.dev/progressive-web-apps/ — Référence pour les PWA, Service Workers et Background Sync API.

[24] **Alembic Authors.** (2024). *Alembic Documentation* (v1.13). https://alembic.sqlalchemy.org/ — Outil de migration de schéma SQLAlchemy utilisé dans le projet.

[25] **Sentry, Inc.** (2024). *Sentry Documentation — Flask Integration*. https://docs.sentry.io/platforms/python/integrations/flask/ — Intégration Sentry pour la surveillance des erreurs en production.

---

## Méthodologies

[26] **Roques, P., & Vallée, F.** (2011). *UML 2 en action : De l'analyse des besoins à la conception* (5e éd.). Eyrolles. — Référence pour la modélisation UML utilisée au chapitre 2 (cas d'utilisation, diagrammes de classes, séquence).

[27] **Schwaber, K., & Sutherland, J.** (2020). *The Scrum Guide*. https://scrumguides.org/ — Référence officielle de la méthode Scrum appliquée dans la gestion du projet (12 sprints, product backlog).

[28] **Roques, P.** (2004). *Ingénierie des systèmes : la méthode 2TUP*. Hermes Science Publications. — Référence pour la méthode 2TUP (Two Track Unified Process) adoptée pour la phase d'analyse et de modélisation.

---

# ANNEXES

---

## Annexe A — Extrait du schéma de base de données

Le schéma complet comporte 21 tables. Les tables centrales sont présentées ci-dessous avec leurs colonnes principales et leurs relations.

### A.1 Tables principales et relations

```
┌─────────────────────────────────┐
│           tenants               │
├─────────────────────────────────┤
│ id          INT PK              │
│ nom         VARCHAR(100)        │
│ plan        ENUM(free,pro,ent)  │
│ created_at  DATETIME            │
└─────────────────┬───────────────┘
                  │ 1
                  │
         ┌────────▼────────┐
         │   utilisateurs  │
         ├─────────────────┤
         │ id          INT PK      │
         │ tenant_id   INT FK      │
         │ email       VARCHAR(150)│
         │ password_hash VARCHAR   │
         │ role        ENUM(admin, │
         │             magasinier, │
         │             vendeur)    │
         │ boutique_id INT FK      │
         │ is_active   BOOL        │
         └─────────────────┘

┌──────────────────────────────────┐
│            produits              │
├──────────────────────────────────┤
│ id               INT PK          │
│ tenant_id        INT FK          │
│ reference        VARCHAR(50)     │
│ designation      VARCHAR(255)    │
│ categorie_id     INT FK          │
│ prix_client      DECIMAL(12,2)   │
│ prix_technicien  DECIMAL(12,2)   │
│ seuil_min        INT             │
│ unite            VARCHAR(20)     │
│ created_at       DATETIME        │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│            boutiques             │
├──────────────────────────────────┤
│ id          INT PK               │
│ tenant_id   INT FK               │
│ nom         VARCHAR(100)         │
│ adresse     TEXT                 │
│ type        ENUM(depot,boutique) │
│ is_active   BOOL                 │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│             stocks               │
├──────────────────────────────────┤
│ id           INT PK              │
│ tenant_id    INT FK              │
│ produit_id   INT FK → produits   │
│ boutique_id  INT FK → boutiques  │
│ quantite     INT                 │
│ updated_at   DATETIME            │
│ UNIQUE (produit_id, boutique_id) │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│             ventes               │
├──────────────────────────────────┤
│ id              INT PK           │
│ tenant_id       INT FK           │
│ boutique_id     INT FK           │
│ utilisateur_id  INT FK           │
│ client_id       INT FK (nullable)│
│ date_vente      DATETIME         │
│ montant_total   DECIMAL(14,2)    │
│ remise_pct      DECIMAL(5,2)     │
│ mode_paiement   ENUM(...)        │
│ synced_offline  BOOL             │
│ offline_id      VARCHAR(50)      │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│          lignes_vente            │
├──────────────────────────────────┤
│ id              INT PK           │
│ vente_id        INT FK → ventes  │
│ produit_id      INT FK           │
│ quantite        INT              │
│ prix_unitaire   DECIMAL(12,2)    │
│ remise_ligne    DECIMAL(5,2)     │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│           transferts             │
├──────────────────────────────────┤
│ id              INT PK           │
│ tenant_id       INT FK           │
│ source_id       INT FK → boutiqs │
│ destination_id  INT FK → boutiqs │
│ utilisateur_id  INT FK           │
│ statut          ENUM(en_cours,   │
│                 validé,annulé)   │
│ date_transfert  DATETIME         │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│        lignes_transfert          │
├──────────────────────────────────┤
│ id              INT PK           │
│ transfert_id    INT FK           │
│ produit_id      INT FK           │
│ quantite        INT              │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│            clients               │
├──────────────────────────────────┤
│ id              INT PK           │
│ tenant_id       INT FK           │
│ nom             VARCHAR(150)     │
│ telephone       VARCHAR(20)      │
│ type_client     ENUM(simple,     │
│                 technicien)      │
│ credit_balance  DECIMAL(14,2)    │
│ created_at      DATETIME         │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│            audit_log             │
├──────────────────────────────────┤
│ id              INT PK           │
│ tenant_id       INT FK           │
│ utilisateur_id  INT FK           │
│ action          VARCHAR(100)     │
│ table_cible     VARCHAR(50)      │
│ id_cible        INT              │
│ details         JSON             │
│ ip_address      VARCHAR(45)      │
│ created_at      DATETIME         │
└──────────────────────────────────┘
```

### A.2 Tables ML

```
┌──────────────────────────────────┐
│          ml_model_registry       │
├──────────────────────────────────┤
│ id              INT PK           │
│ tenant_id       INT FK           │
│ model_type      VARCHAR(50)      │
│ version         INT              │
│ artifact_path   VARCHAR(255)     │
│ metrics         JSON             │
│ status          ENUM(active,     │
│                 archived,failed) │
│ trained_at      DATETIME         │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│          ml_predictions          │
├──────────────────────────────────┤
│ id              INT PK           │
│ tenant_id       INT FK           │
│ model_type      VARCHAR(50)      │
│ entity_id       INT (nullable)   │
│ prediction      JSON             │
│ computed_at     DATETIME         │
└──────────────────────────────────┘
```

---

## Annexe B — Captures d'écran supplémentaires

> *Note : Les captures d'écran de l'interface GesCom-BF sont disponibles dans le dossier `/docs/screenshots/` du dépôt GitHub. Les figures ci-dessous décrivent les écrans principaux de l'application. Les images réelles doivent être insérées à cet emplacement lors de la mise en forme finale du document.*

**Figure B.1 — Tableau de bord principal (vue Admin)**

Écran d'accueil de l'administrateur affichant : le chiffre d'affaires du jour par boutique, la courbe CA des 30 derniers jours, le top 5 des produits vendus, les alertes de stock minimum, et le résumé des transferts en attente de validation.

**Figure B.2 — Interface de saisie de vente (vue Vendeur)**

Formulaire de saisie rapide d'une vente : recherche produit par référence ou désignation (auto-complétion), sélection de la quantité, affichage automatique du prix selon le type de client (simple/technicien), saisie de la remise dans les limites du rôle, validation et impression du ticket.

**Figure B.3 — Mode hors-ligne (indicator PWA)**

Bandeau de notification orange "Mode hors-ligne — les ventes seront synchronisées à la reconnexion", avec compteur de ventes en attente dans la `sync_queue` de l'IndexedDB local. Le bouton "Synchroniser maintenant" devient actif dès le retour de la connexion.

**Figure B.4 — Tableau de bord analytique ML**

Page dédiée aux analyses IA : graphe de prévision de demande Prophet (7 jours, avec intervalles de confiance), carte de segmentation RFM avec les 4 segments colorés, liste des anomalies détectées avec leurs raisons, et histogramme de répartition des scores crédit.

**Figure B.5 — Rapport de scoring crédit (client individuel)**

Fiche détaillée d'un client : score crédit (0–100) affiché en jauge colorée (vert/orange/rouge), niveau de risque (FAIBLE / MOYEN / ÉLEVÉ), et les 3 facteurs SHAP les plus influents avec leur contribution en points (ex. : "Délai moyen de remboursement : −18 pts", "Ancienneté : +12 pts", "Fréquence d'achat : +8 pts").

**Figure B.6 — Écran de gestion des transferts (vue Magasinier)**

Liste des transferts en cours avec statut (en cours / validé / annulé), boutons de validation / annulation, et détail ligne par ligne des produits transférés avec quantités source et destination. Le stock source est vérifié en temps réel avant validation.

**Figure B.7 — Pipeline CI/CD — Tableau de bord GitHub Actions**

Capture du tableau de bord GitHub Actions montrant les 5 dernières exécutions du pipeline, avec les étapes (lint flake8 → pytest 93/93 → deploy PythonAnywhere) et leur durée respective.

---

## Annexe C — Extraits du code ML

### C.1 Fallback Prophet → LinearRegression → Naive

```python
# backend/analytics/demand_forecast.py (extrait simplifié)

def forecast_demand(df: pd.DataFrame, periods: int = 7) -> dict:
    """
    Prévision de demande avec 3 niveaux de fallback.
    
    Args:
        df: DataFrame avec colonnes ['ds' (date), 'y' (quantité vendue)]
        periods: Nombre de jours à prévoir
    
    Returns:
        dict avec 'forecast', 'data_confidence', 'model_used'
    """
    n_days = len(df["ds"].unique())

    # Niveau 1 — Prophet (≥ 30 jours d'historique)
    if n_days >= 30:
        try:
            m = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                holidays=get_burkina_faso_holidays(df["ds"].min(), df["ds"].max()),
            )
            m.fit(df)
            future = m.make_future_dataframe(periods=periods)
            forecast = m.predict(future).tail(periods)
            return {
                "forecast": _sanitize_forecast(forecast),
                "data_confidence": "HIGH",
                "model_used": "PROPHET",
            }
        except Exception as e:
            logger.warning(f"Prophet failed: {e}. Falling back to LinearRegression.")

    # Niveau 2 — Régression linéaire (14–29 jours)
    if n_days >= 14:
        try:
            X = np.arange(len(df)).reshape(-1, 1)
            y = df["y"].values
            model = LinearRegression().fit(X, y)
            X_future = np.arange(len(df), len(df) + periods).reshape(-1, 1)
            predictions = model.predict(X_future).clip(min=0)
            return {
                "forecast": [{"yhat": v, "yhat_lower": v * 0.8, "yhat_upper": v * 1.2}
                              for v in predictions],
                "data_confidence": "MEDIUM",
                "model_used": "LINEAR_REGRESSION",
            }
        except Exception as e:
            logger.warning(f"LinearRegression failed: {e}. Falling back to naive.")

    # Niveau 3 — Moyenne naive (< 14 jours)
    mean_qty = df["y"].mean() if len(df) > 0 else 0.0
    return {
        "forecast": [{"yhat": mean_qty, "yhat_lower": 0, "yhat_upper": mean_qty * 2}
                     for _ in range(periods)],
        "data_confidence": "LOW",
        "model_used": "NAIVE_MEAN",
    }


def _sanitize_forecast(forecast_df: pd.DataFrame) -> list:
    """Remplace NaN/Inf par 0 avant sérialisation JSON."""
    cols = ["yhat", "yhat_lower", "yhat_upper"]
    for col in cols:
        forecast_df[col] = np.nan_to_num(
            forecast_df[col].values, nan=0.0, posinf=0.0, neginf=0.0
        ).clip(min=0)
    return forecast_df[["ds"] + cols].to_dict("records")
```

### C.2 Jours fériés burkinabè pour Prophet

```python
# backend/analytics/burkina_holidays.py

def get_burkina_faso_holidays(start_date, end_date) -> pd.DataFrame:
    """
    Retourne les jours fériés officiels et événements commerciaux du Burkina Faso
    pour la plage de dates donnée.
    
    Sources : calendrier officiel BF + dates lunaires Ramadan/Aïd précalculées.
    """
    holidays = []

    # Jours fériés fixes (par année)
    fixed_holidays = {
        1:  ("Jour de l'An",       0, 0),   # 1er janvier
        3:  ("Fête du travail",    1, 1),   # 1er mai → lower/upper 1 jour
        8:  ("Fête Nationale",     3, 3),   # 11 août (Indépendance)
        12: ("Noël",               2, 2),   # 25 décembre
    }
    # ... (logique d'ajout des dates fixes par année)

    # Dates lunaires (Ramadan + Aïd) précalculées 2023-2027
    RAMADAN_DATES = {
        2023: ("2023-03-23", "2023-04-21"),
        2024: ("2024-03-11", "2024-04-09"),
        2025: ("2025-03-01", "2025-03-30"),
        2026: ("2026-02-18", "2026-03-19"),
        2027: ("2027-02-07", "2027-03-09"),
    }

    for year, (debut, fin) in RAMADAN_DATES.items():
        if start_date.year <= year <= end_date.year:
            # Boost d'achat avant et pendant le Ramadan
            holidays.append({
                "holiday": "Ramadan",
                "ds": pd.date_range(debut, fin, freq="D"),
                "lower_window": -7,   # Achats préventifs 7 jours avant
                "upper_window": 3,
            })
            # Aïd el-Fitr : pic d'achat
            holidays.append({
                "holiday": "Aid_el_Fitr",
                "ds": pd.Timestamp(fin) + pd.Timedelta(days=1),
                "lower_window": -2,
                "upper_window": 1,
            })

    return pd.concat([pd.DataFrame(h) for h in holidays], ignore_index=True)
```

### C.3 Calcul de la probabilité de churn

```python
# backend/analytics/rfm_segmentation.py (extrait)

def compute_churn_probability(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule la probabilité de churn pour chaque client via heuristique
    inspirée du modèle de survie exponentiel (Pareto/NBD simplifié).
    
    Formule : P_churn = 1 - exp(-lambda * R)
    
    Où :
        R      = récence en jours (jours depuis le dernier achat)
        lambda = log(2) / median(R)  [calibré sur le portefeuille actuel]
    
    Ajustement fréquence : les clients très fréquents ont un lambda réduit.
    """
    if rfm_df.empty:
        return rfm_df

    median_recency = rfm_df["recency_days"].median()
    if median_recency <= 0:
        median_recency = 30  # Valeur par défaut

    lambda_base = np.log(2) / median_recency

    def _churn_prob(row):
        # Ajustement : clients fréquents (>= 10 achats) → lambda réduit de 30%
        lambda_adj = lambda_base * 0.7 if row["frequency"] >= 10 else lambda_base
        prob = 1 - np.exp(-lambda_adj * row["recency_days"])
        return round(float(np.clip(prob, 0.0, 1.0)), 4)

    rfm_df["churn_probability"] = rfm_df.apply(_churn_prob, axis=1)

    # Classification en 4 niveaux
    def _churn_level(p):
        if p >= 0.75:   return "CRITIQUE"
        if p >= 0.50:   return "ÉLEVÉ"
        if p >= 0.25:   return "MODÉRÉ"
        return "FAIBLE"

    rfm_df["churn_risk_level"] = rfm_df["churn_probability"].apply(_churn_level)
    return rfm_df
```

### C.4 Design fail-safe du registre de modèles

```python
# backend/analytics/model_registry.py (extrait)

class ModelRegistry:
    """
    Registre central des modèles ML chargés en mémoire.
    
    Design fail-safe : si un nouveau modèle échoue à l'entraînement,
    l'ancien modèle reste actif et continue à servir les prédictions.
    Un modèle stale (non rechargé depuis > 36h) déclenche une alerte.
    """
    _models: dict = {}
    _metadata: dict = {}

    @classmethod
    def register(cls, model_type: str, model, metrics: dict, artifact_path: str):
        """Enregistre un nouveau modèle — remplace l'ancien uniquement si succès."""
        cls._models[model_type] = model
        cls._metadata[model_type] = {
            "status": "loaded",
            "last_trained": datetime.utcnow().isoformat() + "Z",
            "metrics": metrics,
            "artifact_path": artifact_path,
        }
        logger.info(f"[Registry] {model_type} registered — metrics: {metrics}")

    @classmethod
    def get(cls, model_type: str):
        """Retourne le modèle actif, ou None si jamais entraîné."""
        return cls._models.get(model_type)

    @classmethod
    def get_all_statuses(cls) -> dict:
        """Retourne le statut de tous les modèles (pour /health)."""
        now = datetime.utcnow()
        statuses = {}
        for model_type, meta in cls._metadata.items():
            last_trained = datetime.fromisoformat(meta["last_trained"].rstrip("Z"))
            hours_since = (now - last_trained).total_seconds() / 3600
            status = "stale" if hours_since > 36 else "loaded"
            statuses[model_type] = {**meta, "status": status}
        return statuses
```

---

*— Fin du document —*

*Mémoire de fin de cycle — Licence Professionnelle en Génie Logiciel*
*Université Virtuelle du Burkina Faso (UVBF)*
*Soutenance : Juillet 2026*
