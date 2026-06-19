# Données de démonstration GesCom-BF

Ce dossier contient les jeux de données de test pour alimenter le système
GesCom-BF et tester l'ensemble de ses fonctionnalités (POS, stock,
transferts, réceptions, crédit, inventaires, dashboards, modèles ML).

## 1. Générer les données dans la base (recommandé)

Ordre d'exécution, sur une base fraîchement créée :

```bash
flask seed                  # rôles, sites, catalogue de base, utilisateurs
flask seed-demo --months 6  # catalogue étendu, clients, fournisseurs,
                             # historique de ventes/stock/crédit + anomalies
flask etl-daily --days 180  # alimente le feature store (dashboards/ML)
flask ml-train-all --months 6  # entraîne les modèles ML (RF-25 à RF-28)
```

`flask seed-demo` n'est pas idempotent : ne l'exécuter qu'une seule fois sur
une base propre.

## 2. Fichiers de référence (CSV / Excel)

- **GesCom-BF_donnees_demo.xlsx** — classeur multi-feuilles :
  - *Catalogue* : 16 produits (7 de base + 9 ajoutés) avec prix d'achat,
    prix client simple/technicien, seuils d'alerte.
  - *Stock initial* : quantités de départ par site (DEPOT, OUA-TAN, OUA-GOU).
  - *Clients* : 18 clients (10 particuliers SIMPLE, 6 professionnels
    TECHNICIEN + 2 clients de base).
  - *Fournisseurs* : 4 fournisseurs avec leurs produits associés.
  - *Utilisateurs demo* : comptes de test (email / mot de passe / rôle / site).
  - *Stock après 6 mois*, *Ventes (échantillon)*, *Mvts stock (échantillon)*,
    *Échéances crédit* : extraits d'une exécution de référence de
    `flask seed-demo --months 6` (1611 ventes, 3178 mouvements de stock,
    101 échéances de crédit) — utiles pour visualiser le format attendu
    sans relancer la génération.

- **catalogue.csv**, **clients.csv**, **fournisseurs.csv** : exports CSV des
  données maîtres ci-dessus, réutilisables indépendamment (import dans un
  autre outil, vérification manuelle, etc.).

## 3. Comptes de test

| Email | Mot de passe | Rôle | Site |
|---|---|---|---|
| admin@gescom-bf.bf | défini via `SEED_ADMIN_PASSWORD` (def. `Admin#2026`) | ADMIN | Tous |
| magasinier@gescom-bf.bf | Magasinier#2026 | MAGASINIER | Dépôt central |
| vendeur@gescom-bf.bf | Vendeur#2026 | VENDEUR | Boutique Tanghin |
| vendeur2@gescom-bf.bf | Vendeur2#2026 | VENDEUR | Boutique Gounghin |

## 4. Couverture fonctionnelle des données générées

- **Ventes/POS** : 1611 ventes sur 6 mois, statuts VALIDEE/ANNULEE/
  AVOIR_EMIS/EN_ATTENTE_APPROBATION, canaux ONLINE/OFFLINE, paiements
  CASH/CREDIT, remises 0/5/10/15/20% (avec approbation ≥10%).
- **Stock & inventaire** : réceptions fournisseurs, transferts dépôt→boutique,
  8 inventaires physiques avec écarts (justifiés si ≥5%, RG-33).
- **Crédit & recouvrement** : 101 échéances CustomerPayment
  (PENDING/PAID/LATE/CANCELLED).
- **Anomalies volontaires** : 18 ventes anormales injectées sur 60 jours
  (quantités extrêmes, horaires inhabituels, st