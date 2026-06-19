# 4. Règles de gestion (Business Rules)

Les règles de gestion (RG) sont la traduction opérationnelle des exigences fonctionnelles. Elles sont implémentées au niveau **applicatif (Flask)** et, lorsque possible, renforcées au niveau **base de données** (cf. `16-CONTRAINTES-SQL.md`).

## 4.1 Organisation & Structure

- **RG-01** : Une entreprise (tenant) possède **un seul dépôt central** et **0 à N boutiques**.
- **RG-02** : Une boutique appartient à une seule entreprise.
- **RG-03** : Un utilisateur appartient à une seule entreprise et possède un rôle unique parmi {Administrateur, Magasinier, Vendeur}.
- **RG-04** : Un Vendeur est rattaché à une boutique précise ; il ne peut consulter/modifier que le stock et les ventes de sa boutique.
- **RG-05** : Un Magasinier opère uniquement sur le dépôt central et les transferts sortants.
- **RG-06** : Un Administrateur a une vue consolidée sur l'ensemble des boutiques et du dépôt de son entreprise.

## 4.2 Produits & Tarification

- **RG-07** : La référence produit est **unique** au sein d'une entreprise.
- **RG-08** : `prix_achat > 0`.
- **RG-09** : `prix_vente_client_simple >= prix_achat`.
- **RG-10** : `prix_vente_technicien <= prix_vente_client_simple` (le tarif technicien est un tarif préférentiel).
- **RG-11** : Un produit ne peut être supprimé s'il existe des mouvements de stock ou des lignes de vente associées (suppression logique uniquement — `is_active = false`).
- **RG-12** : Le `seuil_min_stock` est défini par produit **et par site** (dépôt ou boutique) — un même produit peut avoir des seuils différents selon le point de vente.

## 4.3 Stock & Transferts

- **RG-13** : Le stock est toujours rattaché à un site (dépôt central **ou** une boutique) — pas de stock "global".
- **RG-14** : Toute entrée de marchandise (réception fournisseur) augmente le stock du **dépôt central uniquement**.
- **RG-15** : Un transfert ne peut être créé que depuis le dépôt central vers une boutique, **ou** entre deux boutiques de la même entreprise (avec validation de l'administrateur).
- **RG-16** : Un transfert suit le cycle : `BROUILLON → EN_TRANSIT → RECU` (ou `ANNULE`).
- **RG-17** : Le stock source est décrémenté au passage en `EN_TRANSIT` ; le stock destination est incrémenté uniquement au passage en `RECU` (réception confirmée par le destinataire).
- **RG-18** : Un transfert ne peut être créé si la quantité demandée dépasse le stock disponible du site source (`quantite_disponible - quantite_reservee >= quantite_transfert`).
- **RG-19** : Toute variation de stock génère un enregistrement dans `stock_movements` avec la nature du mouvement (réception, vente, transfert sortant, transfert entrant, ajustement inventaire).

## 4.4 Ventes & Remises

- **RG-20** : Une vente est rattachée à une boutique et à un vendeur (utilisateur).
- **RG-21** : Le tarif appliqué par défaut est le **tarif client simple**, sauf si le client est identifié comme **technicien** (champ `type_client`).
- **RG-22** : Les remises possibles sont limitées à l'ensemble **{0 %, 5 %, 10 %, 15 %, 20 %}** — toute autre valeur est rejetée par l'API (validation stricte).
- **RG-23** : Toute remise > 0 % doit obligatoirement référencer l'**administrateur ayant donné son accord** (`approved_by_user_id`), conformément à la pratique de l'accord verbal. Ce champ alimente le module d'audit et le détecteur d'anomalies (remises "auto-approuvées" par un vendeur = anomalie).
- **RG-24** : Une vente ne peut être validée si la quantité vendue dépasse le stock disponible de la boutique pour le produit concerné — **sauf** si la vente a été créée en mode hors-ligne (cf. RG-29).
- **RG-25** : Le total d'une vente = somme des `(quantite × prix_unitaire_applique × (1 - remise))` de chaque ligne.
- **RG-26** : Une vente à crédit (RF-18) nécessite un `customer_id` renseigné (le crédit anonyme est interdit) ; le solde du client est mis à jour (`solde_du += montant_credit`).
- **RG-27** : Une vente, une fois validée (`statut = VALIDEE`), est **immuable** — toute correction se fait par un avoir (vente négative liée), jamais par modification directe (exigence d'audit).

## 4.5 Mode hors-ligne (cf. `26-GESTION-OFFLINE-PWA.md`)

- **RG-28** : Toute vente créée hors-ligne reçoit un identifiant local (UUID généré côté client) et un horodatage client.
- **RG-29** : À la synchronisation, si le stock théorique au moment de la vente offline est insuffisant (vente concurrente entre-temps), la vente est acceptée mais **marquée `EN_CONFLIT`** pour revue par l'administrateur — elle n'est jamais rejetée silencieusement.
- **RG-30** : La résolution de conflit privilégie l'**ordre chronologique de saisie côté client** (timestamp local), avec alerte si le stock devient négatif.

## 4.6 Inventaires

- **RG-31** : Un inventaire est rattaché à un site unique (dépôt ou boutique) et a un statut `EN_COURS` ou `VALIDE`.
- **RG-32** : Tant qu'un inventaire est `EN_COURS` sur un site, les ventes/transferts restent autorisés mais génèrent une alerte de "stock en cours de comptage".
- **RG-33** : À la validation, l'écart (`quantite_comptee - quantite_theorique`) génère un mouvement de type `AJUSTEMENT_INVENTAIRE` dans `stock_movements`, avec justification obligatoire si `|écart| > 5 %` du stock théorique.

## 4.7 Audit & Sécurité

- **RG-34** : Tout événement listé (RF-30) est journalisé avec : horodatage UTC, `user_id`, `tenant_id`, type d'événement, entité concernée, valeurs avant/après (le cas échéant).
- **RG-35** : Les journaux d'audit sont **immuables** (pas d'UPDATE ni DELETE applicatif) et conservés **1 an minimum**.
- **RG-36** : Un token JWT expiré renvoie systématiquement `401 Unauthorized` avec un code d'erreur `TOKEN_EXPIRED` permettant au frontend de déclencher le refresh automatique.

## 4.8 Module IA (cf. `20-MACHINE-LEARNING.md`)

- **RG-37** : Une prévision de rupture de stock est calculée **par couple (produit, site)** et republiée quotidiennement (tâche planifiée Celery).
- **RG-38** : Une alerte de rupture est déclenchée si `stock_disponible < seuil_min_stock` **OU** si la prévision Prophet indique un stock prévisionnel négatif dans les 7 jours.
- **RG-39** : Le scoring de solvabilité est recalculé à chaque nouvelle transaction de vente à crédit du client concerné.
- **RG-40** : Toute prédiction stockée référence la **version du modèle** utilisé (`model_version`) pour garantir la traçabilité (data lineage, cf. `21-PIPELINE-ETL.md`).

## 4.9 Multi-tenant (cf. `27-MODELE-SAAS-MULTITENANT.md`)

- **RG-41** : Toute requête API est exécutée dans le contexte d'un `tenant_id` extrait du JWT — aucune donnée d'un tenant ne peut être visible par un autre.
- **RG-42** : La suppression d'un tenant (résiliation) entraîne l'archivage de son schéma PostgreSQL pendant la durée légale de rétention avant suppression définitive.

## 4.10 Tableau récapitulatif des invariants critiques

| Invariant | Vérification |
|---|---|
| `stock_disponible >= 0` (sauf vente offline en conflit) | Contrainte applicative + flag `EN_CONFLIT` |
| `remise IN (0, 5, 10, 15, 20)` | Contrainte CHECK + validation Marshmallow |
| `prix_vente_technicien <= prix_vente_client_simple <= ... ` selon RG-09/RG-10 | Contrainte CHECK |
| Vente validée immuable | Pas d'endpoint PUT/PATCH sur vente validée |
| 1 dép�