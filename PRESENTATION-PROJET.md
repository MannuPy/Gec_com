# Sarmt_Com — Document de présentation projet

---

## 1. Contexte et problématique

Au Burkina Faso, les quincailleries et boutiques de pièces détachées (automobile, motocycle, BTP) fonctionnent encore largement avec des méthodes manuelles : cahiers de stock, fichiers Excel non centralisés, remises accordées à l'oral sans traçabilité. Lorsqu'une entreprise possède un dépôt central et plusieurs boutiques de vente, l'absence de système informatique centralisé engendre des ruptures de stock non anticipées, des erreurs de prix entre clients simples et techniciens, et une impossibilité totale de piloter l'activité sur données réelles.

**Problématique centrale :**
> Comment doter les petites et moyennes quincailleries du Burkina Faso d'un outil de gestion commerciale centralisé, fiable, accessible même en cas de coupure internet, et capable de transformer leurs données de vente en aide à la décision ?

Les solutions existantes (Odoo, Sage, Wave ERP) ont été étudiées : elles sont soit trop coûteuses, soit trop complexes à déployer, soit incapables de fonctionner sans connexion internet stable — une contrainte critique en zone à connectivité intermittente.

---

## 2. Présentation générale du projet

**GesCom-BF** est une application web de gestion commerciale et de stock, conçue spécifiquement pour les quincailleries burkinabè. Elle est développée selon une architecture SaaS (Software as a Service) multi-tenant, ce qui signifie qu'une seule instance de l'application peut servir plusieurs entreprises clientes de façon isolée.

Le projet couvre l'intégralité du cycle de vie d'une vente : de la réception fournisseur au dépôt, au transfert vers les boutiques, à la vente au comptoir, jusqu'aux rapports décisionnels et aux analyses prédictives par intelligence artificielle.

### Ce que le projet fait concrètement

- **Gestion des stocks** : suivi en temps réel des niveaux de stock au dépôt central et dans chaque boutique, avec alertes de seuil minimum
- **Gestion des transferts** : mouvements de marchandises entre le dépôt et les boutiques, avec validation et traçabilité complète
- **Gestion des ventes** : double tarification (prix client simple / prix technicien), remises encadrées par rôle, historique des ventes par caissier et par boutique
- **Gestion des fournisseurs** : réceptions, bons de commande, suivi des dettes fournisseurs
- **Gestion des utilisateurs et des droits** : système RBAC (Role-Based Access Control) avec trois rôles — Administrateur, Magasinier, Vendeur — chacun avec des permissions précises
- **Mode hors-ligne (PWA)** : les vendeurs peuvent continuer à enregistrer des ventes même sans internet ; les données se synchronisent automatiquement à la reconnexion
- **Tableaux de bord et rapports** : chiffre d'affaires, marges, top produits, performance par boutique et par période
- **Module d'intelligence artificielle** : prévisions de demande, scoring crédit clients, détection d'anomalies, segmentation clients, analyse des associations de produits (cf. section 4)

---

## 3. Architecture technique

### 3.1 Vue d'ensemble

Le système est structuré en trois couches indépendantes :

- **Frontend** : application React 18 + TypeScript, packagée en Progressive Web App (PWA). Elle communique exclusivement avec le backend via une API REST sécurisée.
- **Backend** : serveur Flask 3.0.3 (Python), organisé en blueprints modulaires. Il expose l'API REST, gère l'authentification JWT, applique le rate limiting (Flask-Limiter) et orchestre les modules ML.
- **Base de données** : MySQL 8.0 hébergé sur PythonAnywhere. Le schéma est géré par SQLAlchemy + Alembic (migrations versionnées).

### 3.2 Principales technologies

| Couche | Technologie | Version |
|---|---|---|
| Frontend | React + TypeScript + Vite | 18 / 5 |
| Backend | Flask + Blueprints | 3.0.3 |
| ORM | SQLAlchemy + Alembic | 2 / 4.0.7 |
| Authentification | Flask-JWT-Extended | 4.6.0 |
| Rate Limiting | Flask-Limiter | 3.8.0 |
| Prévision temporelle | Prophet | 1.1.5 |
| Machine Learning | scikit-learn | 1.5.1 |
| Explicabilité ML | SHAP | 0.45.1 |
| Règles d'association | mlxtend (Apriori) | 0.23.1 |
| Suivi des modèles | MLflow | 2.14.3 |

### 3.3 Déploiement actuel

L'application est hébergée sur **PythonAnywhere** (plan Developer), qui est la plateforme retenue pour le déploiement de production pendant la phase de soutenance. Ce choix est motivé par son coût accessible et sa compatibilité Python native, mais il impose une contrainte importante : **pas de Redis ni de Celery disponibles**, ce qui signifie que les tâches ML asynchrones sont gérées par des threads Python natifs et un script cron (`scripts/cron_train_all.py`) déclenché chaque nuit à 02h00 UTC.

Le déploiement VPS avec Docker Compose (pour la V2 multi-tenant complète) est documenté mais n'est pas l'environnement de soutenance.

### 3.4 Sécurité

- Authentification JWT avec access token (15 min) + refresh token (7 jours)
- Hachage des mots de passe bcrypt
- RBAC : chaque endpoint est protégé par rôle via décorateurs Flask
- Rate limiting sur les endpoints sensibles (login, register) : 5 tentatives/minute par IP
- TLS natif PythonAnywhere (HTTPS obligatoire)
- Audit log des actions sensibles en base de données

---

## 4. Module d'intelligence artificielle et d'analyse de données

C'est la valeur ajoutée principale du projet en termes académiques. Il comprend **7 modules distincts**, avec des niveaux de sophistication variables. La documentation est volontairement honnête sur la nature réelle de chaque technique.

### 4.1 Tableau de synthèse des modules

| Module | Fichier | Technique réelle | Qualification honnête |
|---|---|---|---|
| Prévision de demande | `demand_forecast.py` | **Prophet** (Meta) + sklearn fallback | ML — modèle bayésien de séries temporelles |
| Scoring crédit | `credit_scoring.py` | **Random Forest** + SHAP | ML supervisé + explicabilité |
| Détection d'anomalies | `anomaly_detection.py` | **Isolation Forest** | ML non supervisé |
| Segmentation clients | `rfm_segmentation.py` | **K-Means** + Silhouette | ML non supervisé (clustering) |
| Market Basket | `market_basket.py` | **Apriori** (mlxtend) | ML non supervisé (règles d'association) |
| Classification ABC/XYZ | `abc_xyz.py` | Règles pandas déterministes | **Analytique BI — pas du ML** |
| Churn probability | (dans rfm_segmentation) | P = 1 − e^(−λ×R) | **Heuristique statistique — pas du ML** |

### 4.2 Détail des modules

**Prévision de demande (Prophet)**
Prophet est un modèle de prévision de séries temporelles développé par Meta, qui décompose la tendance, la saisonnalité hebdomadaire/annuelle et l'effet des jours fériés. Le système a été enrichi avec les jours fériés spécifiques au Burkina Faso (Tabaski, Aïd el-Fitr, fête nationale du 11 décembre…). Si l'historique est insuffisant (< 30 jours), le système bascule automatiquement sur une régression sklearn, puis sur une moyenne naive — un design "fail-safe" avec indicateur de fiabilité (`data_confidence: HIGH/MEDIUM/LOW`).

**Scoring crédit (Random Forest + SHAP)**
Le modèle évalue la solvabilité des clients achetant à crédit, sur la base de 6 variables : ancienneté, fréquence d'achat, montant moyen, délai moyen de remboursement, taux de retard, solde dû actuel. Il utilise un `RandomForestClassifier` (200 arbres) avec validation croisée stratifiée. **SHAP (TreeExplainer)** permet de produire pour chaque client une explication des 3 facteurs qui ont le plus influencé son score — point clé pour la transparence du modèle.

*Limite honnête :* si un client n'a pas d'historique de paiement, le système utilise `credit_balance` comme proxy observable (mode `SIMULATED`). Ce mode est signalé explicitement dans la réponse API.

**Détection d'anomalies (Isolation Forest)**
L'algorithme détecte les ventes statistiquement anormales (montant élevé, remise inhabituelle, heure atypique) via un `IsolationForest` entraîné sur l'historique des ventes. Chaque anomalie est accompagnée d'une liste de raisons lisibles ("Remise inhabituelle > 30 %", "Vente hors horaire habituel"…) pour aider le gérant à investiguer.

**Segmentation RFM + K-Means**
Les clients sont segmentés selon 3 dimensions : Récence (R), Fréquence (F), Montant (M). Le nombre de clusters K est déterminé automatiquement par la méthode Silhouette + Davies-Bouldin + Elbow (endpoint `/analytics/rfm-segments/evaluate-k`), ce qui évite de fixer K arbitrairement.

**Probabilité de churn (heuristique)**
Formule : P_churn = 1 − e^(−λ×R), où R est la récence et λ est calibré sur la médiane de récence du portefeuille. Ce n'est **pas un modèle ML** : il n'y a ni entraînement, ni données labellisées. C'est un modèle statistique inspiré de la théorie de la survie (Pareto/NBD), justifié par l'absence totale de labels "client churné" dans les PME ciblées.

**Market Basket Analysis (Apriori)**
Identifie les associations de produits fréquemment achetés ensemble, avec les métriques support, confidence et lift. L'algorithme Apriori (bibliothèque mlxtend) est utilisé en priorité ; un fallback par co-occurrence est activé si la transaction matrix est trop petite.

**Élasticité prix**
Régression log-log sur l'historique des ventes : `log(quantité) = α + β × log(prix_unitaire)`. Le coefficient β est l'élasticité. Un diagnostic est fourni en cas de données insuffisantes.

**Contexte africain BF**
Endpoint qui agrège des informations contextuelles spécifiques à l'environnement commercial burkinabè : événements calendriers (Ramadan, fêtes nationales), boost de ventes du week-end, indice de stress de trésorerie (calculé sur le taux de retards de paiement), propension au crédit informel. Ces indicateurs n'ont pas d'équivalent dans les ERP génériques.

### 4.3 Tests des modules ML

93 tests unitaires pytest couvrent toutes les fonctions ML pures (sans base de données) : logique d'algorithmes, cas limites (données vides, un seul client, montants nuls), cohérence des sorties. Le pipeline CI/CD (GitHub Actions) bloque tout déploiement si un test échoue.

```
93 passed in 3.93s
```

---

## 5. Ce qui est implémenté vs ce qui est en perspective

La documentation du projet distingue explicitement l'état actuel du système de ses perspectives de V2.

### État actuel (soutenance juillet 2026)

| Fonctionnalité | Statut |
|---|---|
| Gestion stock dépôt + boutiques | ✅ Implémenté |
| Transferts inter-sites | ✅ Implémenté |
| Gestion des ventes (double tarif, remises) | ✅ Implémenté |
| Gestion fournisseurs | ✅ Implémenté |
| RBAC (Admin, Magasinier, Vendeur) | ✅ Implémenté |
| Authentification JWT sécurisée | ✅ Implémenté |
| Rate limiting / anti-brute-force | ✅ Implémenté |
| Mode hors-ligne PWA | ✅ Implémenté |
| Tableaux de bord multi-sites | ✅ Implémenté |
| Module IA/ML (7 modules) | ✅ Implémenté |
| Tests unitaires (93 pytest) | ✅ Implémenté |
| CI/CD GitHub Actions | ✅ Actif |
| Monitoring erreurs (Sentry) | ✅ Intégré |
| Endpoint de santé `/health` | ✅ Implémenté |
| SaaS multi-tenant complet | ⚙️ Architecture documentée, isolation logique en place — déploiement multi-tenant non activé en production |
| Application mobile native | 🔮 Perspective V2 |
| Intégration Mobile Money (Orange/Moov) | 🔮 Perspective V2 |
| Comptabilité générale | 🔮 Hors périmètre |

### Précision sur le SaaS multi-tenant

L'architecture multi-tenant est conçue et documentée (modèle shared database, `tenant_id` sur chaque table). En production PythonAnywhere, une seule instance est déployée pour la démonstration (mono-tenant). La bascule multi-tenant complète est prévue pour un déploiement VPS V2 avec Docker Compose.

---

## 6. Structure de la documentation

Le projet est accompagné de **34 documents** couvrant l'ensemble du cycle de vie :

| Domaine | Documents |
|---|---|
| Contexte & besoins | Introduction, étude de marché, analyse des besoins, règles métier |
| Modélisation | Cas d'utilisation, diagrammes UML (classes, séquence, déploiement), MCD/MLD/MPD |
| Architecture | Architecture technique, backend Flask, frontend React, base de données, sécurité |
| API | Spécification REST complète (20 endpoints analytics + tous les blueprints) |
| IA & Données | Machine Learning (détail de chaque module), pipeline ETL, dashboard BI, analyse de données |
| Qualité & Tests | Plan de tests, CI/CD, monitoring |
| Déploiement | Guides PythonAnywhere, configuration production |
| Perspectives | Conclusion, glossaire, annexes |

---

## 7. Points forts académiques

- **Honnêteté technique** : la documentation distingue clairement ce qui est du ML réel (Prophet, Random Forest, Isolation Forest, K-Means, Apriori) de ce qui est de l'analytique BI (ABC/XYZ) ou de l'heuristique statistique (churn). Cette honnêteté est un choix délibéré.
- **Contextualisation locale** : le projet n'est pas un clone d'ERP occidental — Prophet intègre les jours fériés burkinabè, le module de contexte africain BF est spécifique au marché local (Ramadan, saison des pluies, crédit informel).
- **Explicabilité** : SHAP (TreeExplainer) sur le scoring crédit permet de justifier chaque décision du modèle, ce qui est un standard industriel en ML responsable.
- **Architecture robuste face aux contraintes** : la gestion du fallback Prophet → sklearn → naive, le design fail-safe des entraînements ML (l'ancien modèle reste actif en cas d'échec), et le mode offline-first sont des réponses directes aux contraintes réelles du terrain.
- **Couverture de tests** : 93 tests unitaires automatisés sur les fonctions ML, intégrés dans un pipeline CI/CD.

---

## 8. Limites connues et transparence

| Limite | Explication |
|---|---|
| Données de démonstration | L'application fonctionne sur des données simulées (seed) pour la soutenance — aucun client réel n'utilise encore le système en production. |
| Modèles ML sans données réelles | Les modèles sont entraînés sur des données générées. Les performances affichées (métriques) sont cohérentes mais ne représentent pas un cas d'usage réel de plusieurs mois. |
| Rate limiting en mémoire | Flask-Limiter est configuré en `memory://` (pas de Redis sur PythonAnywhere) — les compteurs se réinitialisent au redémarrage du serveur. |
| Multi-tenant non activé en prod | L'architecture est en place mais un seul tenant est déployé pour la démonstration. |
| Frontend non audité TypeScript strict | Le build Vite compile sans erreur, mais un audit TypeScript strict (`noImplicitAny`) n'a pas été réalisé. |

---

## 9. Résumé exécutif pour le maître de suivi

GesCom-BF est un système de gestion commerciale complet, fonctionnel et déployé, répondant à un besoin réel et documenté dans le contexte des PME commerciales burkinabè. Le projet démontre une maîtrise du cycle de développement logiciel de bout en bout — de l'analyse des besoins au déploiement en production — avec une valeur ajoutée tangible par l'intégration de 7 modules analytiques et d'IA, contextualisés pour le marché local.

Les choix techniques sont justifiés, les limites sont documentées honnêtement, et la qualité est assurée par 93 tests automatisés et un pipeline CI/CD actif.

---

Fin de mon document ----