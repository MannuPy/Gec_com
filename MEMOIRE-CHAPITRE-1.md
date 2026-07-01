# CHAPITRE 1 : PRÉSENTATION DU CONTEXTE ET ÉTUDE DE L'EXISTANT

---

## Introduction

Avant de concevoir toute solution informatique, il est indispensable de comprendre le contexte dans lequel elle s'inscrit, d'identifier les acteurs concernés et d'évaluer les solutions déjà disponibles sur le marché. Ce premier chapitre présente l'environnement institutionnel du projet, dresse un état des lieux du secteur commercial ciblé au Burkina Faso, analyse les solutions existantes et leurs limites, puis définit la solution proposée, ses objectifs et son organisation.

---

## 1.1 Présentation de l'UVBF

L'Université Virtuelle du Burkina Faso (UVBF) est un établissement public d'enseignement supérieur créé pour répondre aux besoins croissants de formation dans le pays, tout en s'appuyant sur les technologies du numérique pour rendre l'enseignement accessible au plus grand nombre, y compris dans les zones éloignées des grandes villes.

Sa mission est de dispenser des formations diplômantes de qualité — du niveau licence au master — dans des domaines répondant aux besoins du marché du travail burkinabè, notamment en sciences et technologies du numérique, en gestion et en droit. L'UVBF s'appuie sur une pédagogie à distance enrichie par des séquences en présentiel, permettant aux étudiants de combiner formation et activité professionnelle.

Le présent mémoire est produit dans le cadre d'un cursus en **[Génie Logiciel / Analyse de Données — à préciser]** au sein de l'UVBF, et vise à démontrer la maîtrise du cycle complet de développement d'un système d'information réel, de l'analyse des besoins au déploiement en production.

---

## 1.2 Secteur cible : la quincaillerie et les pièces détachées au Burkina Faso

### 1.2.1 État des lieux du secteur

Le secteur de la quincaillerie et des pièces détachées — pièces automobiles, pièces motocycle, matériaux de construction, équipements BTP — constitue une composante importante du tissu commercial urbain et péri-urbain du Burkina Faso. Dans les grandes villes comme Ouagadougou et Bobo-Dioulasso, ces commerces sont nombreux et occupent une place centrale dans l'approvisionnement des artisans, techniciens garagistes, maçons et particuliers.

Ces entreprises présentent des caractéristiques structurelles communes :

- Une organisation en **dépôt central unique** qui reçoit les marchandises des fournisseurs (importateurs grossistes) et les redistribue vers une ou plusieurs **boutiques de vente** au détail
- Un double marché clientèle : les **clients simples** (particuliers) et les **techniciens/artisans professionnels**, auxquels s'appliquent des tarifs différenciés — une réalité commerciale locale que les ERP génériques ne modélisent pas nativement
- Un recours fréquent à la **vente à crédit informel**, sans contrat ni système de suivi formalisé
- Une dépendance forte aux **cycles saisonniers** (saison des pluies impactant le BTP, fêtes religieuses augmentant les déplacements et donc la demande en pièces auto)

Sur le plan de la maturité numérique, une enquête de terrain conduite dans le cadre de ce projet révèle que la très grande majorité de ces commerces gèrent encore leur activité de façon entièrement manuelle ou semi-manuelle, avec des outils non conçus pour la gestion commerciale professionnelle.

### 1.2.2 Problèmes identifiés

L'analyse de terrain permet d'identifier six catégories de problèmes récurrents.

**Gestion des stocks non centralisée.** Lorsqu'une entreprise dispose d'un dépôt et de plusieurs boutiques, chaque site tient son propre cahier ou fichier Excel. Le gérant n'a aucune visibilité en temps réel sur les niveaux de stock consolidés. Les ruptures de stock en boutique ne sont découvertes que lors d'une vente ratée, faute de système d'alerte.

**Absence de suivi des transferts.** Les mouvements de marchandises entre le dépôt et les boutiques sont enregistrés sur des bons papier qui peuvent être perdus, falsifiés ou oubliés. Il n'existe aucune traçabilité fiable des quantités transférées, reçues et vendues.

**Erreurs de tarification.** La double grille de prix (client simple / technicien) est appliquée de mémoire par le vendeur, ce qui génère des erreurs fréquentes — soit le client simple bénéficie du tarif technicien, soit le technicien se voit appliquer le tarif standard, au détriment de la marge ou de la relation commerciale.

**Remises non contrôlées.** Les remises sont accordées verbalement et sans traçabilité. Le gérant ne peut pas savoir a posteriori combien de remises ont été accordées, par qui, à quel client, et sur quel montant. Ce manque de contrôle représente une source significative de perte de chiffre d'affaires.

**Incapacité à piloter sur données.** Sans historique structuré, le gérant prend ses décisions d'approvisionnement par instinct ou par expérience empirique. Il ne peut pas identifier quels produits se vendent mieux, quelles boutiques sont plus performantes, quels clients sont à risque de défaut de paiement, ni anticiper les périodes de forte demande.

**Fragilité face aux coupures internet.** Lorsqu'une solution numérique est tentée, les coupures d'électricité ou d'internet — fréquentes au Burkina Faso — rendent le système inutilisable, forçant un retour au papier.

---

## 1.3 Analyse des solutions existantes

### 1.3.1 Solutions ERP génériques étudiées

Cinq solutions ont été analysées et comparées dans le cadre de ce projet.

**Odoo** est un ERP open-source modulaire très complet, couvrant la comptabilité, les achats, le stock, le CRM et bien d'autres fonctions. Il est techniquement capable de gérer un dépôt et des boutiques, mais son déploiement nécessite une expertise technique avancée, une connexion internet permanente pour la version cloud, et son coût de licence (Odoo Enterprise) ou de maintenance (hébergement, intégrateur) est hors de portée de la grande majorité des PME burkinabè. Son interface en anglais par défaut et sa courbe d'apprentissage élevée constituent également des freins majeurs.

**Sage 100** est un ERP commercial reconnu en Afrique francophone. Il offre une gestion robuste de la comptabilité et du stock, mais son modèle de licence est coûteux, il n'offre aucun mode hors-ligne natif, et il ne propose aucune fonctionnalité d'analyse prédictive ou d'intelligence artificielle. Sa configuration pour gérer un dépôt central avec plusieurs boutiques est complexe et nécessite un paramétrage professionnel.

**Wave** et **Loyverse POS** sont des solutions de caisse simplifiées, gratuites ou peu coûteuses. Elles sont adaptées à un point de vente unique, mais ne gèrent ni la logistique de dépôt-boutiques, ni les transferts inter-sites, ni la tarification différenciée, ni aucune forme d'analyse de données avancée.

**Les solutions artisanales** (cahiers, fichiers Excel) restent les plus répandues. Elles offrent une flexibilité totale et un coût nul, mais au prix d'une absence totale de centralisation, de traçabilité et d'analyse.

### 1.3.2 Limites des solutions pour le contexte BF

Le tableau ci-dessous résume la comparaison multicritères des solutions analysées face aux besoins réels des quincailleries burkinabè.

**Tableau 1 : Comparaison des solutions existantes face aux besoins identifiés**

| Critère d'évaluation | Odoo | Sage 100 | Wave / Loyverse | Excel | GesCom-BF |
|---|---|---|---|---|---|
| Coût accessible pour une PME BF | ✗ | ✗ | ✓ | ✓ | ✓ |
| Gestion dépôt central + boutiques | ✓ (complexe) | ✓ (partiel) | ✗ | ✗ | **✓ natif** |
| Mode hors-ligne (coupures réseau) | ✗ | ✗ | ✓ (partiel) | ✓ | **✓ PWA** |
| Double tarification client/technicien | ✓ (config.) | ✓ (config.) | ✗ | Manuel | **✓ natif** |
| Remises encadrées avec traçabilité | ✓ (générique) | ✓ (générique) | ✗ | ✗ | **✓ natif** |
| Prévision de rupture de stock (IA) | ✗ | ✗ | ✗ | ✗ | **✓ Prophet** |
| Scoring crédit informel | ✗ | ✗ | ✗ | ✗ | **✓ RF + SHAP** |
| Détection d'anomalies (ventes) | ✗ | ✗ | ✗ | ✗ | **✓ Isolation Forest** |
| Contexte calendaire burkinabè | ✗ | ✗ | ✗ | ✗ | **✓ natif** |
| Architecture SaaS multi-tenant | ✓ (Odoo.sh, coûteux) | ✗ | ✓ (limité) | ✗ | **✓ conçu nativement** |

L'analyse révèle une **lacune de marché claire** : aucune solution existante ne combine à la fois l'accessibilité financière, le mode hors-ligne robuste, la gestion native dépôt/boutiques et les fonctionnalités d'intelligence artificielle contextualisées au marché burkinabè. Cette lacune justifie le développement d'une solution sur-mesure.

---

## 1.4 Solution proposée : GesCom-BF

### 1.4.1 Positionnement et valeur ajoutée

**GesCom-BF** (Gestion Commerciale Burkina Faso) est une application web SaaS de gestion commerciale et de stock, conçue spécifiquement pour les quincailleries et boutiques de pièces détachées du Burkina Faso. Elle répond directement aux six catégories de problèmes identifiées, avec une proposition de valeur articulée autour de quatre axes différenciateurs.

**Axe 1 — Gestion multi-sites native.** L'application est conçue dès sa conception pour gérer un dépôt central et plusieurs boutiques, avec un suivi des stocks en temps réel, des transferts traçables et des rapports consolidés ou par site.

**Axe 2 — Mode hors-ligne robuste.** Grâce à une architecture Progressive Web App (PWA), les vendeurs peuvent continuer à enregistrer les ventes même sans connexion internet. Les données sont stockées localement dans le navigateur (IndexedDB) et synchronisées automatiquement dès le retour du réseau.

**Axe 3 — Intelligence artificielle contextualisée.** Le module analytique intègre sept composants d'aide à la décision, adaptés aux réalités du marché burkinabè : prévision de demande tenant compte des jours fériés locaux (Tabaski, Aïd el-Fitr, 11 décembre…), scoring du crédit informel, détection d'anomalies sur les ventes et les remises, segmentation des clients, et indicateurs spécifiques au contexte africain (stress de trésorerie, saison des pluies, weekend boost).

**Axe 4 — Architecture SaaS extensible.** La solution est conçue pour être exploitée comme un service à plusieurs entreprises clientes (multi-tenant), chaque tenant bénéficiant d'une isolation totale de ses données. Cette architecture permet une commercialisation à moindre coût et une maintenance centralisée.

### 1.4.2 Périmètre fonctionnel

**Inclus dans le périmètre du projet :**

- Gestion des utilisateurs et des rôles (Administrateur, Magasinier, Vendeur)
- Gestion des produits, catégories, marques et fournisseurs
- Gestion des stocks au dépôt central et dans chaque boutique
- Gestion des transferts inter-sites avec validation et traçabilité
- Gestion des ventes avec double tarification et remises encadrées
- Vente à crédit avec suivi du solde client
- Gestion des inventaires physiques et ajustement du stock théorique
- Mode hors-ligne (PWA) pour la vente en boutique
- Tableau de bord multi-sites et rapports exportables en PDF
- Module d'intelligence artificielle (7 composants, cf. Chapitre 4)
- Audit log des actions sensibles
- Architecture SaaS multi-tenant (isolation logique par `tenant_id`)

**Hors périmètre (perspectives V2) :**

- Application mobile native Android / iOS
- Intégration paiement Mobile Money (Orange Money, Moov Money)
- Module de comptabilité générale et fiscalité complète
- Marketplace B2B entre quincailleries
- Multi-tenant avec isolation par schéma de base de données (PostgreSQL)

---

## 1.5 Objectifs SMART

Les objectifs du projet ont été définis selon le cadre SMART (Spécifique, Mesurable, Atteignable, Réaliste, Temporel).

**Tableau 2 : Objectifs SMART de GesCom-BF**

| # | Objectif | Indicateur de mesure | Cible |
|---|---|---|---|
| O1 | Centraliser la gestion des stocks dépôt + boutiques | 100 % des mouvements de stock tracés en base de données | Sprint 1–3 |
| O2 | Réduire le temps de saisie d'une vente | Durée de saisie d'une vente complète | < 30 secondes |
| O3 | Anticiper les ruptures de stock par IA | Erreur relative de prévision (RMSE / demande moyenne) | < 15 % |
| O4 | Garantir la continuité de service hors-ligne | % des fonctions de vente disponibles sans réseau | 100 %, sync < 5 min |
| O5 | Sécuriser l'accès aux données | Accès non autorisés lors des tests de sécurité | 0 |
| O6 | Détecter les anomalies de gestion | Taux de faux positifs sur jeu de test | < 10 % |
| O7 | Fournir un tableau de bord décisionnel réactif | Temps de rafraîchissement du dashboard | < 2 secondes |
| O8 | Couvrir les fonctions ML par des tests automatisés | Tests unitaires pytest passants | 93 / 93 ✅ |

---

## 1.6 Gestion du projet

### Méthodologie

La gestion du projet a reposé sur une méthode **Scrum adaptée au contexte académique individuel**, avec des sprints de deux semaines. Les rôles ont été distribués comme suit : le Product Owner est représenté par le directeur de mémoire (vision et validation des livrables), le Scrum Master et Développeur est l'étudiant lui-même. Le suivi a été réalisé via un tableau Kanban (GitHub Projects) et un journal de bord quotidien.

L'approche en sprints a permis de gérer la complexité croissante du projet en livrant des fonctionnalités opérationnelles de façon itérative, et de valider chaque module avant d'en entamer un nouveau. La modélisation UML a été réalisée en amont (Sprint 0) selon le processus **2TUP**, garantissant que les décisions d'architecture reposent sur une analyse fonctionnelle complète.

### Organisation en épics

Le backlog du projet a été organisé en 11 épics couvrant l'ensemble des fonctionnalités.

| Épic | Description | Sprints |
|---|---|---|
| E1 | Socle technique et authentification (JWT, RBAC) | 1–2 |
| E2 | Catalogue produits et référentiels | 2–3 |
| E3 | Stock, dépôt et transferts | 3–4 |
| E4 | Ventes — cœur métier (double tarif, remises, crédit) | 4–5 |
| E5 | Mode hors-ligne PWA (Service Worker, IndexedDB, sync) | 6–7 |
| E6 | Inventaires physiques | 5–6 |
| E7 | Rapports et tableau de bord | 9–10 |
| E8 | Module analytique et IA (Prophet, RF+SHAP, Apriori…) | 8–11 |
| E9 | Audit et sécurité avancée | 2 + continu |
| E10 | Architecture SaaS multi-tenant | 1 + 11 |
| E11 | Tests automatisés, CI/CD et documentation finale | Continu + 12 |

### Planning général

Le projet s'est déroulé sur **24 semaines (12 sprints de 2 semaines)**, de janvier à juin 2026. La figure ci-dessous illustre la répartition temporelle des sprints.

**Figure 3 : Planning du projet — Diagramme de Gantt** *(à insérer)*

| Sprint | Période | Objectif principal | Livrable clé |
|---|---|---|---|
| 0 | Semaine 1 | Cadrage et modélisation | MCD/MLD, architecture, environnement |
| 1–2 | Sem. 2–5 | Authentification, RBAC, multi-tenant | API auth fonctionnelle, isolation tenant |
| 3–4 | Sem. 6–9 | Produits, stock, transferts | CRUD complet, contraintes métier |
| 5–6 | Sem. 10–13 | Ventes et inventaires | Module vente opérationnel |
| 7 | Sem. 14–15 | Mode hors-ligne PWA | Vente offline + synchronisation |
| 8–9 | Sem. 16–19 | Pipeline ETL + modules ML (Prophet, RF, RFM) | 3 modules IA opérationnels |
| 10–11 | Sem. 20–23 | Dashboard BI + modules ML complémentaires | 7 modules IA opérationnels |
| 12 | Sem. 24 | Tests (93 pytest), CI/CD, documentation | Pipeline CI/CD actif, 93/93 tests ✅ |

### Estimation du coût de réalisation

Bien que ce projet soit réalisé dans un cadre académique, il est utile d'en estimer le coût réel, notamment pour illustrer la valeur économique du travail accompli et envisager une commercialisation.

**Tableau 18 : Estimation du coût de réalisation**

| Poste | Détail | Coût estimé (FCFA) |
|---|---|---|
| Développement backend | 12 sprints × 2 semaines × 40h/sem × 5 000 FCFA/h | 4 800 000 |
| Développement frontend | Inclus dans l'effort de développement global | — |
| Infrastructure (PythonAnywhere plan Developer) | 5 000 FCFA/mois × 6 mois | 30 000 |
| Outils et licences | GitHub, domaine, outils (essentiellement gratuits/open-source) | 10 000 |
| **Total estimé** | | **≈ 4 840 000 FCFA** |

*Note : le coût de développement est calculé sur la base d'un tarif junior de marché au Burkina Faso. Dans un cadre académique, ce coût est couvert par l'effort de l'étudiant.*

**Modèle économique SaaS envisagé (V2) :** abonnement mensuel par entreprise entre 15 000 et 50 000 FCFA selon le nombre de boutiques, avec un objectif de seuil de rentabilité à partir de 15–20 clients.

---

## Conclusion du chapitre

Ce premier chapitre a permis de poser les fondations du projet. L'analyse du secteur de la quincaillerie au Burkina Faso révèle un besoin réel et non adressé : une solution informatique de gestion commerciale accessible, robuste face aux aléas de connectivité, et capable de transformer les données de vente en aide à la décision. L'étude comparative des solutions existantes confirme qu'aucune d'entre elles ne répond à l'ensemble de ces besoins dans le contexte burkinabè.

GesCom-BF se positionne comme une réponse directe à cette lacune : une application web SaaS conçue sur-mesure, avec un mode hors-ligne natif, une gestion multi-sites intégrée et un module d'intelligence artificielle contextualisé. Les objectifs SMART fixés et l'organisation en sprints Scrum ont guidé le développement de façon rigoureuse sur une durée de six mois.

Le chapitre suivant présente l'analyse détaillée des besoins du système et sa modélisation UML complète.

---

*— Fin du Chapitre 1 —*
