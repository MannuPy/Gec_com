# Guide de tests manuels — GesCom-BF
## Validation complète avant soutenance

> **Date de rédaction :** 1er juillet 2026  
> **URL de production :** https://mannudev.pythonanywhere.com  
> **Objectif :** Vérifier que toutes les fonctionnalités sont opérationnelles avant la présentation au jury.

---

## Avant de commencer — étapes obligatoires

### ⚙️ Checklist pré-test PythonAnywhere

Avant tout test, vérifier ces points dans le tableau de bord PythonAnywhere :

1. **Migrations à jour** — Ouvrir un Bash console et exécuter :
   ```bash
   cd ~/gescom-bf/backend
   source ~/.virtualenvs/gescom-bf/bin/activate
   flask db upgrade
   ```
   Résultat attendu : `Running upgrade ... -> g7h8i9j0k1l2` (ou "already up to date").

2. **Vider le cache navigateur** — `Ctrl+Shift+Del` → vider "cache" et "service workers" → recharger.

3. **Recharger l'app web** — PythonAnywhere → onglet Web → bouton **Reload**.

4. **Tester `/health`** :
   - Ouvrir : https://mannudev.pythonanywhere.com/health
   - Attendu : `{"status":"ok","db":"ok","ml_models_actifs":N,...}`

---

## Comptes de test

| Rôle | Email | Mot de passe | Accès |
|---|---|---|---|
| Administrateur | `admin@gescom-bf.bf` | `Admin#2026` | Tout |
| Magasinier | `magasinier@gescom-bf.bf` | `Magasinier#2026` | Dépôt, transferts, inventaire |
| Vendeuse | `vendeur@gescom-bf.bf` | `Vendeur#2026` | Boutique Tanghin uniquement |

> **Note :** Si `must_change_password=true`, changer le mot de passe via le formulaire `/changer-mot-de-passe` avant de pouvoir accéder à l'application.

---

## Module 1 — Authentification & Sécurité

### TC-AUTH-01 : Connexion valide (Admin)
- Aller sur `/login`
- Saisir `admin@gescom-bf.bf` / `Admin#2026`
- **Attendu :** Redirection vers le tableau de bord (`/`)
- **Indicateur :** Badge "En ligne" vert en haut à droite

### TC-AUTH-02 : Mot de passe incorrect
- Aller sur `/login`
- Saisir `admin@gescom-bf.bf` / `mauvais`
- **Attendu :** Message d'erreur "Identifiants invalides", pas de redirection

### TC-AUTH-03 : Rate limiting brute-force
- Tenter 11 connexions échouées rapides en moins d'une minute
- **Attendu :** 12e tentative → erreur 429 "Trop de tentatives"

### TC-AUTH-04 : Changement de mot de passe obligatoire (RF-05)
- Créer un nouvel utilisateur (Admin → Utilisateurs → Créer)
- Se connecter avec ce compte
- **Attendu :** Redirection automatique vers `/changer-mot-de-passe`
- Tenter d'accéder à `/produits` avant de changer le mot de passe
- **Attendu :** 403 `PASSWORD_CHANGE_REQUIRED` (redirigé vers changement MDP)

### TC-AUTH-05 : Déconnexion
- Se connecter → cliquer sur "Déconnexion"
- **Attendu :** Redirection vers `/login`
- Tenter d'utiliser le back-button du navigateur
- **Attendu :** Redirigé vers `/login` (session effacée)

### TC-AUTH-06 : RBAC — Vendeur ne peut pas accéder aux produits (écriture)
- Se connecter en tant que Vendeuse
- Tenter de créer un produit via l'interface
- **Attendu :** Bouton "Nouveau produit" absent ou erreur 403

### TC-AUTH-07 : RBAC — Vendeur ne voit que sa boutique
- Se connecter en tant que Vendeuse (Boutique Tanghin)
- Aller sur Stock
- **Attendu :** Seul le stock de Boutique Tanghin est visible

---

## Module 2 — Tableau de bord

### TC-DASH-01 : Chargement du tableau de bord (Admin)
- Se connecter en Admin → aller sur `/`
- **Attendu :** KPIs visibles (CA, marges, top produits)
- Aucune erreur rouge dans la console

### TC-DASH-02 : Tableau de bord Vendeur
- Se connecter en Vendeuse → aller sur `/mon-tableau-de-bord`
- **Attendu :** Indicateurs propres à la boutique Tanghin

### TC-DASH-03 : Actualisation des données
- Depuis le tableau de bord Admin
- **Attendu :** Données visibles (pas de spinner infini)
- Si SSE désactivé (PythonAnywhere) : le badge "polling" doit s'afficher et les données se rafraîchissent toutes les 30s

---

## Module 3 — Produits & Catalogue

### TC-PROD-01 : Lister les produits
- Admin → Produits
- **Attendu :** Liste paginée des produits, pas d'erreur

### TC-PROD-02 : Créer un produit
- Admin → Produits → Nouveau produit
- Remplir : Nom = "Vis 6mm Test", Réf = "VIS6MM-TEST", Prix achat = 100, Prix vente = 150, Prix technicien = 130
- **Attendu :** Produit créé, apparaît dans la liste

### TC-PROD-03 : Règle prix technicien ≤ prix simple (RG-10)
- Tenter de créer un produit avec Prix technicien = 200 > Prix vente = 150
- **Attendu :** Erreur de validation, produit non créé

### TC-PROD-04 : Recherche phonétique
- Chercher "boullon" (au lieu de "boulon")
- **Attendu :** Les produits "boulon" apparaissent dans les résultats

### TC-PROD-05 : Désactiver un produit avec stock existant (RG-11)
- Sélectionner un produit ayant du stock
- Tenter de supprimer
- **Attendu :** Désactivation logique uniquement (`is_active=false`), pas de suppression

---

## Module 4 — Fournisseurs & Approvisionnement

### TC-FOUR-01 : Lister les fournisseurs
- Admin → Fournisseurs
- **Attendu :** Page chargée, liste visible sans erreur

> **Note :** Si vous voyez "Failed to fetch dynamically imported module" sur cette page, vider le cache et les Service Workers du navigateur, puis recharger.

### TC-FOUR-02 : Créer un fournisseur
- Fournisseurs → Nouveau fournisseur
- Remplir : Nom = "Test SARL", Téléphone = "+22670000000"
- **Attendu :** Fournisseur créé

### TC-FOUR-03 : Réception de marchandises (RF-11)
- Admin → Fournisseurs → Réceptions → Nouvelle réception
- Sélectionner un fournisseur, ajouter un produit (qté = 50, prix unitaire = 100)
- **Attendu :** Réception créée, stock du dépôt central augmenté de 50

### TC-FOUR-04 : Stock mis à jour après réception
- Après TC-FOUR-03, aller sur Stock → Dépôt Central
- **Attendu :** Stock du produit réceptionné = quantité précédente + 50

---

## Module 5 — Stock & Transferts

### TC-STK-01 : Consulter le stock par site
- Stock → sélectionner "Dépôt Central"
- **Attendu :** Liste des produits avec quantités

### TC-STK-02 : Alerte stock bas
- Modifier le seuil minimum d'un produit à une valeur > stock actuel
- **Attendu :** Indicateur rouge/orange sur le produit

### TC-TRF-01 : Créer un transfert dépôt → boutique (RG-15/RG-17)
- Admin → Transferts → Nouveau transfert
- Source = Dépôt Central, Destination = Boutique Tanghin
- Produit = "Vis 6mm Test", Quantité = 10
- **Attendu :** Transfert créé avec statut `EN_TRANSIT`
- Stock dépôt décrémenté de 10, stock boutique inchangé

### TC-TRF-02 : Stock insuffisant (RG-18)
- Tenter un transfert avec quantité > stock disponible du dépôt
- **Attendu :** Erreur 409 `INSUFFICIENT_STOCK`

### TC-TRF-03 : Réceptionner un transfert (RG-17)
- Se connecter en Vendeuse (Boutique Tanghin) → Transferts → Réceptionner
- **Attendu :** Transfert passe à `RECU`, stock boutique incrémenté de 10

---

## Module 6 — Ventes (Caisse)

### TC-VENTE-01 : Vente simple
- Se connecter en Vendeuse → Caisse
- Ajouter un produit, valider
- **Attendu :** Vente créée, stock boutique décrémenté

### TC-VENTE-02 : Tarif technicien (RG-21)
- Créer une vente en sélectionnant le type client "Technicien"
- **Attendu :** Prix technicien appliqué (inférieur au prix simple)

### TC-VENTE-03 : Remise autorisée avec approbation (RG-22/RG-23)
- Créer une vente avec remise 10%
- Renseigner `approved_by_id` (sélectionner l'admin)
- **Attendu :** Vente créée avec remise

### TC-VENTE-04 : Remise sans approbateur rejetée (RF-16 côté serveur)
- Créer une vente avec remise 10% SANS renseigner `approved_by_id`
- **Attendu :** Erreur 422 "L'identité de l'approbateur est obligatoire pour toute remise"

### TC-VENTE-05 : Remise invalide (RG-22)
- Tenter une remise 12% (hors liste {0,5,10,15,20})
- **Attendu :** Erreur 400 de validation

### TC-VENTE-06 : Vente avec stock insuffisant (RG-24)
- Tenter de vendre 1000 unités d'un produit avec stock = 5
- **Attendu :** Erreur 409 `INSUFFICIENT_STOCK`

### TC-VENTE-07 : Vente immuable après validation (RG-27)
- Récupérer l'ID d'une vente validée
- Tenter de la modifier via l'interface
- **Attendu :** Pas de bouton de modification disponible pour une vente `VALIDEE`

### TC-VENTE-08 : Historique des ventes
- Admin → Historique des ventes
- **Attendu :** Liste des ventes paginée, filtrages fonctionnels

---

## Module 7 — Mode hors-ligne (PWA)

### TC-OFFLINE-01 : Vente hors connexion
- Se connecter en Vendeuse
- Ouvrir DevTools → Network → cocher "Offline"
- Créer une vente dans la caisse
- **Attendu :** Badge "Hors ligne" s'affiche, vente stockée localement
- Décocher "Offline" → vente synchronisée automatiquement

### TC-OFFLINE-02 : Idempotence (RG-28)
- Enregistrer une vente offline
- Synchroniser
- Tenter de re-synchroniser la même vente
- **Attendu :** Réponse `DEJA_SYNCHRONISE`, aucun doublon

---

## Module 8 — Inventaire physique (RF-21 à RF-23)

### TC-INV-01 : Lister les sessions d'inventaire
- Admin → Inventaire physique
- **Attendu :** Page chargée, tableau visible (vide si première fois)
- **Si erreur "Impossible de charger"** : exécuter `flask db upgrade` sur PythonAnywhere

### TC-INV-02 : Créer une session d'inventaire (RF-21)
- Cliquer "+ Nouvelle session"
- Sélectionner "Boutique Tanghin"
- **Attendu :** Session créée avec statut `EN_COURS`, lignes pré-remplies avec le stock théorique de chaque produit

### TC-INV-03 : Saisir les quantités comptées (RF-22)
- Ouvrir la session → entrer des quantités pour 2-3 produits
- **Attendu :** Écarts calculés automatiquement

### TC-INV-04 : Écart > 5% sans justification rejeté (RG-33)
- Entrer une quantité avec écart > 5% du stock théorique, sans commentaire
- Cliquer "Enregistrer les quantités"
- **Attendu :** Erreur "Justification requise si écart > seuil"

### TC-INV-05 : Valider la session (RF-23)
- Saisir toutes les quantités (avec justifications si nécessaire)
- Cliquer "Valider la session"
- **Attendu :** Session passe à `VALIDEE`, stock ajusté selon les comptages

### TC-INV-06 : Annuler une session EN_COURS
- Créer une nouvelle session → cliquer "Annuler la session"
- **Attendu :** Session passe à `ANNULE`, aucun ajustement de stock

### TC-INV-07 : Unicité de session par site
- Avec une session `EN_COURS` sur Boutique Tanghin
- Tenter de créer une nouvelle session sur Boutique Tanghin
- **Attendu :** Erreur 409 `STOCK_COUNT_IN_PROGRESS`

---

## Module 9 — Clients & Crédits

### TC-CLIENT-01 : Lister les clients
- Admin → Clients
- **Attendu :** Liste paginée des clients

### TC-CLIENT-02 : Vente à crédit (RF-18/RG-26)
- Caisse → créer une vente "à crédit" pour un client identifié
- **Attendu :** Solde dû du client augmenté du montant

### TC-CLIENT-03 : Vente à crédit sans client rejetée
- Tenter une vente "à crédit" sans sélectionner de client
- **Attendu :** Erreur 422 `CREDIT_REQUIRES_CUSTOMER`

### TC-CLIENT-04 : Enregistrer un paiement
- Credits → sélectionner un client avec solde dû > 0 → enregistrer paiement partiel
- **Attendu :** Solde dû réduit du montant payé

---

## Module 10 — Rapports

### TC-RPT-01 : Dashboard consolidé (Admin)
- Admin → Tableau de bord
- **Attendu :** CA, marges, top 5 produits, graph des ventes

### TC-RPT-02 : Dashboard Vendeur (limité à sa boutique)
- Vendeuse → Tableau de bord / "Ma performance"
- **Attendu :** Données uniquement pour Boutique Tanghin

### TC-RPT-03 : Rapport comptable
- Admin → Comptabilité
- **Attendu :** Synthèse des ventes, CA, TVA, marges par période

### TC-RPT-04 : Comparatif boutiques
- Admin → Comparatif boutiques
- **Attendu :** Graphique comparant les performances des boutiques

### TC-RPT-05 : Export PDF
- Depuis un rapport → bouton "Exporter PDF"
- **Attendu :** Fichier PDF téléchargé avec les données du rapport

---

## Module 11 — Utilisateurs & Audit

### TC-USR-01 : Lister les utilisateurs (Admin)
- Admin → Utilisateurs
- **Attendu :** Liste des 3 utilisateurs seeds + tout utilisateur créé

### TC-USR-02 : Créer un utilisateur
- Utilisateurs → Créer → Rôle VENDEUR, Boutique = Gounghin
- **Attendu :** Utilisateur créé avec `must_change_password=true`

### TC-USR-03 : Désactiver un utilisateur
- Sélectionner un utilisateur → Désactiver
- **Attendu :** Utilisateur ne peut plus se connecter (403 `ACCOUNT_DISABLED`)

### TC-AUDIT-01 : Journal d'audit
- Admin → Audit
- **Attendu :** Liste des événements (connexions, ventes, remises...)

### TC-AUDIT-02 : Filtrage par type d'événement
- Audit → filtrer par `LOGIN_FAILED`
- **Attendu :** Seules les tentatives de connexion échouées apparaissent

---

## Module 12 — Analytique IA

### TC-AI-01 : Dashboard analytique
- Admin → Analytique
- **Attendu :** Page chargée, onglets visibles

### TC-AI-02 : Prévisions de demande (Prophet)
- Analytique → Prévisions
- **Attendu :** Graphique de prévision avec `data_confidence` affiché

### TC-AI-03 : Alertes rupture de stock
- **Attendu :** Produits avec stock < seuil_min listés avec date estimée de rupture

### TC-AI-04 : Scoring crédit clients
- Analytique → Scoring crédit
- **Attendu :** Liste des clients avec score et niveau de risque

### TC-AI-05 : Explication SHAP d'un score crédit
- Cliquer sur un client → "Expliquer ce score"
- **Attendu :** Graphique SHAP des facteurs déterminants (montant moyen, délai paiement, etc.)

### TC-AI-06 : Détection d'anomalies
- Analytique → Anomalies
- **Attendu :** Liste des transactions suspectes avec raisons détaillées

### TC-AI-07 : Classification ABC/XYZ
- Analytique → ABC/XYZ
- **Attendu :** Tableau des produits classifiés (A/B/C × X/Y/Z)

### TC-AI-08 : Segmentation RFM
- Analytique → Segmentation clients
- **Attendu :** Segments (Champions, Fidèles, À risque...) avec effectifs

### TC-AI-09 : K-optimal RFM (Silhouette/Elbow)
- Analytique → Segmentation → "Évaluer K optimal"
- **Attendu :** Scores Silhouette et Elbow pour K=2 à K=8

### TC-AI-10 : Probabilité de churn
- Analytique → Risque de churn
- **Attendu :** Liste clients avec probabilité de départ

### TC-AI-11 : Analyse paniers (Market Basket)
- Analytique → Paniers d'achat
- **Attendu :** Règles d'association (ex. "Boulon → Vis, support=0.15")

### TC-AI-12 : Élasticité-prix
- Analytique → Élasticité prix
- **Attendu :** Tableau avec coefficient d'élasticité par produit

### TC-AI-13 : Contexte africain BF
- Analytique → Contexte africain
- **Attendu :** Indicateurs saisonnalité BF, week-end boost, stress trésorerie

### TC-AI-14 : Entraînement manuel
- Analytique → "Entraîner les modèles" → sélectionner "demand_forecast"
- **Attendu :** Réponse 202 `{"status":"started"}`, entraînement en arrière-plan

---

## Module 13 — Avoirs & Retours

### TC-AVOIR-01 : Créer un avoir
- Historique ventes → sélectionner une vente validée → Créer avoir
- **Attendu :** Vente négative créée (avoir), stock boutique recrédité

---

## Module 14 — Monitoring & Infrastructure

### TC-MON-01 : Endpoint /health
- Ouvrir : https://mannudev.pythonanywhere.com/health
- **Attendu :**
  ```json
  {
    "status": "ok",
    "db": "ok",
    "ml_models_actifs": N,
    "uptime_s": X,
    "version": "dev",
    "timestamp_utc": "..."
  }
  ```

### TC-MON-02 : Page 404 personnalisée
- Aller sur https://mannudev.pythonanywhere.com/une-page-qui-nexiste-pas
- **Attendu :** Page 404 de l'application React (pas une erreur brute Flask)

### TC-MON-03 : Logs d'erreur PythonAnywhere
- PythonAnywhere → Web → Log files → `error.log`
- **Attendu :** Aucune erreur 500 récente

---

## Récapitulatif des résultats

| ID | Description | ✅/❌ | Observations |
|---|---|---|---|
| TC-AUTH-01 | Connexion valide Admin | | |
| TC-AUTH-02 | MDP incorrect → rejet | | |
| TC-AUTH-03 | Rate limiting 429 | | |
| TC-AUTH-04 | must_change_password RF-05 | | |
| TC-AUTH-05 | Déconnexion | | |
| TC-AUTH-06 | RBAC Vendeur pas de création produit | | |
| TC-AUTH-07 | RBAC Vendeur vue boutique seule | | |
| TC-DASH-01 | Dashboard Admin | | |
| TC-DASH-02 | Dashboard Vendeur | | |
| TC-PROD-01 | Liste produits | | |
| TC-PROD-02 | Créer produit | | |
| TC-PROD-03 | Prix technicien > prix simple rejeté | | |
| TC-PROD-04 | Recherche phonétique | | |
| TC-FOUR-01 | Liste fournisseurs | | |
| TC-FOUR-03 | Réception marchandises | | |
| TC-STK-01 | Stock par site | | |
| TC-TRF-01 | Transfert dépôt → boutique | | |
| TC-TRF-02 | Stock insuffisant → 409 | | |
| TC-TRF-03 | Réception transfert | | |
| TC-VENTE-01 | Vente simple | | |
| TC-VENTE-02 | Tarif technicien | | |
| TC-VENTE-03 | Remise avec approbateur | | |
| TC-VENTE-04 | Remise sans approbateur → 422 | | |
| TC-VENTE-05 | Remise invalide → 400 | | |
| TC-VENTE-06 | Stock insuffisant vente → 409 | | |
| TC-OFFLINE-01 | Vente hors-ligne + sync | | |
| TC-INV-01 | Liste inventaires | | |
| TC-INV-02 | Créer session inventaire | | |
| TC-INV-03 | Saisir quantités comptées | | |
| TC-INV-04 | Écart > 5% sans justification → erreur | | |
| TC-INV-05 | Valider session | | |
| TC-INV-06 | Annuler session | | |
| TC-INV-07 | Unicité session par site | | |
| TC-CLIENT-02 | Vente à crédit | | |
| TC-CLIENT-03 | Crédit sans client → 422 | | |
| TC-RPT-01 | Dashboard consolidé | | |
| TC-RPT-05 | Export PDF | | |
| TC-AI-01 | Page analytique | | |
| TC-AI-02 | Prévisions Prophet | | |
| TC-AI-04 | Scoring crédit | | |
| TC-AI-05 | SHAP explication | | |
| TC-AI-06 | Anomalies | | |
| TC-AI-07 | ABC/XYZ | | |
| TC-AI-08 | Segmentation RFM | | |
| TC-AI-11 | Market Basket | | |
| TC-AI-12 | Élasticité-prix | | |
| TC-MON-01 | /health → 200 ok | | |

---

## Guide de dépannage rapide

| Erreur visible | Cause probable | Solution |
|---|---|---|
| "Failed to fetch dynamically imported module" | Cache navigateur/SW stale | Ctrl+Shift+Del → vider cache + SW → recharger |
| "Impossible de charger les sessions d'inventaire" | Migrations non appliquées | `flask db upgrade` dans PythonAnywhere Bash |
| Toutes les pages donnent 500 | Erreur app Flask | PythonAnywhere → Web → error.log |
| Token expiré (déconnexion auto) | Access token 15 min | Normal — se reconnecter |
| 403 PASSWORD_CHANGE_REQUIRED | must_change_password=true | Aller sur `/changer-mot-de-passe` |
| 429 Too Many Requests | Rate limiting déclenché | Attendre 1 min (login) ou 1h (register) |
| Prévisions IA vides | Modèles pas encore entraînés | Analytique → Entraîner les modèles |
| Page blanche après login | Session expirée ou JWT invalide | Vider localStorage + recharger |
