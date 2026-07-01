# CHAPITRE 2 : ANALYSE ET MODÉLISATION DU SYSTÈME

---

## Introduction

Ce chapitre constitue le cœur de la phase d'analyse et de conception du projet. Il traduit les besoins identifiés au chapitre précédent en spécifications formelles et en modèles graphiques précis, selon le formalisme UML 2.5. Nous identifions d'abord les acteurs du système et leurs rôles, puis nous formalisons les besoins fonctionnels et non fonctionnels, avant de produire l'ensemble des diagrammes UML et la modélisation des données. Enfin, les règles de gestion clés qui gouvernent le comportement du système sont explicitées.

---

## 2.1 Acteurs du système et rôles

GesCom-BF repose sur un modèle de contrôle d'accès basé sur les rôles (RBAC). Quatre acteurs interagissent avec le système, dont un acteur système non humain.

**L'Administrateur** est le responsable de l'entreprise ou son délégué informatique. Il dispose d'un accès complet à toutes les fonctionnalités de son tenant : gestion des utilisateurs, consultation de l'ensemble des stocks et des ventes de toutes les boutiques, validation des remises, accès aux journaux d'audit et à tous les modules d'analyse et d'intelligence artificielle. Il est le seul à pouvoir créer, modifier ou désactiver des comptes utilisateurs.

**Le Magasinier** est le responsable du dépôt central. Il gère les réceptions de marchandises des fournisseurs, crée les transferts vers les boutiques, réalise les inventaires du dépôt et consulte les niveaux de stock. Il n'a pas accès aux ventes en boutique ni aux modules analytiques avancés.

**Le Vendeur** est le personnel de caisse en boutique. Il enregistre les ventes (en ligne ou hors-ligne), réceptionne les transferts entrants, consulte le stock de sa boutique et peut appliquer des remises avec l'accord verbal de l'administrateur. Il est rattaché à une boutique précise et ne peut interagir qu'avec les données de ce site.

**Le Système (tâches planifiées)** est un acteur non humain qui déclenche automatiquement les entraînements ML nocturnes, recalcule les prévisions de demande, rafraîchit les scores de solvabilité et détecte les anomalies selon un calendrier défini.

**Tableau 3 : Rôles et permissions principales**

| Action | Administrateur | Magasinier | Vendeur |
|---|---|---|---|
| Gérer les utilisateurs | ✅ | ✗ | ✗ |
| Créer / modifier produits | ✅ | ✅ | ✗ |
| Réceptionner une livraison fournisseur | ✅ | ✅ | ✗ |
| Créer un transfert | ✅ | ✅ | ✗ |
| Réceptionner un transfert | ✅ | ✅ | ✅ |
| Réaliser un inventaire | ✅ | ✅ | ✅ |
| Enregistrer une vente | ✅ | ✗ | ✅ |
| Approuver une remise | ✅ | ✗ | ✗ |
| Consulter dashboard multi-sites | ✅ | ✗ | ✗ |
| Accéder aux modules IA | ✅ | ✗ | ✗ |
| Consulter journaux d'audit | ✅ | ✗ | ✗ |

---

## 2.2 Besoins fonctionnels

Les exigences fonctionnelles (RF) ont été élicitées à partir de l'analyse du terrain et des entretiens avec les utilisateurs cibles. Elles sont classées selon la méthode MoSCoW (Must / Should / Could / Won't).

**Tableau 4 : Exigences fonctionnelles principales**

| ID | Description | Priorité |
|---|---|---|
| RF-01 | Inscription d'une entreprise avec administrateur initial | Must |
| RF-02 | Connexion JWT avec access token (15 min) et refresh token (7 jours) | Must |
| RF-03 | Gestion des utilisateurs et attribution des rôles par l'administrateur | Must |
| RF-04 | Déconnexion et invalidation du refresh token | Must |
| RF-05 | Changement de mot de passe obligatoire à la première connexion | Should |
| RF-06 | Gestion des catégories et marques de produits | Must |
| RF-07 | Création produit avec référence unique, double tarification, seuil de stock | Must |
| RF-08 | Recherche produit tolérante aux fautes de frappe | Should |
| RF-10 | Gestion des fournisseurs (coordonnées, historique achats) | Must |
| RF-11 | Réception marchandises fournisseur avec mise à jour stock dépôt | Must |
| RF-12 | Stock distinct par site (dépôt + chaque boutique) | Must |
| RF-13 | Création de transfert dépôt → boutique avec cycle de statuts | Must |
| RF-14 | Décrémentation/incrémentation automatique du stock à la réception | Must |
| RF-15 | Vente multi-lignes avec tarification automatique (client simple / technicien) | Must |
| RF-16 | Remise parmi {5, 10, 15, 20 %} avec identité de l'approbateur obligatoire | Must |
| RF-17 | Décrémentation du stock boutique à la validation de la vente | Must |
| RF-18 | Vente à crédit avec suivi du solde client | Should |
| RF-20 | Saisie de vente hors-ligne (PWA), synchronisation différée | Must |
| RF-21 à RF-23 | Inventaire physique, saisie des écarts, validation et ajustement | Must |
| RF-24 | Tableau de bord : CA, marges, top produits, par boutique et consolidé | Must |
| RF-25 | Prévision de demande Prophet avec indicateur de fiabilité | Must |
| RF-26 | Scoring crédit clients avec explication SHAP | Should |
| RF-27 | Détection d'anomalies sur ventes et remises avec raisons lisibles | Should |
| RF-28 | Classification ABC/XYZ des produits (analytique BI) | Should |
| RF-30 à RF-32 | Journalisation des événements sensibles, RBAC, consultation des logs | Must |
| RF-33 | Market Basket Analysis — produits fréquemment achetés ensemble | Could |
| RF-34 | Élasticité prix par produit (régression log-log) | Could |
| RF-35 | Indicateurs contexte africain BF | Could |
| RF-36 | Endpoint `/health` (état DB, modèles ML actifs, uptime) | Should |

---

## 2.3 Besoins non fonctionnels

**Tableau 5 : Exigences non fonctionnelles**

| ID | Catégorie | Exigence | Cible mesurable |
|---|---|---|---|
| RNF-01 | Performance | Temps de réponse API (hors traitements ML) | < 200 ms au 95e percentile |
| RNF-02 | Disponibilité | Disponibilité du service | ≥ 99,5 % (hors maintenance planifiée) |
| RNF-03 | Volumétrie | Produits par tenant | Jusqu'à 20 000 |
| RNF-04 | Volumétrie | Transactions de vente / jour / tenant | Jusqu'à 2 000 |
| RNF-05 | Volumétrie | Boutiques par tenant | Jusqu'à 50 |
| RNF-07 | Sécurité | Chiffrement en transit | TLS 1.2+ obligatoire (HTTPS) |
| RNF-08 | Sécurité | Stockage des mots de passe | bcrypt — jamais en clair |
| RNF-09 | Sécurité | Expiration des tokens JWT | Access : 15 min / Refresh : 7 jours |
| RNF-10 | Offline | Continuité de la vente sans réseau | 100 % des fonctions de caisse, sync < 5 min après reconnexion |
| RNF-11 | Sauvegarde | Fréquence des sauvegardes | Quotidienne, rétention 30 jours |
| RNF-14 | Qualité | Couverture des tests ML automatisés | 93 tests pytest, bloque le déploiement si échec |
| RNF-15 | Déploiement | Environnements cibles | PythonAnywhere (prod V1) + Docker Compose (prod V2) |
| RNF-17 | Observabilité | Traçabilité des prédictions IA | Chaque prédiction référence la version du modèle (data lineage) |
| RNF-18 | Conformité | Rétention des journaux d'audit | 1 an minimum |

---

## 2.4 Modélisation UML

### 2.4.1 Diagramme de cas d'utilisation global

Le diagramme ci-dessous présente l'ensemble des cas d'utilisation du système, regroupés par sous-système, et les acteurs associés.

**Figure 4 : Diagramme de cas d'utilisation global** *(à insérer)*

```
[Diagramme Mermaid — à exporter en image pour le rendu Word/PDF]

flowchart LR
    Admin([Administrateur])
    Mag([Magasinier])
    Vendeur([Vendeur])
    Systeme([Système / Tâches planifiées])

    subgraph SS1[Authentification & Sécurité]
        UC1((UC-01 Se connecter))
        UC2((UC-02 Se déconnecter))
        UC3((UC-03 Gérer les utilisateurs))
        UC4((UC-04 Consulter les journaux d'audit))
    end

    subgraph SS2[Catalogue & Approvisionnement]
        UC5((UC-05 Gérer les produits))
        UC6((UC-06 Gérer les fournisseurs))
        UC7((UC-07 Réceptionner une livraison))
    end

    subgraph SS3[Stock & Transferts]
        UC8((UC-08 Créer un transfert))
        UC9((UC-09 Réceptionner un transfert))
        UC10((UC-10 Réaliser un inventaire))
    end

    subgraph SS4[Ventes]
        UC11((UC-11 Enregistrer une vente))
        UC12((UC-12 Appliquer une remise))
        UC13((UC-13 Vendre à crédit))
        UC14((UC-14 Synchroniser ventes offline))
    end

    subgraph SS5[Pilotage & IA]
        UC15((UC-15 Consulter le dashboard))
        UC16((UC-16 Prévision de rupture de stock))
        UC17((UC-17 Calculer un score de solvabilité))
        UC18((UC-18 Détecter une anomalie))
    end

    Admin --> UC1 & UC2 & UC3 & UC4 & UC5 & UC6 & UC8 & UC15 & UC17 & UC18
    Mag --> UC1 & UC2 & UC6 & UC7 & UC8 & UC9 & UC10
    Vendeur --> UC1 & UC2 & UC9 & UC10 & UC11 & UC12 & UC13 & UC14
    Systeme --> UC16 & UC18

    UC12 -.extends.-> UC11
    UC13 -.extends.-> UC11
    UC14 -.include.-> UC11
    UC9 -.include.-> UC8
```

### 2.4.2 Description détaillée de cas d'utilisation clés

Nous présentons ici la description détaillée de trois cas d'utilisation représentatifs du cœur fonctionnel du système.

#### UC-11 : Enregistrer une vente

**Tableau 6 : Description du CU-11 "Enregistrer une vente"**

| Champ | Détail |
|---|---|
| **Identifiant** | UC-11 |
| **Acteur principal** | Vendeur |
| **Préconditions** | Le vendeur est authentifié et rattaché à une boutique |
| **Scénario principal** | 1. Le vendeur recherche les produits (recherche tolérante aux fautes — RF-08). 2. Il ajoute les lignes produit/quantité. 3. Le système applique automatiquement le tarif selon le profil client (RG-21). 4. Le vendeur valide. 5. Le système vérifie la disponibilité stock (RG-24) et décrémente le stock boutique. 6. La vente est enregistrée au statut VALIDÉE avec un reçu généré. 7. L'événement SALE_CREATED est journalisé. |
| **Scénarios alternatifs** | A1 : stock insuffisant → vente bloquée. A2 : mode hors-ligne → vente stockée localement (UC-14). A3 : application d'une remise → extension UC-12. A4 : vente à crédit → extension UC-13. |
| **Postconditions** | Stock mis à jour, vente immuable (RG-27), reçu généré. |
| **Exigences liées** | RF-15, RF-16, RF-17, RF-19, RG-20 à RG-27 |

#### UC-08 : Créer un transfert (Dépôt → Boutique)

| Champ | Détail |
|---|---|
| **Identifiant** | UC-08 |
| **Acteur principal** | Magasinier (ou Administrateur) |
| **Préconditions** | Stock dépôt suffisant pour les quantités demandées |
| **Scénario principal** | 1. L'acteur sélectionne site source (dépôt) et destination (boutique). 2. Il ajoute les lignes produit/quantité. 3. Le système vérifie la disponibilité (RG-18). 4. Création du transfert en statut BROUILLON puis EN_TRANSIT : stock source décrémenté (RG-17). 5. Journalisation de l'événement. |
| **Scénarios alternatifs** | A1 : stock insuffisant → transfert bloqué, message d'erreur. A2 : annulation avant EN_TRANSIT → statut ANNULÉ, aucun impact stock. |
| **Postconditions** | Le transfert est visible par la boutique en statut EN_TRANSIT. |
| **Exigences liées** | RF-13, RF-14, RG-15 à RG-18 |

#### UC-14 : Synchroniser les ventes hors-ligne

| Champ | Détail |
|---|---|
| **Identifiant** | UC-14 |
| **Acteur principal** | Système (Service Worker), déclenché automatiquement |
| **Préconditions** | Des ventes existent en file locale IndexedDB avec statut EN_ATTENTE_SYNC |
| **Scénario principal** | 1. La connexion réseau est rétablie. 2. Le Service Worker envoie les ventes par lot (POST /sync/sales) avec UUID local et horodatage client. 3. Le serveur traite chaque vente : si stock suffisant → VALIDÉE ; si stock insuffisant → EN_CONFLIT (RG-29). 4. Le serveur renvoie les statuts, le client met à jour son cache local. |
| **Postconditions** | Toutes les ventes locales sont synchronisées ou marquées EN_CONFLIT pour revue admin. |
| **Exigences liées** | RF-20, RG-28, RG-29, RG-30 |

### 2.4.3 Diagramme de classes

Le diagramme de classes décrit la structure statique du système : les entités métier, leurs attributs principaux et les relations qui les unissent.

**Figure 7 : Diagramme de classes global** *(à insérer)*

Les entités principales sont : `Company` (tenant), `Branch` (dépôt ou boutique), `User`, `Role`, `Permission`, `Product`, `Category`, `Brand`, `Supplier`, `Customer`, `Stock`, `StockMovement`, `Transfer`, `TransferLine`, `Sale`, `SaleLine`, `Discount`, `Inventory`, `InventoryLine`, `AuditLog`, `Prediction`, `MlModel`.

Relations clés :
- Une `Company` possède un dépôt central unique et 0 à N boutiques (`Branch`)
- Un `User` est rattaché à un `Role` (ADMIN / MAGASINIER / VENDEUR) et optionnellement à une `Branch`
- Un `Product` possède un `Stock` par `Branch` (ligne distincte par couple produit/site)
- Une `Sale` est composée de 1 à N `SaleLine` et peut comporter un `Discount` (avec `approved_by_user_id`)
- Un `Transfer` est composé de 1 à N `TransferLine` et relie un site source à un site destination
- Toute action sensible génère un enregistrement `AuditLog` immuable
- Toute prédiction ML génère un enregistrement `Prediction` référençant la version du modèle

### 2.4.4 Diagrammes de séquence

Nous présentons les deux diagrammes de séquence les plus représentatifs.

**Figure 8 : Diagramme de séquence — Processus de vente (UC-11)** *(à insérer)*

Le flux est le suivant : le Vendeur saisit les produits dans le Frontend React → la requête `POST /api/v1/sales` est envoyée à l'API Flask → l'API vérifie le stock en base MySQL → si stock suffisant, la vente est enregistrée et le stock décrémenté dans la même transaction → la réponse contient l'identifiant de la vente et le reçu → le journal d'audit est mis à jour.

**Figure 9 : Diagramme de séquence — Transfert inter-sites (UC-08 + UC-09)** *(à insérer)*

Le flux comprend deux phases : (1) création par le Magasinier avec passage en EN_TRANSIT et décrémentation du stock source, (2) réception par le Vendeur avec passage en REÇU et incrémentation du stock destination.

**Diagramme de séquence — Entraînement d'un modèle ML (UC-16)**

La séquence d'entraînement nocturne est déclenchée par le cron PythonAnywhere : le script `cron_train_all.py` appelle successivement les 6 modules ML. Pour chaque module, le pipeline ETL extrait les données de MySQL, entraîne le modèle, sauvegarde le fichier `.joblib` via MLflow, met à jour la table `ml_models` (statut ACTIVE), et enregistre les prédictions dans la table `predictions`. En cas d'échec, l'ancien modèle reste actif (design fail-safe).

### 2.4.5 Diagramme de déploiement

**Figure 10 : Diagramme de déploiement (PythonAnywhere)** *(à insérer)*

L'architecture de déploiement comprend trois nœuds principaux :
- **Poste client** : navigateur web exécutant la PWA React (avec Service Worker pour le mode offline)
- **Serveur PythonAnywhere** : serveur uWSGI hébergeant l'application Flask, avec le script cron nocturne pour les entraînements ML
- **Base de données** : instance MySQL managée PythonAnywhere (`<user>$gescom_bf`)

La communication entre le client et le serveur se fait exclusivement en HTTPS (TLS natif PythonAnywhere). Les artefacts ML (fichiers `.joblib`) sont stockés sur le système de fichiers du serveur, référencés par MLflow.

---

## 2.5 Modélisation des données

### 2.5.1 Modèle Conceptuel de Données (MCD)

Le MCD représente les entités métier et leurs associations, indépendamment de toute technologie de base de données.

**Figure 11 : Modèle Conceptuel de Données (MCD)** *(à insérer)*

Les entités principales et leurs associations sont :
- `ENTREPRISE` (1,1) — gère — (0,N) `SITE` (dépôt ou boutique)
- `SITE` (1,1) — détient — (0,N) `STOCK` — (1,1) `PRODUIT`
- `PRODUIT` (0,N) — appartient à — (1,1) `CATÉGORIE`
- `PRODUIT` (0,N) — est de marque — (1,1) `MARQUE`
- `VENTE` (1,N) — composée de — (1,N) `PRODUIT` (via `LIGNE_VENTE`)
- `VENTE` (0,1) — bénéficie de — (0,1) `REMISE` (approuvée par `UTILISATEUR`)
- `TRANSFERT` (1,N) — porte sur — (1,N) `PRODUIT` (via `LIGNE_TRANSFERT`)
- `CLIENT` (0,N) — effectue — (0,N) `VENTE`
- `FOURNISSEUR` (0,N) — livre — (0,N) `PRODUIT` (via `RÉCEPTION`)

### 2.5.2 Modèle Logique de Données (MLD)

Le MLD est la traduction relationnelle du MCD : chaque entité devient une table, chaque association se traduit par des clés étrangères.

Les tables principales du système sont : `companies`, `branches`, `users`, `roles`, `permissions`, `role_permissions`, `categories`, `brands`, `products`, `suppliers`, `customers`, `stock`, `stock_movements`, `supplier_receptions`, `supplier_reception_lines`, `transfers`, `transfer_lines`, `sales`, `sale_lines`, `discounts`, `inventories`, `inventory_lines`, `audit_logs`, `predictions`, `ml_models`.

Le schéma relationnel complet est représenté par le diagramme ER de la figure 12 *(à insérer)*.

### 2.5.3 Dictionnaire des données (tables principales)

Nous présentons ici le dictionnaire des cinq tables les plus centrales du système.

**Tableau 7 : Table `products`**

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| id | UUID | PK | Identifiant unique du produit |
| category_id | UUID | FK→categories | Catégorie du produit |
| brand_id | UUID | FK→brands | Marque du produit |
| name | VARCHAR(200) | NN | Désignation en français |
| name_moore | VARCHAR(200) | — | Désignation en mooré (RF-09) |
| reference | VARCHAR(100) | NN, UNIQUE | Référence interne unique (RG-07) |
| purchase_price | NUMERIC(12,2) | NN, > 0 | Prix d'achat (RG-08) |
| retail_price | NUMERIC(12,2) | NN, ≥ purchase_price | Prix client simple (RG-09) |
| technician_price | NUMERIC(12,2) | NN, ≤ retail_price | Prix technicien (RG-10) |
| is_active | BOOLEAN | NN, défaut TRUE | Suppression logique (RG-11) |
| created_at | TIMESTAMPTZ | NN | Date de création |

**Tableau 8 : Table `sales`**

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| id | UUID | PK | Identifiant de la vente |
| branch_id | UUID | NN, FK→branches | Boutique de vente (RG-20) |
| seller_id | UUID | NN, FK→users | Vendeur (RG-20) |
| customer_id | UUID | FK→customers, nullable | Client (obligatoire si crédit — RG-26) |
| status | VARCHAR(20) | NN | VALIDÉE / EN_ATTENTE_SYNC / EN_CONFLIT / ANNULÉE / AVOIR_ÉMIS |
| channel | VARCHAR(10) | NN | ONLINE ou OFFLINE |
| offline_uuid | UUID | UNIQUE, nullable | UUID client pour idempotence (RG-28) |
| total_amount | NUMERIC(14,2) | NN, ≥ 0 | Montant total (RG-25) |
| created_at | TIMESTAMPTZ | NN | Date d'enregistrement serveur |
| client_created_at | TIMESTAMPTZ | nullable | Horodatage de saisie client (offline) |

**Tableau 9 : Table `customers`**

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| id | UUID | PK | Identifiant client |
| name | VARCHAR(150) | NN | Nom du client |
| phone | VARCHAR(30) | — | Téléphone |
| type_client | VARCHAR(20) | NN, SIMPLE ou TECHNICIEN | Détermine le tarif appliqué (RG-21) |
| solde_du | NUMERIC(12,2) | NN, défaut 0 | Solde dû (crédit informel — RG-26) |
| credit_score | NUMERIC(5,2) | nullable, 0–100 | Score de solvabilité ML (RG-39) |
| score_updated_at | TIMESTAMPTZ | — | Date du dernier calcul du score |

**Table `stock`** : une ligne par couple (product_id, branch_id), avec `quantity` (≥ 0), `min_stock` (seuil d'alerte par site — RG-12) et `updated_at`.

**Table `audit_logs`** : enregistre tout événement sensible avec `user_id`, `event_type`, `entity`, `entity_id`, valeurs `before`/`after` en JSON, `created_at`. Les enregistrements sont immuables (pas d'UPDATE ni DELETE — RG-35).

---

## 2.6 Règles de gestion clés

Les règles de gestion (RG) sont le pont entre les besoins métier et leur implémentation technique. Elles sont appliquées au niveau applicatif (Flask + Marshmallow) et renforcées au niveau base de données (contraintes CHECK, index uniques).

**Tableau 10 : Règles de gestion clés**

| Référence | Domaine | Règle |
|---|---|---|
| RG-01 | Structure | Une entreprise possède **un seul dépôt central** et 0 à N boutiques |
| RG-04 | RBAC | Un Vendeur ne peut interagir qu'avec les données de **sa boutique** |
| RG-07 | Produits | La référence produit est unique au sein d'une entreprise |
| RG-08/09/10 | Tarification | `prix_achat > 0` ; `prix_client ≥ prix_achat` ; `prix_technicien ≤ prix_client` |
| RG-12 | Stock | Le seuil minimum est défini **par produit ET par site** |
| RG-16 | Transferts | Cycle de vie : `BROUILLON → EN_TRANSIT → REÇU` (ou `ANNULÉ`) |
| RG-17 | Transferts | Stock source décrémenté à EN_TRANSIT ; stock destination incrémenté à REÇU |
| RG-21 | Ventes | Tarif technicien appliqué automatiquement si `type_client = TECHNICIEN` |
| RG-22 | Remises | Remises limitées à {0, 5, 10, 15, 20 %} — toute autre valeur rejetée par l'API |
| RG-23 | Remises | Toute remise > 0 % doit référencer l'administrateur approbateur (`approved_by_user_id`) |
| RG-25 | Ventes | Total = Σ(quantité × prix_unitaire × (1 − remise)) sur toutes les lignes |
| RG-26 | Crédit | Vente à crédit impossible sans `customer_id` identifié |
| RG-27 | Ventes | Vente validée **immuable** — toute correction passe par un avoir (vente négative) |
| RG-29 | Offline | Conflit de synchronisation → statut `EN_CONFLIT`, jamais rejeté silencieusement |
| RG-35 | Audit | Journaux d'audit immuables, rétention 1 an minimum |
| RG-38 | IA | Alerte rupture si stock < seuil_min **OU** prévision Prophet < 0 dans les 7 jours |
| RG-41 | Multi-tenant | Toute requête API est scopée au `tenant_id` extrait du JWT |

---

## Conclusion du chapitre

Ce chapitre a établi le fondement formel du système GesCom-BF. La définition des acteurs et de leurs rôles a permis de délimiter précisément les périmètres de responsabilité. L'élicitation des besoins fonctionnels (36 exigences RF) et non fonctionnels (18 exigences RNF) fournit une base contractuelle claire entre la vision métier et l'implémentation technique. Les diagrammes UML produits — cas d'utilisation, classes, séquences et déploiement — constituent le référentiel de conception qui a guidé tout le développement. Enfin, la modélisation des données (MCD, MLD, dictionnaire) et les règles de gestion formalisent les invariants que le système doit respecter en toutes circonstances.

Le chapitre suivant s'appuie sur ces fondations pour décrire les choix d'architecture technique et la réalisation concrète du système.

---

---

# CHAPITRE 3 : ARCHITECTURE TECHNIQUE ET RÉALISATION

---

## Introduction

Ce chapitre décrit les choix techniques qui ont gouverné la construction de GesCom-BF et la réalisation concrète du système. Partant des spécifications du chapitre précédent, nous présentons l'architecture globale de l'application, justifions chaque choix technologique, détaillons les mécanismes de sécurité, expliquons le fonctionnement du mode hors-ligne, décrivons l'API REST et l'architecture SaaS multi-tenant, et présentons les interfaces utilisateur produites.

---

## 3.1 Architecture globale (3-tiers, API-first)

GesCom-BF repose sur une architecture **3-tiers avec séparation stricte des couches** et une approche **API-first** : le backend expose exclusivement une API REST JSON, consommée par le frontend React de façon découplée. Cette séparation présente plusieurs avantages : le frontend peut être remplacé ou complété (application mobile native, future V2) sans modification du backend ; les deux couches peuvent être déployées et mises à l'échelle indépendamment ; les tests d'intégration peuvent cibler l'API directement.

**Figure 12 : Architecture globale 3-tiers de GesCom-BF** *(à insérer)*

Les trois couches sont :

- **Couche Présentation** : application React 18 + TypeScript, packagée en PWA. Elle communique avec le backend via des appels HTTP REST sécurisés, gère l'état local avec React Query (cache, invalidation, synchronisation), et stocke les données offline dans IndexedDB via Dexie.js.

- **Couche Application** : serveur Flask 3.0.3, organisé en blueprints modulaires (auth, products, stock, sales, transfers, inventory, reports, analytics, users). Il gère l'authentification JWT, le rate limiting, la validation des entrées (Marshmallow), la logique métier, l'orchestration ML et l'API REST. Sur PythonAnywhere, le serveur d'application est uWSGI.

- **Couche Données** : base de données MySQL 8.0 hébergée sur PythonAnywhere pour la production V1. Le schéma est géré par SQLAlchemy (ORM) et Alembic (migrations versionnées). Les artefacts ML (fichiers `.joblib`) sont stockés sur le système de fichiers du serveur et référencés par MLflow.

---

## 3.2 Choix technologiques justifiés

### 3.2.1 Backend : Flask 3.0.3 + Blueprints + SQLAlchemy

**Flask** a été retenu comme framework backend pour plusieurs raisons complémentaires. Sa légèreté et sa flexibilité permettent de construire une API REST modulaire sans sur-ingénierie. Sa compatibilité native avec l'écosystème scientifique Python (scikit-learn, Prophet, SHAP, mlxtend) évite toute rupture de stack entre le backend API et les modules ML : les deux s'exécutent dans le même processus Python, sans appel inter-services.

L'organisation en **Blueprints** découpe l'application en modules indépendants (`auth`, `products`, `stock`, `sales`, `transfers`, `analytics`…), facilitant la maintenance et les tests unitaires par domaine.

**SQLAlchemy** (ORM) permet d'écrire la logique d'accès aux données en Python pur, avec une compatibilité transparente entre MySQL (production PythonAnywhere) et PostgreSQL (développement Docker et future V2 multi-tenant). **Alembic** gère les migrations de schéma de façon versionnée, garantissant la reproductibilité des déploiements.

**Marshmallow** est utilisé pour la validation stricte des entrées et la sérialisation des sorties, appliquant les règles de gestion (RG-22 : remises dans {0,5,10,15,20 %}) dès la couche de validation.

### 3.2.2 Frontend : React 18 + TypeScript + Vite (PWA)

**React 18** a été choisi pour sa maturité, son écosystème riche et ses nouvelles fonctionnalités (Concurrent Rendering) qui améliorent la réactivité de l'interface. **TypeScript** apporte un typage statique fort, réduisant significativement les bugs à l'exécution et améliorant la maintenabilité — particulièrement important pour un frontend qui consomme une API complexe avec de nombreux types de réponses.

**Vite** remplace Create React App pour un build ultra-rapide (Hot Module Replacement quasi-instantané en développement) et des bundles optimisés en production.

**React Query** gère le cache des données API côté client : chaque requête est mise en cache, invalidée intelligemment après une mutation, et synchronisée en arrière-plan — éliminant la plupart du code de gestion d'état manuel.

Le packaging en **Progressive Web App (PWA)** via un Service Worker (Workbox) permet l'installation sur l'écran d'accueil d'un appareil, le chargement hors-ligne de l'interface (App Shell), et la synchronisation différée des ventes via la Background Sync API.

### 3.2.3 Base de données : MySQL 8.0 (PythonAnywhere)

**MySQL 8.0** est la base de données de production pour la V1, imposée par les contraintes de l'hébergement PythonAnywhere (plan Developer) qui propose MySQL managé. La compatibilité est assurée par la détection automatique du dialecte dans `backend/app/utils/db_dialect.py` : selon la valeur de `DATABASE_URL`, SQLAlchemy adapte le DDL généré par Alembic (types, contraintes, syntaxe).

Pour le développement local et la V2 multi-tenant, **PostgreSQL 16** sera utilisé, grâce à sa prise en charge native des schémas par tenant (`SET search_path TO tenant_<slug>`) et de fonctionnalités avancées comme JSONB, les index partiels et le partitionnement.

**Tableau 11 : Choix technologiques et justifications**

| Couche | Technologie | Version | Justification principale |
|---|---|---|---|
| Backend framework | Flask + Blueprints | 3.0.3 | Léger, compatible écosystème ML Python, modulaire |
| ORM | SQLAlchemy + Alembic | 2 / 4.0.7 | Compatible MySQL/PostgreSQL, migrations versionnées |
| Validation | Marshmallow | 3.21.3 | Validation stricte + sérialisation, DRY |
| Authentification | Flask-JWT-Extended | 4.6.0 | JWT stateless adapté SPA/PWA, refresh token |
| Rate limiting | Flask-Limiter | 3.8.0 | Anti-brute-force, compatible PythonAnywhere (sans Redis) |
| Frontend framework | React 18 + TypeScript | 18 / 5 | Maturité, typage fort, PWA compatible |
| Build tool | Vite | 5 | Build rapide, HMR instantané |
| Cache API client | React Query | 5 | Cache intelligent, synchronisation en arrière-plan |
| DB production | MySQL 8.0 | 8.0 | Imposé par PythonAnywhere (plan Developer) |
| DB développement | PostgreSQL 16 | 16 | Multi-tenant natif (schémas), full-featured |
| ML principal | scikit-learn | 1.5.1 | Standard, Random Forest, Isolation Forest, K-Means |
| Prévision temporelle | Prophet | 1.1.5 | Séries temporelles + jours fériés locaux |
| Explicabilité ML | SHAP | 0.45.1 | TreeExplainer, standard industriel |
| Règles d'association | mlxtend | 0.23.1 | Algorithme Apriori |
| Suivi des modèles | MLflow | 2.14.3 | Registry, métriques, artefacts |
| Monitoring erreurs | Sentry | sentry-sdk 2.x | Alertes temps réel, stack traces en production |
| Serveur WSGI | uWSGI (prod) / Gunicorn (VPS) | — | uWSGI natif PythonAnywhere |

---

## 3.3 Sécurité applicative

### 3.3.1 RBAC et authentification JWT

L'authentification repose sur **JSON Web Tokens (JWT)** via Flask-JWT-Extended. Deux tokens sont délivrés à la connexion : un **access token** (durée de vie : 15 minutes) transmis dans l'en-tête `Authorization: Bearer`, et un **refresh token** (durée de vie : 7 jours) stocké dans un cookie HttpOnly côté client (inaccessible par JavaScript, protégé contre le vol XSS).

Le contrôle d'accès **RBAC** est implémenté par des décorateurs Python sur chaque endpoint Flask. Chaque rôle dispose d'un ensemble de permissions granulaires (codes comme `sales.create`, `discounts.approve`, `analytics.read`) vérifiées à chaque requête. Le `tenant_id` extrait du JWT garantit que chaque requête ne peut accéder qu'aux données du tenant de l'utilisateur connecté (RG-41).

Les mots de passe sont systématiquement hachés avec **bcrypt** — ils ne sont jamais stockés en clair ni même loggés.

### 3.3.2 Rate limiting (Flask-Limiter)

**Flask-Limiter 3.8.0** protège les endpoints sensibles contre les attaques par force brute. Les limites appliquées sont :

- `POST /auth/login` : 5 tentatives par minute par adresse IP
- `POST /auth/register` : 3 tentatives par heure par IP
- Endpoints analytics (entraînement ML) : 2 requêtes par minute par utilisateur

Le stockage des compteurs est en **mémoire** (`memory://`), compatible avec les contraintes PythonAnywhere (pas de Redis disponible). Cette configuration est suffisante pour la V1 mono-tenant ; la V2 utilisera Redis pour la persistance des compteurs entre redémarrages.

### 3.3.3 Audit log et traçabilité

Un **journal d'audit complet** est maintenu dans la table `audit_logs`. Chaque événement sensible génère un enregistrement avec : horodatage UTC, identifiant de l'utilisateur, type d'événement (LOGIN_SUCCESS, SALE_CREATED, DISCOUNT_APPLIED, TRANSFER_VALIDATED, PRICE_MODIFIED…), entité concernée, et valeurs avant/après en JSON.

Les journaux sont **immuables** : aucun endpoint ne permet de modifier ou supprimer un enregistrement d'audit (RG-35). La rétention minimale est de 1 an (RNF-18). L'administrateur peut filtrer les journaux par utilisateur, type d'événement et période via l'interface.

---

## 3.4 Mode hors-ligne (PWA + Service Worker + IndexedDB)

Le mode hors-ligne est l'une des fonctionnalités différenciatrices de GesCom-BF, directement motivée par la réalité des coupures réseau au Burkina Faso.

**Figure 14 : Schéma du mode hors-ligne PWA** *(à insérer)*

L'architecture offline repose sur trois composants complémentaires.

**L'App Shell (Service Worker — Workbox)** met en cache les ressources statiques de l'application (HTML, CSS, JavaScript, polices) lors de la première visite. Les visites suivantes chargent l'interface instantanément, même sans réseau.

**Le Cache catalogue (IndexedDB via Dexie.js)** stocke localement le catalogue produits (noms, références, prix simple et technicien) et les niveaux de stock de la boutique, rafraîchis périodiquement lorsque la connexion est disponible. En mode offline, le vendeur peut rechercher et ajouter des produits au panier depuis ce cache local.

**La file de synchronisation (Background Sync API)** est la pièce centrale du mécanisme offline. Chaque vente créée sans connexion est écrite dans une table IndexedDB `sync_queue` avec un UUID généré côté client (RG-28). Dès la reconnexion, le Service Worker déclenche automatiquement l'envoi par lot de ces ventes en attente vers l'endpoint `POST /sync/sales`. En cas de conflit de stock (vente concurrente réalisée en ligne entre-temps), la vente est acceptée mais marquée `EN_CONFLIT` pour revue par l'administrateur — elle n'est jamais rejetée silencieusement (RG-29).

---

## 3.5 API REST — Principaux endpoints

L'API REST de GesCom-BF est documentée selon la norme OpenAPI 3.0. Elle est organisée en 8 blueprints, exposant au total plus de 60 endpoints.

**Conventions** : toutes les URLs sont préfixées par `/api/v1/`. Toutes les réponses sont en JSON. Les erreurs suivent un format uniforme `{ "error": { "code": "...", "message": "..." } }`. La pagination est systématique sur les listes (`?page=1&per_page=20`).

Les endpoints les plus représentatifs sont présentés ci-dessous.

| Méthode | Endpoint | Rôle requis | Description |
|---|---|---|---|
| POST | /auth/login | — | Authentification, retourne les JWT |
| POST | /auth/refresh | — | Renouvellement de l'access token |
| GET | /products | Tous | Liste des produits (filtrée par boutique pour Vendeur) |
| POST | /products | Admin / Mag. | Création d'un produit |
| GET | /stock | Tous | Niveaux de stock (scopés au site de l'utilisateur) |
| POST | /transfers | Admin / Mag. | Création d'un transfert |
| PATCH | /transfers/{id}/receive | Tous | Réception d'un transfert (statut → REÇU) |
| POST | /sales | Vendeur | Enregistrement d'une vente |
| POST | /sync/sales | Vendeur | Synchronisation des ventes offline (lot) |
| GET | /analytics/dashboard | Admin | Tableau de bord multi-sites |
| GET | /analytics/forecast | Admin | Prévisions de demande Prophet |
| GET | /analytics/rfm-segments | Admin | Segmentation clients RFM |
| GET | /analytics/basket | Admin | Règles d'association Market Basket |
| GET | /analytics/credit-scores | Admin | Scores de solvabilité clients |
| GET | /analytics/anomalies | Admin | Ventes et remises signalées comme anomalies |
| POST | /analytics/ml/train | Admin | Déclenchement manuel d'un entraînement ML |
| GET | /health | — | État du système (DB, modèles ML, uptime) |
| GET | /audit-logs | Admin | Journaux d'audit filtrables |

---

## 3.6 Architecture SaaS multi-tenant

### 3.6.1 Modèle shared database / tenant_id

GesCom-BF a été conçu dès l'origine pour supporter plusieurs entreprises clientes (tenants) sur une même instance. La stratégie d'isolation retenue pour la V1 est le modèle **shared database avec colonne `tenant_id`** (ou `company_id`) sur chaque table de données. Cette approche est la plus simple à mettre en œuvre et convient parfaitement à la phase académique.

Le `tenant_id` est extrait du JWT à chaque requête par un middleware Flask, puis injecté automatiquement dans toutes les requêtes SQLAlchemy via le contexte de l'application. Aucune donnée d'un tenant ne peut être visible par un autre (RG-41).

Pour la V2, la stratégie cible est le modèle **schema-per-tenant sur PostgreSQL** : chaque entreprise cliente dispose de son propre schéma PostgreSQL (`tenant_<slug>`), offrant une isolation plus forte et une performance accrue grâce à des index plus petits.

### 3.6.2 État actuel (mono-tenant V1) et cible V2

**État actuel (production PythonAnywhere — soutenance juillet 2026) :** une seule instance est déployée, correspondant à un seul tenant de démonstration. L'endpoint `POST /companies/register` (inscription d'un nouveau tenant) retourne `503 MULTI_TENANT_UNAVAILABLE` sur cette configuration, puisque le déploiement multi-tenant complet nécessite PostgreSQL et un VPS avec Docker Compose.

**Cible V2 (post-soutenance) :** déploiement sur VPS avec Docker Compose (Flask + PostgreSQL + Nginx + Celery + Redis), activation du schema-per-tenant, portail d'auto-inscription, et tableau de bord Super-Administrateur pour la gestion des tenants et de la facturation.

---

## 3.7 Présentation des interfaces utilisateur

Cette section présente les interfaces principales de GesCom-BF. Les captures d'écran sont à insérer dans la version finale du mémoire.

### 3.7.1 Tableau de bord principal

**Figure 21 : Capture — Tableau de bord principal** *(à insérer)*

Le tableau de bord est la première page affichée à l'administrateur après connexion. Il présente en un coup d'œil les indicateurs clés : chiffre d'affaires consolidé de la période, marge brute, nombre de ventes, alertes de rupture de stock actives, et performance comparative par boutique. Les données sont filtrables par période (7 jours, 30 jours, personnalisé) et par site. Le tableau de bord se rafraîchit automatiquement, avec un temps de réponse mesuré inférieur à 2 secondes (objectif O7).

### 3.7.2 Module Ventes

**Figure 22 : Capture — Module Ventes** *(à insérer)*

L'interface de caisse est conçue pour la rapidité de saisie (objectif O2 : < 30 secondes par vente). La recherche de produits est tolérante aux fautes de frappe et affiche les résultats en temps réel. Le tarif (simple ou technicien) est appliqué automatiquement selon le profil du client sélectionné. Un indicateur visuel signale l'état de la connexion réseau et le nombre de ventes en attente de synchronisation. En mode offline, l'interface reste pleinement fonctionnelle avec un badge "HORS-LIGNE" clairement visible.

### 3.7.3 Module Stocks et Transferts

**Figure 23 : Capture — Module Stocks / Transferts** *(à insérer)*

La vue stocks affiche les niveaux de stock par produit et par site, avec un code couleur : vert (stock normal), orange (proche du seuil minimum), rouge (rupture imminente ou atteinte). La création d'un transfert est accessible en un clic depuis cette vue, avec sélection du produit, de la quantité et du site destination. Le cycle de vie du transfert (BROUILLON → EN_TRANSIT → REÇU) est suivi en temps réel.

### 3.7.4 Module Analytique (aperçu)

**Figure 24 : Capture — Dashboard analytique IA** *(à insérer)*

Le module analytique est accessible uniquement à l'Administrateur. Il présente les différentes analyses sous forme d'onglets : Prévisions de demande (graphique temporel Prophet avec intervalles de confiance), Segmentation clients RFM (tableau avec indicateur de risque churn), Score de solvabilité (liste clients avec explication SHAP des facteurs), Anomalies détectées (liste avec raisons lisibles), Market Basket (règles d'association triées par lift), et Contexte BF (événements calendaires actifs, indicateurs de trésorerie).

**Figure 26 : Capture — Prévision de demande (graphique Prophet)** *(à insérer)*

Le graphique Prophet affiche l'historique de ventes d'un produit sur un site, la prévision à 30 jours avec intervalles de confiance, et une alerte de rupture si le stock prévisionnel devient négatif dans les 7 jours. L'indicateur `data_confidence` (HIGH / MEDIUM / LOW) informe l'administrateur sur la fiabilité de la prévision selon la taille de l'historique disponible.

---

## Conclusion du chapitre

Ce chapitre a présenté l'architecture technique de GesCom-BF et la réalisation concrète du système. L'architecture 3-tiers API-first, avec Flask pour le backend et React PWA pour le frontend, répond aux contraintes fonctionnelles et non fonctionnelles identifiées : performance (< 200 ms au p95), sécurité (JWT + RBAC + rate limiting + audit log), résilience hors-ligne (PWA + IndexedDB + Background Sync) et extensibilité SaaS. Les choix technologiques ont été justifiés par des critères objectifs liés au contexte du projet — notamment la compatibilité de Flask avec l'écosystème ML Python, et l'adaptation des mécanismes asynchrones aux contraintes de PythonAnywhere.

Le chapitre suivant, qui constitue la contribution originale principale de ce mémoire, présente en détail le module d'intelligence artificielle et d'analyse de données intégré à GesCom-BF.

---

*— Fin des Chapitres 2 et 3 —*
