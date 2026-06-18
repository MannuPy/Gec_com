# 3. Analyse des besoins

## 3.1 Exigences fonctionnelles (RF)

### Module Authentification & Utilisateurs

| ID | Exigence | Priorité |
|---|---|---|
| RF-01 | Le système doit permettre l'inscription d'une entreprise (tenant) avec un administrateur initial | Must |
| RF-02 | Le système doit permettre la connexion via email/mot de passe avec délivrance d'un JWT (access + refresh token) | Must |
| RF-03 | Le système doit permettre à l'administrateur de créer, modifier, désactiver des comptes utilisateurs et leur attribuer un rôle | Must |
| RF-04 | Le système doit permettre la déconnexion et l'invalidation du refresh token | Must |
| RF-05 | Le système doit forcer le changement de mot de passe à la première connexion | Should |

### Module Produits & Catalogue

| ID | Exigence | Priorité |
|---|---|---|
| RF-06 | Le système doit permettre la gestion des catégories et marques de produits | Must |
| RF-07 | Le système doit permettre la création d'un produit avec référence unique, prix d'achat, prix de vente client simple, prix technicien, seuil d'alerte stock minimum | Must |
| RF-08 | Le système doit permettre la recherche de produits par nom, référence, catégorie, avec tolérance aux fautes de frappe (recherche phonétique) | Should |
| RF-09 | Le système doit permettre l'affichage du libellé produit en français et en mooré | Could |

### Module Fournisseurs & Approvisionnement

| ID | Exigence | Priorité |
|---|---|---|
| RF-10 | Le système doit permettre la gestion des fournisseurs (coordonnées, historique des achats) | Must |
| RF-11 | Le système doit permettre l'enregistrement des réceptions de marchandises au dépôt central, avec mise à jour automatique du stock | Must |

### Module Dépôt & Transferts

| ID | Exigence | Priorité |
|---|---|---|
| RF-12 | Le système doit gérer un stock distinct pour le dépôt central et pour chaque boutique | Must |
| RF-13 | Le système doit permettre de créer un transfert de produits du dépôt vers une boutique (ou entre boutiques) avec statut (en attente, en transit, reçu) | Must |
| RF-14 | Le système doit décrémenter automatiquement le stock source et incrémenter le stock destination à la réception du transfert | Must |

### Module Ventes

| ID | Exigence | Priorité |
|---|---|---|
| RF-15 | Le système doit permettre d'enregistrer une vente avec un ou plusieurs produits, en appliquant le tarif client simple ou technicien selon le profil client | Must |
| RF-16 | Le système doit permettre l'application d'une remise parmi {5 %, 10 %, 15 %, 20 %} sur une vente, avec enregistrement de l'identité de l'administrateur ayant donné son accord verbal | Must |
| RF-17 | Le système doit décrémenter le stock de la boutique au moment de la validation de la vente | Must |
| RF-18 | Le système doit permettre la vente à crédit pour les clients identifiés, avec suivi du solde dû | Should |
| RF-19 | Le système doit permettre de générer un reçu de vente (PDF ou impression) | Should |
| RF-20 | Le système doit permettre la saisie d'une vente **en mode hors-ligne**, stockée localement et synchronisée au retour de la connexion | Must |

### Module Inventaires

| ID | Exigence | Priorité |
|---|---|---|
| RF-21 | Le système doit permettre de lancer un inventaire physique pour le dépôt ou une boutique | Must |
| RF-22 | Le système doit permettre de saisir les quantités physiquement comptées et calculer l'écart avec le stock théorique | Must |
| RF-23 | Le système doit permettre la validation de l'inventaire et l'ajustement automatique du stock théorique | Must |

### Module Rapports & Analytics

| ID | Exigence | Priorité |
|---|---|---|
| RF-24 | Le système doit fournir un tableau de bord avec chiffre d'affaires, marges, top produits, par boutique et consolidé | Must |
| RF-25 | Le système doit fournir une prévision de rupture de stock par produit/boutique à horizon 7-30 jours | Must |
| RF-26 | Le système doit fournir un scoring de solvabilité pour les clients à crédit | Should |
| RF-27 | Le système doit détecter et signaler les anomalies (ventes suspectes, remises excessives, mouvements de stock inhabituels) | Should |
| RF-28 | Le système doit fournir une classification ABC/XYZ des produits avec recommandations de réapprovisionnement | Should |
| RF-29 | Le système doit permettre l'export des rapports en PDF | Should |

### Module Audit & Sécurité

| ID | Exigence | Priorité |
|---|---|---|
| RF-30 | Le système doit journaliser tous les événements sensibles (connexion, vente, remise, modification de prix, transfert) au format JSON | Must |
| RF-31 | Le système doit appliquer un contrôle d'accès basé sur les rôles (RBAC) pour chaque endpoint | Must |
| RF-32 | Le système doit permettre à l'administrateur de consulter les journaux d'audit filtrés par utilisateur, type d'événement, période | Should |

## 3.2 Exigences non-fonctionnelles (RNF)

| ID | Catégorie | Exigence | Cible |
|---|---|---|---|
| RNF-01 | Performance | Temps de réponse API (hors traitements ML asynchrones) | **< 200 ms** (p95) |
| RNF-02 | Disponibilité | Disponibilité du service (hors maintenance planifiée) | **≥ 99,5 %** |
| RNF-03 | Scalabilité (volumétrie) | Nombre de produits par tenant | jusqu'à **20 000** |
| RNF-04 | Scalabilité (volumétrie) | Nombre de transactions de vente / jour / tenant | jusqu'à **2 000** |
| RNF-05 | Scalabilité (volumétrie) | Nombre de boutiques par tenant | jusqu'à **50** |
| RNF-06 | Scalabilité (volumétrie) | Nombre de tenants supportés (architecture cible) | jusqu'à **200** la première année |
| RNF-07 | Sécurité | Chiffrement des données sensibles en transit | **TLS 1.2+ obligatoire (HTTPS)** |
| RNF-08 | Sécurité | Chiffrement des mots de passe | **bcrypt / argon2**, jamais en clair |
| RNF-09 | Sécurité | Expiration des tokens JWT | access token 15 min, refresh token 7 jours |
| RNF-10 | Disponibilité offline | Continuité de la vente sans connexion | **100 % des fonctions de vente disponibles offline**, synchronisation automatique < 5 min après reconnexion |
| RNF-11 | Sauvegarde | Fréquence de backup PostgreSQL | **quotidienne**, rétention 30 jours + backup hebdomadaire 6 mois |
| RNF-12 | Reprise d'activité | RTO (Recovery Time Objective) | **< 4 heures** |
| RNF-13 | Reprise d'activité | RPO (Recovery Point Objective) | **< 24 heures** |
| RNF-14 | Maintenabilité | Couverture de tests automatisés | **≥ 80 %** (backend et frontend) |
| RNF-15 | Portabilité | Déploiement | **conteneurisé (Docker)**, reproductible sur tout environnement Linux |
| RNF-16 | Accessibilité | Compatibilité interface | **français + mooré**, design responsive (tablette/mobile) |
| RNF-17 | Observabilité | Traçabilité des prédictions IA | chaque prédiction doit être traçable jusqu'à la donnée source et la version du modèle (data lineage) |
| RNF-18 | Conformité | Rétention des logs d'audit | **1 an minimum** |

## 3.3 Matrice de priorisation (MoSCoW)

| Priorité | Nombre d'exigences RF | Exemples |
|---|---|---|
| **Must** | 19 | Authentification, RBAC, ventes, stock, transferts, inventaires, dashboard, prévision de rupture, offline, audit |
| **Should** | 9 | Crédit client, reçu PDF, scoring, anomalies, ABC/XYZ, export PDF, mot de passe initial |
| **Could** | 1 | Libellés produits en mooré |
| **Won't (cette version)** | - | App mobile native, mobile money (cf. `31-CONCLUSION-PERSPECTIVES.md`) |

## 3.4 Traçabilité besoins → modules

| Module fonctionnel | RF couvertes | Document de référence |
|---|---|---|
| Authentification | RF-01 à RF-05 | `18-SECURITE.md` |
| Produits | RF-06 à RF-09 | `11-BASE-DE-DONNEES.md` |
| Fournisseurs | RF-10, RF-11 | `11-BASE-DE-DONNEES.md` |
| Dépôt & Transferts | RF-12 à RF-14 | `05-ARCHITECTURE-FONCTIONNELLE.md` |
| Ventes | RF-15 à RF-20 | `06-CAS-DUTILISATION.md`, `26-GESTION-OFFLINE-PWA.md` |
| Inventaires | RF-21 à RF-23 | `11-BASE-DE-DONNEES.md` |
| Rapports & IA | RF-24 à RF-29 | `19-ANALYSE-DE-DONNEES.md`, `20-MACHINE-LEARNING.md`, `22-DASHBOARD-BI.md` |
| Audit | RF-30 à RF-32 | `28-MONITORING-OBSERVABILITE.md` |
