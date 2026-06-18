# 29. Wireframes UI (maquettes basse fidélité)

## 29.1 Objectif

Donner une représentation visuelle des écrans clés avant développement, en cohérence avec les écrans listés dans `10-FRONTEND-REACT.md` (tableau des écrans) et les parcours `06-CAS-DUTILISATION.md`. Ces maquettes basse fidélité (ASCII) servent de support de discussion ; une déclinaison Figma est une perspective (`31-CONCLUSION-PERSPECTIVES.md`).

## 29.2 Écran de connexion (UC-01)

```text
┌──────────────────────────────────────────────┐
│                                                │
│              [Logo GesCom-BF]                 │
│                                                │
│      ┌──────────────────────────────┐        │
│      │ Email                         │        │
│      └──────────────────────────────┘        │
│      ┌──────────────────────────────┐        │
│      │ Mot de passe            👁     │        │
│      └──────────────────────────────┘        │
│                                                │
│            [ Se connecter ]                   │
│                                                │
│      Langue :  🇫🇷 Français  |  Mooré         │
│                                                │
│      v1.0.0 — GesCom-BF SaaS                  │
└──────────────────────────────────────────────┘
```

| Élément | Comportement |
|---|---|
| Champ email/mot de passe | Validation côté client (Zod), message d'erreur sous le champ |
| Bouton "Se connecter" | Désactivé pendant la requête, spinner intégré |
| Sélecteur de langue | Persisté en `localStorage`, applique i18next (RF-32) |
| Erreur de connexion | Bandeau rouge au-dessus du formulaire : "Email ou mot de passe incorrect" |

## 29.3 Écran de caisse / vente (UC-11, UC-12, UC-13) — écran central de l'application

```text
┌──────────────────────────────────────────────────────────────────┐
│ 🟢 En ligne   GesCom-BF — Boutique Tanghin      👤 Aïcha (Vendeur) │
├──────────────────────────────────────────────────────────────────┤
│ 🔍 [_____Rechercher produit (nom, code-barres)_____]   [Scan 📷]  │
├──────────────────────────────────────────────┬───────────────────┤
│ Résultats recherche (fuzzy search)            │  TICKET EN COURS  │
│ ┌────────────────────────────────────────┐   │ ─────────────────│
│ │ Vis 6mm (boîte 100)      450 F  Stock:120│   │ Vis 6mm  x2  900F │
│ │ Vis 8mm (boîte 100)      550 F  Stock: 45│   │ Ciment 50kg x1    │
│ │ Ciment CIM 50kg         6500 F  Stock: 30│   │          6500F    │
│ └────────────────────────────────────────┘   │ ─────────────────│
│                                                │ Sous-total: 7400F │
│ Touches rapides :                             │ Remise: [0%▾]     │
│ [F1 Nouvelle vente] [F2 Client] [F3 Remise]   │ TOTAL  : 7400 F   │
│ [F4 Paiement] [F5 Annuler ligne] [F8 Valider] │                   │
│                                                │ Type paiement:    │
│                                                │ (•) Comptant      │
│                                                │ ( ) Crédit        │
│                                                │                   │
│                                                │ [  VALIDER (F8) ] │
└────────────────────────────────────────────────┴───────────────────┘
```

| Élément | Détail |
|---|---|
| Pastille connexion (haut gauche) | 🟢 En ligne / 🟡 Hors-ligne (cf. `26-GESTION-OFFLINE-PWA.md` §26.8) |
| Recherche fuzzy | Tolère fautes de frappe, recherche par nom ou code-barres, résultats < 200 ms (RNF-01) |
| Sélecteur de remise (F3) | Limité aux taux autorisés [0, 5, 10, 15, 20] % (RG-22) ; si ≥ 10 %, ouvre modal d'approbation (RG-23) |
| Sélecteur client (F2) | Requis si paiement = Crédit (RG-26), recherche client existant ou création rapide |
| Bouton Valider (F8) | Déclenche `POST /sales` (en ligne) ou écriture IndexedDB (hors-ligne) |
| Bascule Mooré | Icône globe en haut à droite (non représentée ci-dessus pour la lisibilité), bascule les libellés (RF-32) |

### 29.3.1 Modal d'approbation de remise (RG-23)

```text
┌─────────────────────────────────────────┐
│  Remise de 15% — Approbation requise     │
│                                           │
│  Code PIN administrateur :               │
│  [ • • • • ]                             │
│                                           │
│        [ Annuler ]   [ Valider ]         │
└─────────────────────────────────────────┘
```

## 29.4 Écran Catalogue / Produits (RF-06 à RF-10)

```text
┌──────────────────────────────────────────────────────────────────┐
│ Produits                              [+ Nouveau produit]         │
├──────────────────────────────────────────────────────────────────┤
│ 🔍 [Rechercher...]   Catégorie:[Toutes▾]  Marque:[Toutes▾]         │
├──────────────────────────────────────────────────────────────────┤
│ Code    │ Nom              │ Catégorie │ Prix simple │ Prix tech. │ Stock │
│ P-00123 │ Vis 6mm boîte100 │ Visserie  │   450 F     │   400 F    │  120  │
│ P-00124 │ Vis 8mm boîte100 │ Visserie  │   550 F     │   500 F    │   45  │ ⚠
│ P-00200 │ Ciment CIM 50kg  │ Matériaux │  6500 F     │  6200 F    │   30  │
├──────────────────────────────────────────────────────────────────┤
│  ⚠ = alerte rupture imminente (cf. prévision IA)                  │
│  Pagination : ◀ 1 2 3 ... 40 ▶                                     │
└──────────────────────────────────────────────────────────────────┘
```

## 29.5 Écran Transferts inter-sites (UC-08, UC-09)

```text
┌──────────────────────────────────────────────────────────────────┐
│ Transferts                              [+ Nouveau transfert]      │
├──────────────────────────────────────────────────────────────────┤
│ Réf.     │ Origine │ Destination │ Statut       │ Date    │ Action │
│ TR-0045  │ Dépôt   │ Boutique A  │ EN_TRANSIT   │ 12/06   │ [Recevoir] │
│ TR-0044  │ Dépôt   │ Boutique B  │ RECU         │ 10/06   │ [Voir]     │
│ TR-0043  │ Dépôt   │ Boutique A  │ ANNULE       │ 08/06   │ [Voir]     │
└──────────────────────────────────────────────────────────────────┘
```

### 29.5.1 Détail réception de transfert (UC-09)

```text
┌──────────────────────────────────────────────────────────────────┐
│ Réception TR-0045 — Dépôt → Boutique A                             │
├──────────────────────────────────────────────────────────────────┤
│ Produit            │ Qté envoyée │ Qté reçue (à saisir)  │ Écart   │
│ Vis 6mm boîte100   │     50      │ [   50   ]            │   0     │
│ Ciment CIM 50kg    │     20      │ [   18   ]            │  -2 ⚠   │
├──────────────────────────────────────────────────────────────────┤
│ Commentaire écart : [_____________________________]               │
│                                                                     │
│                          [ Confirmer la réception ]               │
└──────────────────────────────────────────────────────────────────┘
```

## 29.6 Écran Inventaire (UC-10, RG-33)

```text
┌──────────────────────────────────────────────────────────────────┐
│ Inventaire — Boutique Tanghin — 14/06/2026         [En cours]      │
├──────────────────────────────────────────────────────────────────┤
│ Produit          │ Stock théorique │ Comptage │ Écart  │ Justif.   │
│ Vis 6mm boîte100 │       120       │ [ 118 ]  │  -2    │ [______]  │
│ Ciment CIM 50kg  │        30       │ [  28 ]  │  -2    │ [______]  │
│ Peinture 1L Blc  │        15       │ [  16 ]  │  +1    │ [______]  │
├──────────────────────────────────────────────────────────────────┤
│ ⚠ Écart Ciment CIM 50kg = -6,7% (> seuil 5%) → justification requise │
│                                                                     │
│              [ Enregistrer brouillon ]   [ Valider l'inventaire ] │
└──────────────────────────────────────────────────────────────────┘
```

## 29.7 Dashboard administrateur

Voir la maquette détaillée en `22-DASHBOARD-BI.md` §22.4 — reproduite ici pour rappel de cohérence visuelle (mêmes composants : KPIs, graphique CA, alertes IA temps réel, ABC/XYZ, RFM).

## 29.8 Écran Module IA — Prévisions de rupture (UC-16)

```text
┌──────────────────────────────────────────────────────────────────┐
│ Prévisions de rupture de stock          Boutique : [Tanghin ▾]    │
├──────────────────────────────────────────────────────────────────┤
│ Produit          │ Stock actuel │ Rupture prévue │ Qté recommandée│
│ Vis 8mm boîte100 │      45      │   J+5 (19/06)  │      450       │
│ Peinture 5L Rouge│      12      │   J+9 (23/06)  │      80        │
├──────────────────────────────────────────────────────────────────┤
│ [Graphique : prévision de demande 30 jours - Vis 8mm boîte100]    │
│                                                                     │
│   demande                                                          │
│   30 │           ___                                              │
│   20 │      ___--   \___                                          │
│   10 │ ____/              intervalle de confiance 80% (zone grise)│
│    0 └─────────────────────────────────────────────────► jours    │
│                                                                     │
│        [Commander 450 unités auprès de : Fournisseur SOBA]        │
└──────────────────────────────────────────────────────────────────┘
```

## 29.9 Écran Module IA — Score de solvabilité client (UC-13 contexte)

```text
┌──────────────────────────────────────────────────────────────────┐
│ Fiche client : Konaté Issouf                                       │
├──────────────────────────────────────────────────────────────────┤
│ Score de solvabilité :  72.5 / 100      Niveau : MOYEN 🟡          │
│                                                                     │
│ Facteurs principaux :                                              │
│   - Taux de retard historique : faible (impact positif)           │
│   - Fréquence d'achat mensuelle : élevée (impact positif)          │
│                                                                     │
│ Encours actuel : 45 000 F   |  Plafond recommandé : 60 000 F       │
│                                                                     │
│ Segment RFM : "Clients réguliers"                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 29.10 Responsive & accessibilité

| Aspect | Recommandation |
|---|---|
| Écran de caisse | Optimisé pour tablette (10") et clavier physique (raccourcis F1-F8) |
| Dashboard | Optimisé desktop ; version mobile simplifiée (KPIs uniquement) en perspective V2 |
| Contraste | Respect WCAG AA pour les libellés de prix et alertes (lisibilité en environnement lumineux de boutique) |
| Taille de police | Minimum 14px sur écran de caisse pour lisibilité rapide par le vendeur |

## 29.11 Prochaine étape recommandée

Convertir ces wireframes en maquettes haute-fidélité (Figma) pour les écrans UC-11 (caisse) et dashboard avant le développement frontend du Sprint 5 (cf. `23-PLAN-DE-DEVELOPPEMENT.md`), afin de valider l'ergonomie auprès d'un utilisateur pilote si disponible.
