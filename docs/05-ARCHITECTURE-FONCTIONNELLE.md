# 5. Architecture fonctionnelle

## 5.1 Organisation hiérarchique

```text
Entreprise (Tenant)
    |
    +-- Dépôt Central (unique)
            |
            +-- Boutique 1
            +-- Boutique 2
            +-- Boutique N
```

```mermaid
graph TD
    A[Entreprise / Tenant] --> B[Dépôt Central]
    B --> C[Boutique 1]
    B --> D[Boutique 2]
    B --> E[Boutique N]
    A --> F[Utilisateurs]
    F --> G[Administrateur]
    F --> H[Magasinier]
    F --> I[Vendeur]
    H -.opère sur.-> B
    I -.opère sur.-> C
    I -.opère sur.-> D
    G -.supervise.-> A
```

## 5.2 Cartographie des modules

```mermaid
graph LR
    subgraph Coeur Métier
        M1[1. Authentification]
        M2[2. Utilisateurs]
        M3[3. Produits]
        M4[4. Fournisseurs]
        M5[5. Dépôt]
        M6[6. Transferts]
        M7[7. Ventes]
        M8[8. Inventaires]
    end
    subgraph Pilotage
        M9[9. Rapports]
        M10[10. Analytics]
        M11[11. IA]
        M12[12. Audit]
    end
    M1 --> M2
    M4 --> M5
    M5 --> M6 --> M7
    M3 --> M7
    M7 --> M8
    M7 --> M9
    M7 --> M10 --> M11
    M1 --> M12
    M7 --> M12
    M6 --> M12
```

| # | Module | Description | Acteurs principaux |
|---|---|---|---|
| 1 | Authentification | Login, JWT, gestion de session, multi-tenant | Tous |
| 2 | Utilisateurs | Gestion des comptes, rôles, permissions (RBAC) | Administrateur |
| 3 | Produits | Catalogue, catégories, marques, tarifications | Administrateur, Magasinier |
| 4 | Fournisseurs | Référentiel fournisseurs, historique achats | Magasinier, Administrateur |
| 5 | Dépôt | Stock du dépôt central, réceptions | Magasinier |
| 6 | Transferts | Mouvements dépôt ↔ boutiques | Magasinier, Administrateur |
| 7 | Ventes | Saisie des ventes, remises, crédit, offline | Vendeur |
| 8 | Inventaires | Comptages physiques, ajustements de stock | Magasinier, Vendeur (boutique) |
| 9 | Rapports | Tableaux de bord, exports PDF | Administrateur |
| 10 | Analytics | ABC/XYZ, segmentation clients, KPIs | Administrateur |
| 11 | IA | Prévisions, scoring, détection d'anomalies | Système (automatisé) + Administrateur |
| 12 | Audit | Journalisation, traçabilité, sécurité | Système + Administrateur |

## 5.3 Cycle métier global

```mermaid
flowchart LR
    A[Fournisseur] -->|Livraison| B[Réception au Dépôt]
    B -->|Mise à jour stock dépôt| C[Stock Dépôt Central]
    C -->|Transfert| D[Stock Boutique]
    D -->|Vente| E[Vente Client]
    E -->|Décrémentation stock boutique| D
    E -->|Agrégation| F[Rapports & Analytics]
    F -->|Alimente| G[Module IA]
    G -->|Prévisions / Alertes| H[Décisions: réapprovisionnement, remise, crédit]
    H -->|Commande| A
    C -->|Inventaire| I[Ajustement Stock]
    D -->|Inventaire| I
```

## 5.4 Vue d'ensemble offline-first

```mermaid
flowchart TD
    subgraph Boutique (Client / PWA)
        UI[Interface Vente]
        IDB[(IndexedDB local)]
        SW[Service Worker]
    end
    subgraph Serveur
        API[API Flask]
        DB[(PostgreSQL)]
        Q[File de synchronisation]
    end
    UI -->|Vente saisie| IDB
    IDB -->|Connexion disponible| SW
    SW -->|POST /sync/sales| API
    API --> Q --> DB
    API -->|ACK / Conflits| SW
    SW -->|Mise à jour statut| IDB
    UI <-->|Lecture stock cache| IDB
```

## 5.5 Flux de données vers le module IA

```mermaid
flowchart LR
    A[(sales / sale_lines)] --> B[ETL Nettoyage & Agrégation]
    B --> C[(Feature Store)]
    C --> D1[Prophet - Prévision rupture]
    C --> D2[XGBoost - Affinage prévision]
    C --> D3[Random Forest - Scoring crédit]
    C --> D4[Isolation Forest - Anomalies]
    C --> D5[ABC/XYZ - Classification]
    D1 --> E[(predictions)]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E
    E --> F[Dashboard BI temps réel]
    E --> G[Alertes Celery -> Administrateur]
```

## 5.6 Synthèse des interactions inter-modules

| Module source | Module cible | Donnée échangée |
|---|---|---|
| Ventes | Stock (Boutique) | Décrémentation quantité |
| Transferts | Stock (Dépôt + Boutique) | Décrémentation source / incrémentation destination |
| Fournisseurs | Stock (Dépôt) | Incrémentation à réception |
| Inventaires | Stock | Ajustement (écart) |
| Ventes | Audit | Log de vente, remise |
| Authentification | Audit | Log de connexion |
| Ventes / Stock | Analytics & IA | Données d'entraînement et features |
| IA | Rapports / Dashboard | Prévisions, scores, anomalies, alertes |
