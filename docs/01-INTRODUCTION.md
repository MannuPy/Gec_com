# 1. Introduction & Contexte

## 1.1 Contexte général

Au Burkina Faso, le secteur de la quincaillerie et des pièces détachées (automobile, motocycle, BTP) est dominé par des commerces de taille petite à moyenne, organisés le plus souvent autour d'un **dépôt central** et d'un réseau de **boutiques de vente**. La gestion y est encore très largement manuelle :

- Suivi des stocks sur cahiers ou fichiers Excel non centralisés
- Absence de visibilité en temps réel sur les stocks entre dépôt et boutiques
- Erreurs fréquentes de prix (tarif client simple vs technicien)
- Remises accordées de façon informelle, sans traçabilité
- Aucune anticipation des ruptures de stock
- Aucune donnée exploitable pour la prise de décision

Cette situation entraîne des **pertes financières** (ruptures de stock, surstockage, remises non contrôlées, vols/erreurs non détectés) et une **incapacité à piloter l'activité** sur plusieurs points de vente.

## 1.2 Problématique

> Comment doter les quincailleries et boutiques de pièces détachées du Burkina Faso d'un outil de gestion commerciale **centralisé, fiable, accessible même en cas de coupure internet**, et capable de **transformer leurs données de vente en aide à la décision** (prévisions, alertes, scoring client) ?

## 1.3 Analyse de l'existant (synthèse)

Une analyse détaillée des solutions existantes (Odoo, Sage, Wave ERP, solutions artisanales Excel) est fournie dans `02-ETUDE-DU-MARCHE.md`. En synthèse :

- Les ERP génériques (Odoo, Sage) sont **puissants mais surdimensionnés, coûteux et exigeants en connexion internet stable** — peu adaptés au contexte des quincailleries de taille moyenne en zone à connectivité intermittente.
- Les solutions artisanales (Excel, cahiers) ne permettent **aucune centralisation multi-boutiques ni analyse prédictive**.
- Aucune solution étudiée n'intègre nativement un **mode hors-ligne robuste** ni un **module IA contextualisé** (saisonnalité locale, scoring de crédit informel).

→ D'où l'opportunité d'une solution **sur-mesure, légère, modulaire, offline-first et orientée data**.

## 1.4 Périmètre du projet

### Inclus dans le périmètre

- Gestion d'une entreprise avec **un dépôt central** et **plusieurs boutiques**
- Gestion des utilisateurs et rôles (Administrateur, Magasinier, Vendeur)
- Gestion des produits, fournisseurs, catégories, marques
- Gestion des stocks (dépôt + boutiques) et des transferts inter-sites
- Gestion des ventes avec double tarification (client simple / technicien) et remises encadrées
- Gestion des inventaires physiques
- Rapports décisionnels et tableaux de bord
- Module d'analyse de données et d'intelligence artificielle (prévision de rupture, scoring crédit, détection d'anomalies, ABC/XYZ)
- Mode offline-first (PWA) pour la vente en boutique
- Architecture SaaS multi-tenant (plusieurs entreprises clientes)
- Module d'audit et de sécurité (RBAC, logs)

### Hors périmètre (perspectives futures, cf. `31-CONCLUSION-PERSPECTIVES.md`)

- Application mobile native (Android/iOS)
- Intégration paiement mobile money (Orange Money, Moov Money)
- Module de comptabilité générale / fiscalité complète
- Marketplace B2B entre quincailleries

## 1.5 Objectifs SMART

| # | Objectif | Spécifique | Mesurable | Atteignable | Réaliste | Temporel |
|---|---|---|---|---|---|---|
| O1 | Centraliser la gestion des stocks dépôt + boutiques | Module Stock + Transferts | 100 % des mouvements tracés en base | Oui (architecture définie) | Oui | Sprint 1-3 |
| O2 | Réduire le temps de saisie d'une vente | Module Ventes avec raccourcis caissier | Saisie d'une vente < 30 secondes | Oui (UX dédiée) | Oui | Sprint 4-5 |
| O3 | Anticiper les ruptures de stock | Modèle Prophet par produit/boutique | RMSE < 15 % de la demande moyenne | Oui (données historiques simulées) | Oui | Sprint 8-9 |
| O4 | Garantir la continuité de service hors-ligne | PWA + Service Worker + IndexedDB | 100 % des ventes saisissables hors-ligne, synchronisées en < 5 min après reconnexion | Oui | Oui | Sprint 6-7 |
| O5 | Sécuriser l'accès aux données | RBAC + JWT + chiffrement | 0 accès non autorisé lors des tests de sécurité | Oui | Oui | Sprint 2 |
| O6 | Détecter les anomalies de gestion | Isolation Forest sur ventes/remises/stocks | Taux de faux positifs < 10 % sur jeu de test | Oui | Oui | Sprint 10 |
| O7 | Fournir un tableau de bord décisionnel | Dashboard React + WebSocket | Temps de rafraîchissement < 2 s | Oui | Oui | Sprint 9-10 |
| O8 | Couvrir le code par des tests automatisés | pytest + Jest | Couverture ≥ 80 % | Oui | Oui | Continu |

## 1.6 Utilisateurs du système

| Rôle | Description | Niveau d'accès |
|---|---|---|
| **Administrateur** | Gère l'entreprise, les boutiques, les utilisateurs, valide les remises, consulte tous les rapports et le module IA | Accès complet (scopé à son tenant) |
| **Magasinier** | Gère le dépôt central : réceptions fournisseurs, transferts vers boutiques, inventaires | Accès Dépôt, Stock, Transferts, Inventaires |
| **Vendeur** | Effectue les ventes en boutique, consulte le stock de sa boutique, applique les remises autorisées | Accès Ventes, Stock (lecture boutique) |
| **Super-Administrateur (SaaS)** | Gère les tenants, la facturation, le monitoring global (cf. `27-MODELE-SAAS-MULTITENANT.md`) | Accès plateforme |

## 1.7 Particularités métier (contraintes locales)

- **Un seul dépôt central** par entreprise, avec **N boutiques**
- Pas de scanner code-barres obligatoire (saisie manuelle ou recherche assistée)
- **Deux tarifs de vente** : Client simple et Technicien
- **Remises fixes** : 5 %, 10 %, 15 %, 20 % — pas de remise libre
- Validation des remises par **accord verbal de l'administrateur**, tracé dans le système (cf. RG dans `04-REGLES-METIER.md`)
- **Coupures internet fréquentes** → nécessité d'un mode offline-first (cf. `26-GESTION-OFFLINE-PWA.md`)
- **Saisonnalité locale** : fêtes (Tabaski, Noël, Nouvel An), saison des pluies (juin-octobre) impactant fortement la demande en pièces détachées et matériaux
- Possibilité de **vente à crédit informel** pour certains clients fidèles (artisans, techniciens)
- Certains utilisateurs sont peu familiers avec les outils numériques → interface simplifiée, support du **mooré** pour les libellés produits (cf. `29-WIREFRAMES-UI.md`)

## 1.8 Lecture recommandée

Pour une lecture en vue de la soutenance, suivre l'ordre des fichiers numérotés du dossier `docs/`. Pour une lecture technique ciblée (développeur backend, par exemple), se référer directement à `08-ARCHITEC