# 7. Diagrammes UML

## 7.1 Diagramme de classes

```mermaid
classDiagram
    class Company {
        +UUID id
        +String name
        +String schema_name
        +String subscription_plan
        +DateTime created_at
    }

    class Branch {
        +UUID id
        +UUID company_id
        +String name
        +String type
        +String address
    }

    class User {
        +UUID id
        +UUID company_id
        +UUID branch_id
        +String email
        +String password_hash
        +UUID role_id
        +Boolean is_active
        +DateTime last_login
    }

    class Role {
        +UUID id
        +String name
        +String description
    }

    class Permission {
        +UUID id
        +String code
        +String description
    }

    class Supplier {
        +UUID id
        +UUID company_id
        +String name
        +String phone
        +String address
    }

    class Customer {
        +UUID id
        +UUID company_id
        +String name
        +String phone
        +String type_client
        +Numeric solde_du
        +Numeric credit_score
    }

    class Category {
        +UUID id
        +String name
    }

    class Brand {
        +UUID id
        +String name
    }

    class Product {
        +UUID id
        +UUID company_id
        +String name
        +String name_moore
        +String reference
        +UUID category_id
        +UUID brand_id
        +Numeric purchase_price
        +Numeric retail_price
        +Numeric technician_price
        +Boolean is_active
    }

    class Stock {
        +UUID id
        +UUID product_id
        +UUID branch_id
        +Integer quantity
        +Integer min_stock
        +DateTime updated_at
    }

    class StockMovement {
        +UUID id
        +UUID product_id
        +UUID branch_id
        +String type
        +Integer quantity
        +UUID reference_id
        +DateTime created_at
    }

    class Transfer {
        +UUID id
        +UUID company_id
        +UUID source_branch_id
        +UUID dest_branch_id
        +String status
        +UUID created_by
        +DateTime created_at
        +DateTime received_at
    }

    class TransferLine {
        +UUID id
        +UUID transfer_id
        +UUID product_id
        +Integer quantity
    }

    class Sale {
        +UUID id
        +UUID company_id
        +UUID branch_id
        +UUID seller_id
        +UUID customer_id
        +String status
        +String channel
        +UUID offline_uuid
        +Numeric total_amount
        +DateTime created_at
    }

    class SaleLine {
        +UUID id
        +UUID sale_id
        +UUID product_id
        +Integer quantity
        +Numeric unit_price
        +String price_type
    }

    class Discount {
        +UUID id
        +UUID sale_id
        +Numeric rate
        +UUID approved_by_user_id
        +String approval_note
    }

    class Inventory {
        +UUID id
        +UUID branch_id
        +String status
        +UUID created_by
        +DateTime created_at
        +DateTime validated_at
    }

    class InventoryLine {
        +UUID id
        +UUID inventory_id
        +UUID product_id
        +Integer theoretical_qty
        +Integer counted_qty
        +String justification
    }

    class AuditLog {
        +UUID id
        +UUID company_id
        +UUID user_id
        +String event_type
        +String entity
        +UUID entity_id
        +JSON before
        +JSON after
        +DateTime created_at
    }

    class Prediction {
        +UUID id
        +UUID company_id
        +UUID product_id
        +UUID branch_id
        +String model_type
        +String model_version
        +JSON payload
        +DateTime created_at
    }

    Company "1" --> "1" Branch : dépôt central
    Company "1" --> "0..*" Branch : boutiques
    Company "1" --> "0..*" User
    Company "1" --> "0..*" Product
    Company "1" --> "0..*" Supplier
    Company "1" --> "0..*" Customer
    User "1" --> "1" Role
    Role "1" --> "0..*" Permission
    User "0..1" --> "0..1" Branch : rattachement
    Product "1" --> "1" Category
    Product "1" --> "1" Brand
    Product "1" --> "0..*" Stock
    Branch "1" --> "0..*" Stock
    Stock "1" --> "0..*" StockMovement
    Transfer "1" --> "1..*" TransferLine
    TransferLine "1" --> "1" Product
    Transfer "1" --> "1" Branch : source
    Transfer "1" --> "1" Branch : destination
    Sale "1" --> "1..*" SaleLine
    SaleLine "1" --> "1" Product
    Sale "0..1" --> "0..1" Discount
    Sale "1" --> "1" Branch
    Sale "1" --> "1" User : vendeur
    Sale "0..1" --> "1" Customer
    Inventory "1" --> "1..*" InventoryLine
    InventoryLine "1" --> "1" Product
    Inventory "1" --> "1" Branch
    Company "1" --> "0..*" AuditLog
    Company "1" --> "0..*" Prediction
    Prediction "0..1" --> "1" Product
    Prediction "0..1" --> "1" Branch
```

## 7.2 Diagramme de séquence — Flux 1 : Authentification (UC-01)

```mermaid
sequenceDiagram
    actor U as Utilisateur
    participant FE as Frontend React
    participant API as API Flask (/auth/login)
    participant DB as PostgreSQL
    participant AUD as Audit Service

    U->>FE: Saisie email + mot de passe
    FE->>API: POST /api/v1/auth/login {email, password}
    API->>DB: SELECT user WHERE email AND company schema
    DB-->>API: Utilisateur + hash mot de passe
    alt identifiants valides et compte actif
        API->>API: Vérification bcrypt + génération JWT (access 15min, refresh 7j)
        API->>AUD: log(LOGIN_SUCCESS, user_id)
        API-->>FE: 200 {access_token, refresh_token, user, role, permissions}
        FE->>FE: Stockage access_token (mémoire) + refresh_token (cookie httpOnly)
        FE-->>U: Redirection vers Dashboard
    else identifiants invalides
        API->>AUD: log(LOGIN_FAILED, email)
        API-->>FE: 401 {error: "INVALID_CREDENTIALS"}
        FE-->>U: Message d'erreur
    else compte désactivé
        API-->>FE: 403 {error: "ACCOUNT_DISABLED"}
        FE-->>U: Message d'erreur
    end
```

## 7.3 Diagramme de séquence — Flux 2 : Enregistrement d'une vente avec remise (UC-11 + UC-12)

```mermaid
sequenceDiagram
    actor V as Vendeur
    participant FE as Frontend React (PWA)
    participant IDB as IndexedDB (local)
    participant API as API Flask (/sales)
    participant DB as PostgreSQL
    participant AUD as Audit Service

    V->>FE: Recherche produit + ajout lignes
    V->>FE: Sélection remise 10% + administrateur approbateur
    FE->>FE: Vérifie connectivité réseau

    alt En ligne
        FE->>API: POST /api/v1/sales {lines[], discount, customer_id?}
        API->>DB: Vérifie stock disponible (branch)
        alt stock suffisant
            API->>DB: INSERT sale, sale_lines, discount
            API->>DB: UPDATE stock (décrément) + INSERT stock_movement
            API->>AUD: log(SALE_CREATED), log(DISCOUNT_APPLIED, approved_by)
            API-->>FE: 201 {sale_id, total, status: VALIDEE}
            FE-->>V: Reçu généré (PDF)
        else stock insuffisant
            API-->>FE: 409 {error: "INSUFFICIENT_STOCK"}
            FE-->>V: Message d'erreur
        end
    else Hors-ligne
        FE->>IDB: INSERT sale (offline_uuid, status=EN_ATTENTE_SYNC)
        FE-->>V: Vente enregistrée localement (reçu provisoire)
        Note over FE,IDB: Synchronisation différée — cf. Flux 3
    end
```

## 7.4 Diagramme de séquence — Flux 3 : Synchronisation des ventes hors-ligne (UC-14)

```mermaid
sequenceDiagram
    participant SW as Service Worker
    participant IDB as IndexedDB (local)
    participant API as API Flask (/sync/sales)
    participant DB as PostgreSQL
    participant AUD as Audit Service

    Note over SW: Détection retour de connexion
    SW->>IDB: Récupère ventes (status=EN_ATTENTE_SYNC)
    SW->>API: POST /api/v1/sync/sales {ventes[]: {offline_uuid, lines, client_timestamp,...}}
    loop pour chaque vente
        API->>DB: Vérifie idempotence (offline_uuid déjà traité ?)
        alt déjà traité
            API-->>SW: status=DEJA_SYNCHRONISE
        else nouveau
            API->>DB: Vérifie stock courant au site
            alt stock suffisant
                API->>DB: INSERT sale (status=VALIDEE), update stock
                API->>AUD: log(SALE_SYNCED)
                API-->>SW: status=VALIDEE
            else stock insuffisant
                API->>DB: INSERT sale (status=EN_CONFLIT)
                API->>AUD: log(SALE_CONFLICT)
                API-->>SW: status=EN_CONFLIT
            end
        end
    end
    SW->>IDB: Met à jour statuts locaux, vide la file synchronisée
    Note over API: Notification Administrateur si EN_CONFLIT
```

## 7.5 Diagramme d'activité — Cycle de vente complet

```mermaid
flowchart TD
    Start([Début]) --> A[Vendeur recherche un produit]
    A --> B{Produit trouvé ?}
    B -- Non --> A
    B -- Oui --> C[Ajout de la ligne quantité/prix]
    C --> D{Autre produit ?}
    D -- Oui --> A
    D -- Non --> E{Remise demandée ?}
    E -- Oui --> F[Sélection taux 5/10/15/20%]
    F --> G[Sélection administrateur approbateur]
    G --> H
    E -- Non --> H{Connexion réseau disponible ?}
    H -- Oui --> I[Vérification stock disponible]
    I --> J{Stock suffisant ?}
    J -- Non --> K[Erreur : stock insuffisant]
    K --> End1([Fin - Vente annulée])
    J -- Oui --> L[Calcul du total - RG-25]
    L --> M[Enregistrement vente VALIDEE]
    M --> N[Décrémentation stock + mouvement]
    N --> O[Journalisation audit]
    O --> P[Génération reçu]
    P --> End2([Fin - Vente réussie])

    H -- Non --> Q[Enregistrement local IndexedDB - EN_ATTENTE_SYNC]
    Q --> R[Reçu provisoire affiché]
    R --> S{Connexion rétablie ?}
    S -- Non --> S
    S -- Oui --> T[Synchronisation via Service Worker]
    T --> U{Stock suffisant côté serveur ?}
    U -- Oui --> M
    U -- Non --> V[Statut EN_CONFLIT - revue admin]
    V --> End3([Fin - Vente synchronisée avec conflit])
```

## 7.6 Diagramme d'état — Cycle de vie d'un Transfert

```mermaid
stateDiagram-v2
    [*] --> BROUILLON : Création
    BROUILLON --> EN_TRANSIT : Validation (décrément stock source)
    BROUILLON --> ANNULE : Annulation
    EN_TRANSIT --> RECU : Confirmation réception (incrément stock destination)
    EN_TRANSIT --> ANNULE : Annulation exceptionnelle (réintégration stock source)
    RECU --> [*]
    ANNULE --> [*]
```

## 7.7 Diagramme d'état — Cycle de vie d'une Vente

```mermaid
stateDiagram-v2
    [*] --> EN_ATTENTE_SYNC : Saisie hors-ligne
    [*] --> VALIDEE : Saisie en ligne (stock OK)
    EN_ATTENTE_SYNC --> VALIDEE : Sync OK (stock OK)
    EN_ATTENTE_SYNC --> EN_CONFLIT : Sync (stock insuffisant)
    EN_CONFLIT --> VALIDEE : Résolution par administrateur
    EN_CONFLIT --> ANNULEE : Rejet par administrateur
    VALIDEE --> AVOIR_EMIS : Correction (avoir)
    VALIDEE --> [*]
    ANNULEE --> [*]
    AVOIR_EMIS --> [*]
```

## 7.8 Diagramme de composants — Vue d'ensemble système

```mermaid
flowchart TB
    subgraph Client
        PWA[React PWA + Service Worker]
    end
    subgraph Edge
        NGINX[Nginx Reverse Proxy / TLS]
    end
    subgraph Backend
        API[Flask API - Gunicorn]
        WORKER[Celery Workers]
        SCHED[Celery Beat - tâches planifiées]
    end
    subgraph Data
        PG[(PostgreSQL multi-schéma)]
        REDIS[(Redis - cache, queue, pub/sub)]
    end
    subgraph IA
        ML[Modèles Prophet / XGBoost / sklearn]
        MLFLOW[(MLflow - registry & lineage)]
    end

    PWA <--> NGINX
    NGINX <--> API
    API <--> PG
    API <--> REDIS
    API --> WORKER
    SCHED --> WORKER
    WORKER <--> PG
    WORKER <--> REDIS
    WORKER <--> ML
    ML <--> MLFLOW
    API -.WebSocket alertes.-> PWA
```
