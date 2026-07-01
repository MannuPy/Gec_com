# CHAPITRE 4 : MODULE D'INTELLIGENCE ARTIFICIELLE ET D'ANALYSE DE DONNÉES

---

## Introduction

Ce chapitre constitue la contribution originale principale de ce mémoire. Il présente le module analytique de GesCom-BF, composé de sept composants d'aide à la décision couvrant des problématiques réelles des PME commerciales burkinabè : anticiper les ruptures de stock, évaluer la solvabilité des clients à crédit, détecter les fraudes et remises abusives, segmenter le portefeuille clients, identifier les associations de produits, et analyser la sensibilité aux prix dans leur contexte africain.

Chaque composant est décrit avec rigueur : l'algorithme utilisé, sa justification, ses paramètres, son implémentation dans le code, et — point fondamental — une classification honnête de sa nature réelle (ML supervisé, ML non supervisé, analytique BI ou heuristique statistique). Cette honnêteté est un choix délibéré : elle démontre la maîtrise conceptuelle du domaine et la capacité à distinguer ce qui relève de l'apprentissage automatique de ce qui n'en relève pas.

---

## 4.1 Vue d'ensemble du module analytique

### 4.1.1 Classification honnête des techniques

Le tableau ci-dessous présente les sept composants du module analytique avec leur qualification technique réelle.

**Tableau 12 : Classification des modules analytiques (ML réel / BI / heuristique)**

| Module | Fichier | Algorithme | Nature réelle | Fréquence |
|---|---|---|---|---|
| Prévision de demande | `demand_forecast.py` | **Prophet** (Meta) + sklearn fallback + naive | **ML — série temporelle bayésienne** | Hebdomadaire |
| Scoring crédit | `credit_scoring.py` | **Random Forest** + LogReg + **SHAP** | **ML supervisé + explicabilité** | Après chaque transaction |
| Détection d'anomalies | `anomaly_detection.py` | **Isolation Forest** | **ML non supervisé** | Quotidienne |
| Segmentation RFM | `rfm_segmentation.py` | **K-Means** + Silhouette + Elbow | **ML non supervisé (clustering)** | Mensuelle |
| Market Basket | `market_basket.py` | **Apriori** (mlxtend) + co-occurrence fallback | **ML non supervisé (règles d'association)** | Hebdomadaire |
| Classification ABC/XYZ | `abc_xyz.py` | Règles pandas déterministes | **Analytique BI — pas du ML** | Quotidienne |
| Probabilité de churn | `rfm_segmentation.py` | P = 1 − e^(−λ×R), calibré sur médiane | **Heuristique statistique — pas du ML** | Avec segmentation RFM |
| Élasticité prix | `price_elasticity_service.py` | Régression log-log (LinearRegression) | **Statistique descriptive** | À la demande |
| Contexte africain BF | `routes.py` | Règles calendaires + métriques de paiement | **Analytique contextuelle** | Temps réel |

> **Note méthodologique :** La classification "ML" ou "non-ML" n'est pas une question de valeur, mais de rigueur terminologique. Les modules heuristiques et analytiques apportent une valeur opérationnelle réelle et sont parfaitement justifiés par les contraintes de données des PME ciblées (absence de données labellisées, historiques courts). Ce que le jury doit retenir : chaque choix technique est motivé par les données disponibles, pas par l'effet d'annonce.

### 4.1.2 Pipeline d'entraînement nocturne (cron PythonAnywhere)

L'entraînement des modèles ML est orchestré par le script `backend/scripts/cron_train_all.py`, configuré comme **tâche planifiée PythonAnywhere** déclenchée chaque nuit à 02h00 (heure Africa/Abidjan), heure à faible trafic.

**Figure 15 : Pipeline d'entraînement ML nocturne** *(à insérer)*

```
Tâche planifiée PythonAnywhere (02:00)
          │
          ▼
  cron_train_all.py
          │
    ┌─────┴──────────────────────────────────────────┐
    │  1. demand_forecast.train(months=6)             │
    │  2. credit_scoring.train()                      │
    │  3. anomaly_detection.train(days=90)            │
    │  4. rfm_segmentation.train(months=12)           │
    │  5. abc_xyz.train()                             │
    │  6. market_basket.train(months=6)               │
    └─────────────────────────────────────────────────┘
          │
          ▼
   Pour chaque module :
   ┌──────────────────────────────────────────┐
   │ Extraction données MySQL                 │
   │ Entraînement modèle                      │
   │ Sauvegarde artefact .joblib (MLflow)     │
   │ Mise à jour ml_models (statut = ACTIVE)  │
   │ Enregistrement prédictions               │
   └──────────────────────────────────────────┘
          │
     Succès ──→ Modèle ACTIVE en production
     Échec  ──→ Ancien modèle conservé (fail-safe)
                Log d'erreur dans /tmp/gescom_ml_training.log
```

Le design est **fail-safe** : en cas d'échec d'un module (données insuffisantes, erreur de convergence…), l'ancien modèle reste actif en production et une alerte `MLPredictionStale` est générée après 36 heures sans mise à jour. Aucune prédiction erronée ne remplace une prédiction valide.

Sur PythonAnywhere, l'absence de Redis et Celery impose l'utilisation de threads Python natifs pour les entraînements déclenchés manuellement via l'API (`POST /analytics/ml/train`). Le cron nocturne est synchrone et séquentiel, ce qui suffit pour la volumétrie V1.

### 4.1.3 Gestion des modèles (MLflow)

Chaque modèle entraîné est tracé via **MLflow 2.14.3** :

- **Versioning** : chaque entraînement crée une nouvelle version du modèle avec un identifiant unique (`model_version`) référencé dans chaque prédiction (traçabilité data lineage — RNF-17).
- **Métriques** : les métriques de performance (RMSE pour Prophet, F1-score pour le scoring crédit, score de contamination pour l'Isolation Forest…) sont enregistrées et consultables.
- **Artefacts** : les fichiers `.joblib` (modèles sérialisés) sont sauvegardés sur le système de fichiers PythonAnywhere et référencés par MLflow.
- **Registre** : la table `ml_models` en base de données maintient le statut de chaque modèle (TRAINING / ACTIVE / DEPRECATED) et permet aux endpoints de charger toujours la version active.

---

## 4.2 Prévision de demande — Prophet

### 4.2.1 Justification du choix

La prévision de demande est le module ML le plus central : il alimente les alertes de rupture de stock, qui sont la douleur principale des gérants de quincaillerie. Le choix d'un algorithme adapté aux séries temporelles commerciales est donc critique.

**Prophet**, développé par Meta (anciennement Facebook) et publié en open-source en 2017, est un modèle de prévision de séries temporelles bayésien qui présente plusieurs avantages décisifs pour ce contexte :

- **Gestion native de la saisonnalité multiple** : Prophet décompose la série temporelle en trois composantes — tendance (croissance linéaire ou logistique), saisonnalité (hebdomadaire et annuelle), et effet des événements spéciaux — ce qui correspond parfaitement aux variations de demande d'une quincaillerie burkinabè.
- **Robustesse aux données manquantes** : les séries de ventes comportent souvent des jours sans transaction (jours fériés, fermetures). Prophet les gère nativement sans imputation préalable.
- **Intégration des jours fériés personnalisés** : c'est l'argument décisif pour le contexte burkinabè. Prophet permet de renseigner des événements personnalisés avec des fenêtres d'influence (`lower_window`, `upper_window`), ce qui permet de modéliser l'impact des fêtes locales sur la demande.
- **Performance avec peu de données** : Prophet est conçu pour fonctionner avec aussi peu que 60 à 90 jours d'historique, ce qui est réaliste pour une PME en phase de digitalisation.

Les algorithmes alternatifs considérés ont été écartés pour les raisons suivantes : ARIMA nécessite une stationnarité difficile à garantir sans prétraitement complexe ; LSTM (Deep Learning) requiert plusieurs années de données et des ressources computationnelles incompatibles avec PythonAnywhere ; XGBoost a été initialement prévu mais retiré car non disponible dans les contraintes de déploiement final.

### 4.2.2 Architecture de la solution (Prophet → sklearn → naive)

La solution adopte une architecture **à trois niveaux de fallback**, garantissant qu'une prévision est toujours produite même en cas de données insuffisantes.

```
Données historiques disponibles ?
         │
    ≥ 30 jours ──────────────────────────────────────────→ PROPHET
    (HAS_PROPHET = True)                                  + jours fériés BF
                                                          data_confidence = HIGH
         │
    14 ≤ données < 30 jours ─────────────────────────→ SKLEARN LinearRegression
    (HAS_SKLEARN = True)                                  + tendance + saisonnalité/jour
                                                          data_confidence = MEDIUM
         │
    < 14 jours ──────────────────────────────────────→ SEASONAL NAIVE
                                                          moyenne par jour de semaine
                                                          data_confidence = LOW
```

**Niveau 1 — Prophet** (données ≥ 30 jours) :

Le modèle Prophet est initialisé avec les paramètres suivants :
- Saisonnalité hebdomadaire : activée (Fourier order = 3)
- Saisonnalité annuelle : activée si historique ≥ 180 jours
- Changepoint prior scale : 0.05 (tendance peu agressive)
- Jours fériés Burkina Faso : 8 événements configurés

Les jours fériés intégrés sont :

| Événement | Dates configurées | Fenêtre d'influence |
|---|---|---|
| Tabaski (Aïd el-Adha) | 07/06/2025, 27/05/2026 | −7 jours à +3 jours |
| Début Ramadan | 01/03/2025, 18/02/2026 | −3 jours à +30 jours |
| Fête nationale (Indépendance) | 05/08/2025, 05/08/2026 | −1 jour à +1 jour |
| Noël | 25/12/2025, 25/12/2026 | −5 jours à +2 jours |

Ces fenêtres permettent à Prophet de capturer non seulement le pic de ventes du jour férié lui-même, mais aussi la montée en charge préalable (achats préparatoires) et la décrue post-fête.

**Niveau 2 — LinearRegression sklearn** (14 à 29 jours) :

Un modèle de régression linéaire avec variables exogènes encodées : indice temporel (tendance), et indicateurs binaires pour chaque jour de la semaine (saisonnalité hebdomadaire simple). La prévision à 30 jours est obtenue par extrapolation.

**Niveau 3 — Seasonal Naive** (< 14 jours) :

Moyenne de la demande par jour de la semaine sur l'historique disponible. Algorithme de référence (baseline) utilisé comme plancher de performance.

### 4.2.3 Indicateur data_confidence (HIGH / MEDIUM / LOW)

Chaque prévision est accompagnée d'un indicateur de fiabilité `data_confidence` déterminé par le niveau de fallback utilisé :

| Algorithme utilisé | `data_confidence` | Signification pour le gérant |
|---|---|---|
| Prophet (≥ 30 jours) | `HIGH` | Prévision fiable, intégrant la saisonnalité et les fêtes |
| LinearRegression (14–29 j) | `MEDIUM` | Prévision indicative, tendance capturée mais saisonnalité partielle |
| Seasonal Naive (< 14 j) | `LOW` | Prévision approximative — augmenter la marge de sécurité |

Cet indicateur est affiché dans l'interface sous forme de badge coloré (vert / orange / rouge) et est transmis dans la réponse API via le champ `data_confidence`. Il permet au gérant d'ajuster son niveau de confiance dans les recommandations de réapprovisionnement.

---

## 4.3 Scoring crédit — Random Forest + SHAP

### 4.3.1 Variables retenues et justification

Le modèle de scoring crédit évalue la probabilité qu'un client à crédit soit un bon ou mauvais payeur, sur la base de **huit variables** observables dans la base de données de l'application.

**Tableau 13 : Variables du modèle de scoring crédit**

| Variable | Description | Justification |
|---|---|---|
| `nb_achats_credit_total` | Nombre total d'achats à crédit | Plus ce nombre est élevé, plus on a d'historique pour évaluer le comportement |
| `montant_moyen_achat` | Montant moyen par achat (FCFA) | Indicateur de capacité économique du client |
| `delai_moyen_remboursement_jours` | Délai moyen de remboursement observé | Variable la plus prédictive — un délai court indique un bon payeur |
| `taux_retard` | Taux de remboursements en retard | Mesure directe de la fiabilité passée |
| `anciennete_client_mois` | Ancienneté de la relation commerciale | Un client ancien est mieux connu et souvent plus fiable |
| `frequence_achat_mensuelle` | Nombre d'achats par mois en moyenne | Indicateur de fidélité et d'engagement |
| `solde_du_actuel` | Solde dû actuel en FCFA | Un solde élevé non remboursé est un signal d'alarme direct |
| `is_technicien` | Client technicien (1) ou simple (0) | Les techniciens ont généralement un comportement de paiement différent (régulier) |

Ces variables ont été sélectionnées selon deux critères : (1) elles sont disponibles nativement dans la base de données de GesCom-BF sans acquisition de données externes, et (2) elles ont une valeur prédictive métier directe, validée par la littérature sur le scoring crédit en microfinance africaine.

**Gestion des données manquantes (proxy `SIMULATED`) :** Si un client n'a aucun historique de paiement dans `CustomerPayment`, le système utilise `credit_balance` (solde dû actuel) comme proxy observable, et le `délai_moyen` est remplacé par la médiane globale des délais de paiement de tous les clients. Ce mode est explicitement signalé dans la réponse API (`data_source: "SIMULATED"`) pour alerter le gérant que la prédiction est moins fiable.

### 4.3.2 Modèle Random Forest + validation croisée

**Architecture du modèle :**

Le modèle principal est un `RandomForestClassifier` (scikit-learn) avec les hyperparamètres suivants :
- `n_estimators = 200` : 200 arbres de décision — suffisant pour la stabilité sur des petits jeux de données
- `max_depth = None` (arbres complets, avec contrôle du sur-apprentissage par le nombre d'arbres)
- `class_weight = "balanced"` : pour compenser le déséquilibre de classes (les mauvais payeurs sont rares)
- `random_state = 42` : reproductibilité garantie

Un second modèle `LogisticRegressionCV` (régression logistique avec validation croisée de la pénalité C) est entraîné en parallèle. Le score final est la **moyenne pondérée des probabilités** des deux modèles (0.6 × RF + 0.4 × LogReg), ce qui améliore la robustesse et réduit la variance.

**Validation croisée :**

La validation est réalisée par `StratifiedKFold` avec k = min(5, n_classes_minority), garantissant la présence des deux classes dans chaque fold même avec peu d'exemples. Le score F1-macro est loggé dans MLflow.

Le modèle n'est entraîné que si le nombre de clients avec historique de paiement est supérieur à 20 (`MIN_SAMPLES_FOR_ML = 20`). En dessous de ce seuil, un système de scoring par règles pondérées est utilisé comme fallback (chaque variable contribue à un score de 0 à 100 selon des seuils métier définis).

**Score final :** le score brut (probabilité de la classe "bon payeur", entre 0 et 1) est converti en score 0–100 puis interprété selon trois niveaux de risque :

| Plage de score | Niveau de risque | Recommandation |
|---|---|---|
| 0 – 40 | ÉLEVÉ | Refuser ou limiter le crédit |
| 41 – 70 | MOYEN | Accorder avec garantie ou suivi renforcé |
| 71 – 100 | FAIBLE | Crédit accordable selon les conditions habituelles |

### 4.3.3 Explicabilité SHAP — exemple d'interprétation

**SHAP (SHapley Additive exPlanations)** est une bibliothèque d'explicabilité ML basée sur la théorie des jeux coopératifs (valeurs de Shapley). Elle décompose la prédiction d'un modèle en contributions individuelles de chaque variable, permettant de répondre à la question : "Pourquoi ce client a-t-il obtenu ce score ?"

**Implémentation technique :**

```python
# Extrait de credit_scoring.py
import shap
explainer = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(X_client)
# shap_values[1] = valeurs SHAP pour la classe "bon payeur"
top3_features = sorted(
    zip(FEATURE_LABELS_FR.keys(), shap_values[1][0]),
    key=lambda x: abs(x[1]),
    reverse=True
)[:3]
```

**Figure 17 : Exemple de graphique SHAP — scoring crédit** *(à insérer)*

Exemple d'interprétation pour un client avec score 35 / 100 (risque ÉLEVÉ) :

```
Score de base (valeur moyenne) : 58 / 100

Contributions des variables :
  ↓ taux_retard = 0.45        → −18 pts  (taux de retard élevé, pénalise fortement)
  ↓ solde_du_actuel = 450 000 → −12 pts  (solde dû élevé non remboursé)
  ↓ delai_moyen = 52 jours    → −8 pts   (délai de remboursement long)
  ↑ anciennete = 24 mois      →  +7 pts  (ancienneté positive)
  ↑ frequence = 3/mois        →  +8 pts  (client régulier)
  ─────────────────────────────────────────
  Score final : 35 / 100 → Risque ÉLEVÉ
```

L'interface présente au gérant les **3 facteurs les plus déterminants** pour chaque client, avec leur contribution en points positifs ou négatifs. Cette transparence est essentielle dans le contexte du crédit informel burkinabè, où le gérant doit pouvoir justifier sa décision au client.

---

## 4.4 Détection d'anomalies — Isolation Forest

### 4.4.1 Principe de l'algorithme

**Isolation Forest** est un algorithme de détection d'anomalies non supervisé introduit par Liu et al. (2008). Son principe est fondamentalement différent des approches classiques (distance, densité) : au lieu de modéliser ce qu'est un comportement "normal" pour ensuite identifier les déviants, Isolation Forest cherche directement à *isoler* les points anormaux.

L'intuition de l'algorithme est la suivante : **un point anormal est plus facile à isoler qu'un point normal**. L'algorithme construit une forêt d'arbres de décision aléatoires (Isolation Trees) : à chaque nœud, une variable et un seuil de coupure sont choisis aléatoirement. Les points anomaux — qui se trouvent dans des régions peu denses de l'espace des features — nécessitent en moyenne beaucoup moins de coupures pour être isolés dans une feuille. Le score d'anomalie est inversement proportionnel à la longueur du chemin moyen dans la forêt.

**Paramètres utilisés dans GesCom-BF :**
- `contamination = 0.05` : hypothèse que 5 % des transactions sont anormales (ajustable)
- `n_estimators = 100` : 100 arbres pour la stabilité
- `random_state = 42` : reproductibilité

**Vecteur de features** (5 dimensions) :

| Feature | Description |
|---|---|
| `montant_total` | Montant total de la vente (FCFA) |
| `remise_taux` | Taux de remise appliqué (0, 5, 10, 15 ou 20 %) |
| `heure_vente` | Heure de la vente (0–23) |
| `ecart_vs_moyenne_produit` | Écart du montant par rapport à la moyenne du produit (en σ) |
| `ecart_vs_moyenne_vendeur` | Écart du montant par rapport à la moyenne du vendeur (en σ) |

### 4.4.2 Raisons enrichies produites par le système

L'Isolation Forest seul produit un score numérique opaque. Pour que l'administrateur puisse agir sur un signalement, GesCom-BF enrichit chaque anomalie avec une liste de **raisons lisibles en français**, générées par un moteur de règles appliqué après la prédiction. Cette approche hybride (ML pour la détection, règles pour l'explication) est une bonne pratique reconnue en ML responsable.

Les raisons générées couvrent plusieurs catégories :

**Remises suspectes :**
- "Remise maximale accordée (20 %) — approbation requise"
- "Remise élevée (≥ 15 %)"
- "Remise accordée en dehors des heures de supervision (avant 8h)"

**Écarts de montant :**
- "Montant 3.2× supérieur à la moyenne du produit"
- "Volume 2.8× supérieur à la moyenne du vendeur — risque fraude"

**Horaires atypiques :**
- "Vente très tôt le matin (avant 6h) — horaire inhabituel"
- "Vente en soirée tardive (après 21h) — horaire inhabituel"

**Combinaisons à risque élevé :**
- "Combinaison remise élevée + volume vendeur anormal"
- "Montant suspect avec remise sur produit à écart élevé"

Si aucune règle spécifique ne s'applique : "Profil statistique atypique (score Isolation Forest bas)" — ce qui indique que c'est l'algorithme lui-même qui a détecté la déviance sans correspondance à un pattern connu.

---

## 4.5 Segmentation clients RFM — K-Means

### 4.5.1 Dimensions Récence / Fréquence / Montant

La **segmentation RFM** est un modèle classique d'analyse de la valeur client issu du marketing direct, reposant sur trois dimensions complémentaires :

- **Récence (R)** : nombre de jours depuis le dernier achat du client. Un R faible indique un client actif et récent.
- **Fréquence (F)** : nombre total d'achats sur la période analysée (12 mois par défaut). Un F élevé indique un client fidèle.
- **Montant (M)** : chiffre d'affaires total généré par le client sur la période. Un M élevé indique un client à forte valeur économique.

Ces trois dimensions sont calculées directement depuis la table `sales` (jointure avec `sale_lines`), sans nécessiter de données externes. La date de référence est `NOW()` en UTC.

**Quatre segments sont définis :**

| Segment | Label | Profil RFM | Action recommandée |
|---|---|---|---|
| CHAMPIONS | Champions | R faible, F élevée, M élevé | Programme de fidélité, crédit étendu |
| REGULIERS | Clients réguliers | R modérée, F modérée | Relances ciblées et offres personnalisées |
| A_RISQUE | À risque | R élevée, F faible | Campagne de réactivation urgente |
| OCCASIONNELS | Occasionnels | R élevée, F et M faibles | Communication standard |

L'affectation des clients à ces segments utilise K-Means sur les coordonnées RFM standardisées (StandardScaler). L'algorithme assigne chaque client au cluster dont le centre est le plus proche (distance euclidienne dans l'espace standardisé). Les centres sont ensuite interprétés pour assigner les labels CHAMPIONS / REGULIERS / A_RISQUE / OCCASIONNELS selon un score composite (F + M − R).

### 4.5.2 Détermination automatique de K (Silhouette + Elbow)

Un problème fréquent du K-Means est le choix du nombre de clusters K. Fixer K arbitrairement à 4 (pour CHAMPIONS / REGULIERS / A_RISQUE / OCCASIONNELS) est une simplification valable, mais GesCom-BF propose un endpoint d'évaluation automatique (`GET /analytics/rfm-segments/evaluate-k`) qui calcule trois métriques pour chaque valeur de K entre 2 et 8 :

**Score de Silhouette :** mesure la cohésion intra-cluster et la séparation inter-cluster. Il varie entre −1 et +1 ; une valeur > 0.5 indique une bonne séparation. La valeur optimale de K est celle qui **maximise** le score de Silhouette.

```
s(i) = (b(i) - a(i)) / max(a(i), b(i))

où :
  a(i) = distance moyenne du point i à tous les autres points de son cluster
  b(i) = distance moyenne du point i au cluster le plus proche (autre que le sien)
```

**Indice de Davies-Bouldin :** mesure le rapport entre la dispersion intra-cluster et la séparation inter-cluster. Une valeur proche de 0 indique des clusters compacts et bien séparés. La valeur optimale de K est celle qui **minimise** cet indice.

**Inertie (méthode du coude) :** somme des distances au carré de chaque point à son centre de cluster. Elle décroît monotonement avec K ; le "coude" de la courbe indique le K au-delà duquel le gain marginal devient faible.

L'endpoint retourne le K optimal recommandé (par maximisation du score de Silhouette) avec son interprétation en langage naturel :

| Score de Silhouette optimal | Interprétation |
|---|---|
| ≥ 0.71 | Excellente séparation — les segments sont bien distincts |
| 0.51 – 0.70 | Bonne séparation |
| 0.26 – 0.50 | Séparation faible — chevauchement partiel des segments |
| < 0.26 | Aucune structure naturelle détectée — données homogènes |

---

## 4.6 Market Basket Analysis — Apriori

### 4.6.1 Règles d'association (support, confidence, lift)

L'**analyse du panier d'achat** (Market Basket Analysis) identifie les produits fréquemment achetés ensemble dans la même transaction. Elle génère des **règles d'association** de la forme : "Si un client achète le produit A, il est probable qu'il achète aussi le produit B."

Ces règles sont caractérisées par trois métriques fondamentales :

**Support :** proportion des transactions contenant l'ensemble d'items {A, B}.

```
support({A, B}) = |transactions contenant A et B| / |total transactions|
```

Un support de 0.05 signifie que 5 % de toutes les transactions contiennent à la fois A et B.

**Confidence :** probabilité conditionnelle d'acheter B sachant qu'on a déjà acheté A.

```
confidence(A → B) = support({A, B}) / support({A})
```

Une confidence de 0.70 signifie que dans 70 % des transactions contenant A, B est également présent.

**Lift :** mesure l'intérêt réel de la règle en comparaison avec l'indépendance statistique.

```
lift(A → B) = confidence(A → B) / support({B})
```

Un lift > 1 indique une association réelle (A favorise l'achat de B). Un lift = 1 indique une indépendance. Un lift < 1 indique une association négative.

**Paramètres Apriori dans GesCom-BF :**
- `min_support = 0.02` : une règle doit apparaître dans au moins 2 % des transactions
- `min_confidence = 0.30` : probabilité minimale de 30 % que B soit acheté avec A
- `min_lift = 1.2` : l'association doit être au moins 1.2× plus fréquente que par hasard
- `max_len = 3` : règles de 2 ou 3 produits maximum (gestion combinatoire)

**Algorithme Apriori vs fallback co-occurrence :**

L'algorithme **Apriori** (bibliothèque mlxtend) utilise la propriété d'anti-monotonie : si un itemset est peu fréquent (support < min_support), tous ses sur-ensembles le sont aussi. Cette propriété permet d'élaguer efficacement l'espace de recherche. Il est utilisé lorsque `HAS_MLXTEND = True` et que la transaction matrix est suffisamment grande.

En cas d'indisponibilité de mlxtend ou de corpus trop petit, un **fallback par co-occurrence** est activé : les paires de produits co-présentes dans des transactions sont comptées avec `Counter` et `combinations`, et les K paires les plus fréquentes sont retournées avec support et lift approximatifs.

### 4.6.2 Application : recommandations croisées pour le vendeur

Les règles d'association générées alimentent deux usages concrets dans l'interface :

**Recommandations de vente croisée (cross-selling) :** lorsqu'un vendeur ajoute un produit au panier, le système peut suggérer les produits fréquemment achetés avec lui (lift > 1.5). Exemple dans le contexte quincaillerie : "Les clients qui achètent des boulons M10 achètent aussi des rondelles M10 (confidence : 68 %, lift : 3.2)."

**Optimisation de l'agencement :** les produits avec fort lift peuvent être rapprochés physiquement en boutique ou dans le dépôt, réduisant le temps de préparation des commandes.

**Optimisation du stock préventif :** si la règle {A → B} a un lift élevé, une rupture de stock sur A peut être utilisée comme signal prédictif d'une baisse de ventes sur B — utile pour les décisions de réapprovisionnement.

---

## 4.7 Modules complémentaires

### 4.7.1 Classification ABC/XYZ (analytique BI — règles déterministes)

> **Note de classification honnête :** ce module **n'est pas du Machine Learning**. Il s'agit d'une classification déterministe par règles métier implémentée en pandas. Aucun algorithme d'apprentissage, aucun paramètre entraîné, résultat 100 % reproductible à données identiques. Il est présenté dans ce chapitre car il contribue à l'aide à la décision.

La **classification ABC** répartit les produits selon leur contribution au chiffre d'affaires total, selon la loi de Pareto :

| Classe | Proportion CA cumulé | Interprétation |
|---|---|---|
| **A** | 0 – 70 % | Produits critiques — priorité de stock absolue |
| **B** | 70 – 90 % | Produits importants — stock régulier |
| **C** | 90 – 100 % | Produits secondaires — stock minimal |

La **classification XYZ** évalue la régularité de la demande par le coefficient de variation (CV) des ventes hebdomadaires :

| Classe | CV | Interprétation |
|---|---|---|
| **X** | CV < 0.5 | Demande régulière — prévision fiable |
| **Y** | 0.5 ≤ CV < 1.0 | Demande variable — stock de sécurité recommandé |
| **Z** | CV ≥ 1.0 | Demande très irrégulière — approvisionnement à la demande |

La **classification combinée ABC-XYZ** croise les deux dimensions : un produit AX est critique et prévisible (à approvisionner en priorité avec stock régulier) ; un produit CZ est secondaire et imprévisible (à commander à la demande uniquement). Les produits avec `dead_stock = True` (aucune vente depuis 90 jours) sont signalés séparément pour action immédiate (déstockage, promotion).

### 4.7.2 Probabilité de churn (heuristique P = 1 − e^(−λ×R))

> **Note de classification honnête :** ce module **n'est pas du Machine Learning**. Il n'y a ni entraînement, ni données labellisées "client churné / non churné", ni split train/test, ni métrique AUC/F1. C'est un **modèle statistique heuristique** inspiré de la théorie de la survie (modèle de décroissance exponentielle de type Pareto/NBD).

**Justification du choix heuristique :** un modèle ML supervisé (RandomForest, XGBoost) pour prédire le churn nécessiterait des centaines d'exemples positifs (clients ayant effectivement churné, c'est-à-dire cessé définitivement leurs achats). Or, dans les PME burkinabè ciblées, les données historiques sont courtes (projet récent) et le label "churné" est difficile à définir sans suivi contractuel. Le modèle heuristique offre une valeur opérationnelle immédiate sans ces prérequis.

**Modèle mathématique :**

```
P(churn) = 1 − exp(−λ × R)

où :
  R = récence du client (jours depuis son dernier achat)
  λ = log(2) / médiane(R)  [calibration sur la demi-vie de la récence]

Ajustement par la fréquence :
  P_ajustée = P(churn) × (1 − 0.25 × fréquence_relative)
  
  où fréquence_relative = fréquence_client / max(fréquence_portefeuille)
  (les clients très fréquents sont moins susceptibles de churner)
```

La calibration sur la médiane de récence garantit que λ est auto-adaptatif au portefeuille : si la médiane de récence est de 30 jours, λ = log(2)/30 ≈ 0.023, et un client absent depuis 60 jours a une probabilité de churn de 1 − e^(−0.023 × 60) ≈ 75 %.

**Niveaux de risque et actions :**

| P_ajustée | Niveau de risque | Action recommandée |
|---|---|---|
| 0 – 30 % | FAIBLE | Maintenir la relation standard |
| 30 – 60 % | MODÉRÉ | Envoyer une offre de fidélité |
| 60 – 80 % | ÉLEVÉ | Relance personnalisée recommandée |
| 80 – 100 % | CRITIQUE | Contact direct urgent — risque de perte définitive |

### 4.7.3 Élasticité prix (régression log-log)

> **Note de classification honnête :** ce module est de la **statistique descriptive/économétrique**, pas du Machine Learning au sens strict.

L'**élasticité prix** mesure la sensibilité de la quantité vendue aux variations de prix (via les remises appliquées). Elle est calculée par une **régression log-log** (double logarithmique) :

```
ln(quantité) = α + β × ln(1 − taux_remise) + ε

où :
  α = constante (ordonnée à l'origine en log)
  β = élasticité-remise (coefficient directeur)
  ε = terme d'erreur
```

L'élasticité β s'interprète ainsi :
- β > 0 : une augmentation de la remise augmente la quantité vendue (produit élastique)
- β ≈ 0 : la remise n'influence pas les ventes (produit inélastique)
- β < 0 : cas rare (produit de Giffen ou effet de signe négatif dû aux données)

Pour chaque produit ayant au moins 20 lignes de vente sur la période (dont des ventes avec et sans remise), la régression est estimée par `LinearRegression` sklearn. Le coefficient de détermination R² est calculé et retourné avec l'élasticité pour indiquer la qualité de l'ajustement.

**Interprétation automatique en langage naturel :**
- β > 1.5 : "Produit très sensible aux remises — une remise de 10 % génère +15 % de volumes"
- 0.5 < β ≤ 1.5 : "Produit moyennement sensible aux remises"
- β ≤ 0.5 : "Produit peu sensible aux remises — la tarification peut être maintenue"

Si aucune vente avec remise n'est disponible sur la période, l'API retourne un diagnostic explicite au lieu d'une liste vide, orientant l'administrateur vers l'action corrective.

### 4.7.4 Contexte africain BF (événements, stress trésorerie, crédit informel)

Ce module est une **originalité forte** de GesCom-BF par rapport aux ERP génériques. Il agrège en temps réel des indicateurs contextuels spécifiques à l'environnement commercial burkinabè, accessibles via `GET /analytics/african-context`.

**Événements calendaires actifs :**

Le système détecte automatiquement les événements saisonniers en fonction de la date courante :

| Événement | Période | Impact | Recommandation stock |
|---|---|---|---|
| Saison Tabaski | Juin–juillet | Forte demande alimentaire et habillement | +40 à 60 % sur les stocks concernés |
| Saison des pluies | Juin–septembre | Accès difficile dans certaines zones | Constituer des réserves pour 45–60 jours |
| Rentrée scolaire | 1–20 septembre | Forte demande en fournitures scolaires | Augmenter stocks articles scolaires |
| Semaine de paie | À partir du 25 du mois | Pic de ventes lié au pouvoir d'achat | Assurer disponibilité articles forte rotation |
| Fête de l'indépendance | 5–11 août | Réduction d'activité et déplacements | Stock préventif 3–5 jours |

**Indice de stress de trésorerie :**

Calculé à partir des paiements à crédit en retard (`CustomerPayment` avec `status = LATE`) :

```
Indice_stress = |paiements_en_retard| / |paiements_totaux_analysés|

Niveaux :
  < 0.20 : LOW  — situation saine
  0.20 – 0.40 : MEDIUM — vigilance
  > 0.40 : HIGH  — stress de trésorerie significatif
```

**Propension au crédit informel :**

```
Propension = |clients_actifs_sans_historique_formel| / |clients_actifs_90_jours|
```

Cet indicateur mesure la proportion de clients qui achètent à crédit sans que leurs paiements soient tracés dans le système (crédit purement oral). Il signale le manque à gagner en termes de données pour le scoring crédit, et incite à la formalisation progressive des remboursements.

**Weekend boost :** le système détecte si nous sommes en vendredi ou samedi (jours de marché hebdomadaire en milieu burkinabè) et signale le boost de ventes estimé (+15 à +25 % selon les données historiques), avec recommandation d'adaptation du personnel et du stock.

---

## Conclusion du chapitre

Ce chapitre a présenté en détail les sept composants du module d'intelligence artificielle et d'analyse de données de GesCom-BF. Chaque composant a été décrit avec honnêteté intellectuelle : Prophet, Random Forest, Isolation Forest, K-Means et Apriori constituent de véritables modules de Machine Learning ; la classification ABC/XYZ est une analytique BI déterministe ; le modèle de churn est une heuristique statistique justifiée par l'absence de données labellisées ; l'élasticité prix relève de l'économétrie descriptive.

Les contributions originales par rapport aux ERP génériques sont multiples : la contextualisation burkinabè de Prophet (jours fériés locaux), l'explicabilité SHAP du scoring crédit (transparence des décisions dans le contexte du crédit informel), la détermination automatique de K pour la segmentation RFM, et le module de contexte africain BF qui n'a aucun équivalent dans les solutions commerciales existantes.

Le chapitre suivant présente la stratégie de tests qui garantit la qualité de ces modules, le pipeline CI/CD et les résultats de déploiement.

---

*— Fin du Chapitre 4 —*
