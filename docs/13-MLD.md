# 13. Modèle Logique de Données (MLD)

## 13.1 Conventions

- Clé primaire en **gras**.
- Clé étrangère préfixée par `#`.
- Type Merise simplifié ; les types SQL précis sont définis dans `14-MPD.md` et `15-DICTIONNAIRE-DES-DONNEES.md`.
- Toutes les tables métier incluent implicitement `#id_entreprise` pour le filtrage multi-tenant — **sauf** que dans l'implémentation *schema-per-tenant* (cf. `27-MODELE-SAAS-MULTITENANT.md`), ce champ est **omis au niveau physique** (l'isolation se fait par schéma). Il est néanmoins représenté ici pour la lisibilité conceptuelle/logique.

## 13.2 Schéma relationnel (notation Merise)

```text
COMPANIES ( id_entreprise, nom, schema_name, plan_abonnement, date_creation )

BRANCHES ( id_site, #id_entreprise, nom, type_site, adresse )

ROLES ( id_role, nom_role, description )

PERMISSIONS ( id_permission, code_permission, description )

ROLE_PERMISSIONS ( #id_role, #id_permission )

USERS ( id_utilisateur, #id_entreprise, #id_role, #id_site, email, mot_de_passe_hash,
        nom_complet, est_actif, derniere_connexion, date_creation )

CATEGORIES ( id_categorie, #id_entreprise, nom_categorie )

BRANDS ( id_marque, #id_entreprise, nom_marque )

PRODUCTS ( id_produit, #id_entreprise, #id_categorie, #id_marque, nom, nom_moore,
           reference, prix_achat, prix_client_simple, prix_technicien,
           est_actif, date_creation )

STOCK ( id_stock, #id_produit, #id_site, quantite, seuil_min, date_maj )

STOCK_MOVEMENTS ( id_mouvement, #id_stock, type_mouvement, quantite, #id_reference,
                  date_mouvement )

SUPPLIERS ( id_fournisseur, #id_entreprise, nom, telephone, adresse )

SUPPLIER_RECEPTIONS ( id_reception, #id_fournisseur, #id_site, reference_bon,
                       #id_utilisateur, date_reception )

SUPPLIER_RECEPTION_LINES ( id_ligne_reception, #id_reception, #id_produit,
                            quantite_recue, prix_achat_unitaire )

CUSTOMERS ( id_client, #id_entreprise, nom, telephone, type_client, solde_du,
            score_credit, date_maj_score )

TRANSFERS ( id_transfert, #id_entreprise, #id_site_source, #id_site_destination,
            statut, #id_utilisateur_createur, date_creation, date_reception )

TRANSFER_LINES ( id_ligne_transfert, #id_transfert, #id_produit, quantite )

SALES ( id_vente, #id_entreprise, #id_site, #id_vendeur, #id_client, statut,
        canal, uuid_offline, montant_total, date_vente )

SALE_LINES ( id_ligne_vente, #id_vente, #id_produit, quantite, prix_unitaire_applique,
             type_prix )

DISCOUNTS ( id_remise, #id_vente, taux, #id_utilisateur_approbateur, note_approbation )

INVENTORIES ( id_inventaire, #id_entreprise, #id_site, statut,
               #id_utilisateur_createur, date_creation, date_validation )

INVENTORY_LINES ( id_ligne_inventaire, #id_inventaire, #id_produit,
                   quantite_theorique, quantite_comptee, justification )

AUDIT_LOGS ( id_log, #id_entreprise, #id_utilisateur, type_evenement, entite,
             #id_entite, donnees_avant, donnees_apres, date_evenement )

ML_MODELS ( id_modele, type_modele, version, date_entrainement, metriques,
            chemin_artefact )

PREDICTIONS ( id_prediction, #id_entreprise, #id_modele, #id_produit, #id_site,
               type_prediction, contenu, date_generation )
```

## 13.3 Résolution des associations N:N et porteuses (Merise → MLD)

| Association MCD | Entité de jonction MLD | Clé primaire | Clés étrangères |
|---|---|---|---|
| CONTIENT (Vente-Produit) | `SALE_LINES` | `id_ligne_vente` | `#id_vente`, `#id_produit` |
| CONTIENT (Transfert-Produit) | `TRANSFER_LINES` | `id_ligne_transfert` | `#id_transfert`, `#id_produit` |
| COMPTE (Inventaire-Produit) | `INVENTORY_LINES` | `id_ligne_inventaire` | `#id_inventaire`, `#id_produit` |
| CONCERNE (Réception-Produit) | `SUPPLIER_RECEPTION_LINES` | `id_ligne_reception` | `#id_reception`, `#id_produit` |
| ACCORDE (Rôle-Permission) | `ROLE_PERMISSIONS` | `(#id_role, #id_permission)` | `#id_role`, `#id_permission` |

## 13.4 Cardinalités résolues — récapitulatif des relations 1:N

| Table parente | Table enfant | Clé étrangère | Règle de suppression |
|---|---|---|---|
| COMPANIES | BRANCHES, USERS, PRODUCTS, SUPPLIERS, CUSTOMERS, ... | `id_entreprise` | RESTRICT (schema-per-tenant : N/A) |
| BRANCHES | USERS, STOCK, SALES, TRANSFERS (source/dest), INVENTORIES | `id_site` | RESTRICT |
| ROLES | USERS | `id_role` | RESTRICT |
| CATEGORIES | PRODUCTS | `id_categorie` | RESTRICT |
| BRANDS | PRODUCTS | `id_marque` | RESTRICT |
| PRODUCTS | STOCK, SALE_LINES, TRANSFER_LINES, INVENTORY_LINES, SUPPLIER_RECEPTION_LINES, PREDICTIONS | `id_produit` | RESTRICT (soft-delete `est_actif`) |
| STOCK | STOCK_MOVEMENTS | `id_stock` | CASCADE |
| SALES | SALE_LINES, DISCOUNTS | `id_vente` | CASCADE (mais vente immuable — RG-27) |
| TRANSFERS | TRANSFER_LINES | `id_transfert` | CASCADE |
| INVENTORIES | INVENTORY_LINES | `id_inventaire` | CASCADE |
| SUPPLIER_RECEPTIONS | SUPPLIER_RECEPTION_LINES | `id_reception` | CASCADE |
| USERS | SALES, AUDIT_LOGS, DISCOUNTS (approbateur), TRANSFERS (créateur) | `id_utilisateur` | RESTRICT |
| ML_MODELS | PREDICTIONS | `id_modele` | RESTRICT |

## 13.5 Vérification de normalisation (3FN)

| Forme normale | Vérification |
|---|---|
| **1FN** | Toutes les tables ont des attributs atomiques (pas de listes : ex. les lignes de vente sont dans une table séparée `SALE_LINES`, pas une colonne JSON répétée) |
| **2FN** | Aucune dépendance partielle : chaque attribut non-clé dépend de la totalité de la clé primaire (les clés sont toutes simples, sauf `ROLE_PERMISSIONS` qui est une clé composite sans attribut non-clé) |
| **3FN** | Aucune dépendance transitive : ex. `prix_unitaire_applique` est stocké dans `SALE_LINES` (et non recalculé depuis `PRODUCTS`) **intentionnellement** — il s'agit d'une **dénormalisation contrôlée** pour garantir l'immuabilité historique des ventes (RG-27), documentée comme exception justifiée |

> **Exception documentée** : `SALE_LINES.prix_unitaire_applique` et `STOCK.quantite` (donnée dérivée des `STOCK_MOVEMENTS`) sont des dénormalisations volontaires pour la performance (RNF-01) et la traçabilité historique. La cohérence est garantie par triggers (cf. `16-CONTRAINTES-SQL.md`).
