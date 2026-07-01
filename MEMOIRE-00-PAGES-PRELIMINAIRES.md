# MEMOIRE DE FIN DE CYCLE — GesCom-BF
<!-- Fichier : MEMOIRE-00-PAGES-PRELIMINAIRES.md -->
<!-- Remplacer tous les champs entre [ ] avant impression -->

---

# PAGE DE GARDE

<div align="center">

**UNIVERSITÉ VIRTUELLE DU BURKINA FASO (UVBF)**

*Département des Sciences et Technologies du Numérique*

---

**MÉMOIRE DE FIN DE CYCLE**

*Présenté en vue de l'obtention du diplôme de*

**[Licence Professionnelle / Master / BTS — à préciser]**

*en Génie Logiciel / Analyse de Données*

---

**TITRE DU MÉMOIRE :**

# CONCEPTION ET DÉVELOPPEMENT D'UNE APPLICATION WEB SAAS DE GESTION COMMERCIALE AVEC MODULE D'INTELLIGENCE ARTIFICIELLE

*Cas des quincailleries et boutiques de pièces détachées du Burkina Faso*

---

**Présenté et soutenu par :**

**[VOTRE NOM COMPLET]**

*Sous la direction de :*

**[Nom du Maître de suivi], [Grade/Titre]**

---

*Membres du jury :*

| Qualité | Nom |
|---|---|
| Président | [Nom et grade] |
| Directeur de mémoire | [Nom et grade] |
| Examinateur | [Nom et grade] |

---

**Année académique : 2025-2026**

*Soutenu le : [Date de soutenance] à [Lieu]*

</div>

---

# DÉDICACE

<div align="center">
<br><br>

*À ma famille,*

*pour son soutien indéfectible et ses sacrifices tout au long de ce parcours.*

<br>

*À tous ceux qui croient que la technologie peut être un levier de développement*
*pour l'Afrique et pour le Burkina Faso en particulier.*

<br><br>
</div>

---

# REMERCIEMENTS

La réalisation de ce mémoire n'aurait pas été possible sans le concours de nombreuses personnes à qui je tiens à exprimer ma profonde gratitude.

Je remercie en premier lieu **[Nom du Maître de suivi]**, mon directeur de mémoire, pour sa disponibilité, ses orientations précieuses et ses remarques constructives tout au long de l'élaboration de ce travail.

Mes remerciements vont également à l'ensemble du **corps enseignant de l'Université Virtuelle du Burkina Faso (UVBF)** pour la qualité de la formation dispensée et pour les connaissances transmises qui ont rendu ce projet possible.

Je remercie les **membres du jury** qui ont accepté d'évaluer ce travail et d'y consacrer leur temps et leur expertise.

Ma reconnaissance va aussi à **[Nom de la structure d'accueil / entreprise, si applicable]** pour m'avoir permis de confronter mes connaissances théoriques à des problématiques réelles du terrain burkinabè.

Enfin, je remercie chaleureusement ma **famille et mes proches** pour leur soutien moral constant, leur patience et leurs encouragements sans lesquels ce mémoire n'aurait pu voir le jour.

---

# RÉSUMÉ

La gestion commerciale des petites et moyennes entreprises au Burkina Faso, en particulier dans le secteur de la quincaillerie et des pièces détachées, repose encore largement sur des méthodes manuelles — cahiers de stock, fichiers Excel non centralisés, remises accordées sans traçabilité. Cette situation engendre des ruptures de stock non anticipées, des erreurs de tarification et une incapacité à piloter l'activité sur plusieurs points de vente.

Ce mémoire présente la conception et le développement de **GesCom-BF**, une application web SaaS (Software as a Service) de gestion commerciale destinée à répondre à ces problèmes. La solution couvre l'ensemble du cycle de vie d'une vente, de la réception fournisseur au tableau de bord décisionnel, en passant par la gestion des stocks multi-sites, les transferts inter-boutiques et la vente au comptoir avec double tarification. Une fonctionnalité hors-ligne (Progressive Web App) garantit la continuité de service même en cas de coupure internet.

La valeur ajoutée principale du système réside dans un **module d'intelligence artificielle et d'analyse de données** composé de sept composants : prévision de demande par séries temporelles (Prophet), scoring crédit des clients (Random Forest + SHAP), détection d'anomalies (Isolation Forest), segmentation RFM (K-Means), analyse des associations de produits (Apriori), classification ABC/XYZ et estimation de la probabilité de churn. Ces modules sont contextualisés pour le marché burkinabè (jours fériés locaux, indicateurs de trésorerie, crédit informel).

L'application est développée avec **Flask 3.0.3** (Python) pour le backend et **React 18 / TypeScript** pour le frontend, déployée sur PythonAnywhere avec une base de données MySQL. La qualité est assurée par 93 tests unitaires automatisés (pytest) intégrés dans un pipeline CI/CD GitHub Actions.

**Mots-clés :** Gestion commerciale, SaaS, Intelligence artificielle, Prévision de demande, Scoring crédit, Machine Learning, Burkina Faso, Flask, React, PWA.

---

# ABSTRACT

Commercial management of small and medium-sized enterprises in Burkina Faso, particularly in the hardware and spare parts sector, still largely relies on manual methods — stock registers, non-centralized Excel files, discounts granted without traceability. This situation leads to unanticipated stockouts, pricing errors, and an inability to monitor activity across multiple points of sale.

This dissertation presents the design and development of **GesCom-BF**, a SaaS (Software as a Service) web application for commercial management aimed at addressing these challenges. The solution covers the entire sales lifecycle, from supplier reception to decision-making dashboards, including multi-site inventory management, inter-branch transfers, and counter sales with dual pricing. An offline feature (Progressive Web App) ensures service continuity even during internet outages.

The system's main value-added lies in an **artificial intelligence and data analytics module** comprising seven components: time-series demand forecasting (Prophet), customer credit scoring (Random Forest + SHAP), anomaly detection (Isolation Forest), RFM segmentation (K-Means), product association analysis (Apriori), ABC/XYZ classification, and churn probability estimation. These modules are contextualized for the Burkinabe market (local public holidays, treasury indicators, informal credit).

The application is built with **Flask 3.0.3** (Python) for the backend and **React 18 / TypeScript** for the frontend, deployed on PythonAnywhere with a MySQL database. Quality is ensured by 93 automated unit tests (pytest) integrated into a GitHub Actions CI/CD pipeline.

**Keywords:** Commercial management, SaaS, Artificial intelligence, Demand forecasting, Credit scoring, Machine Learning, Burkina Faso, Flask, React, PWA.

---

# LISTE DES SIGLES ET ABRÉVIATIONS

| Sigle / Abréviation | Signification |
|---|---|
| **API** | Application Programming Interface (Interface de Programmation Applicative) |
| **BI** | Business Intelligence (Intelligence d'Affaires) |
| **BTP** | Bâtiment, Travaux Publics |
| **CI/CD** | Continuous Integration / Continuous Deployment (Intégration et Déploiement Continus) |
| **CLV** | Customer Lifetime Value (Valeur Vie Client) |
| **CRUD** | Create, Read, Update, Delete |
| **CSS** | Cascading Style Sheets |
| **DB** | Database (Base de données) |
| **ERP** | Enterprise Resource Planning (Progiciel de Gestion Intégré) |
| **HTML** | HyperText Markup Language |
| **HTTP / HTTPS** | HyperText Transfer Protocol / Secure |
| **IA** | Intelligence Artificielle |
| **IndexedDB** | API de stockage local côté navigateur (offline) |
| **JSON** | JavaScript Object Notation |
| **JWT** | JSON Web Token |
| **KPI** | Key Performance Indicator (Indicateur Clé de Performance) |
| **MCD** | Modèle Conceptuel de Données |
| **MLD** | Modèle Logique de Données |
| **ML** | Machine Learning (Apprentissage Automatique) |
| **MLflow** | Plateforme open-source de gestion du cycle de vie des modèles ML |
| **MPD** | Modèle Physique de Données |
| **MVP** | Minimum Viable Product (Produit Minimum Viable) |
| **ORM** | Object-Relational Mapper |
| **PME** | Petite et Moyenne Entreprise |
| **PWA** | Progressive Web App |
| **RBAC** | Role-Based Access Control (Contrôle d'Accès Basé sur les Rôles) |
| **REST** | Representational State Transfer |
| **RF** | Requirement Functional (Exigence Fonctionnelle) |
| **RFM** | Récence, Fréquence, Montant (modèle de segmentation client) |
| **RG** | Règle de Gestion |
| **RNF** | Requirement Non-Functional (Exigence Non Fonctionnelle) |
| **SaaS** | Software as a Service (Logiciel en tant que Service) |
| **SHAP** | SHapley Additive exPlanations (explicabilité ML) |
| **SQL** | Structured Query Language |
| **TLS** | Transport Layer Security |
| **UML** | Unified Modeling Language (Langage de Modélisation Unifié) |
| **UVBF** | Université Virtuelle du Burkina Faso |
| **VPS** | Virtual Private Server (Serveur Privé Virtuel) |

---

# LISTE DES FIGURES

| N° | Titre de la figure | Page |
|---|---|---|
| Figure 1 | Organigramme du secteur quincaillerie — dépôt + boutiques | [x] |
| Figure 2 | Comparaison des solutions ERP existantes | [x] |
| Figure 3 | Planning du projet — diagramme de Gantt | [x] |
| Figure 4 | Diagramme de cas d'utilisation global | [x] |
| Figure 5 | Description détaillée — CU "Effectuer une vente" | [x] |
| Figure 6 | Description détaillée — CU "Entraîner un modèle ML" | [x] |
| Figure 7 | Diagramme de classes global | [x] |
| Figure 8 | Diagramme de séquence — processus de vente | [x] |
| Figure 9 | Diagramme de séquence — transfert inter-sites | [x] |
| Figure 10 | Diagramme de déploiement (PythonAnywhere) | [x] |
| Figure 11 | Modèle Conceptuel de Données (MCD) | [x] |
| Figure 12 | Architecture globale 3-tiers de GesCom-BF | [x] |
| Figure 13 | Architecture de déploiement PythonAnywhere | [x] |
| Figure 14 | Schéma du mode hors-ligne PWA (Service Worker) | [x] |
| Figure 15 | Pipeline d'entraînement ML nocturne (cron) | [x] |
| Figure 16 | Architecture de la prévision de demande (Prophet → sklearn → naive) | [x] |
| Figure 17 | Exemple de graphique SHAP — scoring crédit | [x] |
| Figure 18 | Exemple de segmentation RFM (nuage de points K-Means) | [x] |
| Figure 19 | Exemple de règles d'association Market Basket (support/lift) | [x] |
| Figure 20 | Pipeline CI/CD GitHub Actions | [x] |
| Figure 21 | Capture — Tableau de bord principal | [x] |
| Figure 22 | Capture — Module Ventes | [x] |
| Figure 23 | Capture — Module Stocks / Transferts | [x] |
| Figure 24 | Capture — Dashboard analytique IA | [x] |
| Figure 25 | Capture — Segmentation RFM clients | [x] |
| Figure 26 | Capture — Prévision de demande (graphique Prophet) | [x] |

---

# LISTE DES TABLEAUX

| N° | Titre du tableau | Page |
|---|---|---|
| Tableau 1 | Comparaison des solutions ERP existantes | [x] |
| Tableau 2 | Objectifs SMART du projet | [x] |
| Tableau 3 | Rôles et permissions (RBAC) | [x] |
| Tableau 4 | Exigences fonctionnelles principales (RF) | [x] |
| Tableau 5 | Exigences non fonctionnelles (RNF) | [x] |
| Tableau 6 | Description du CU "Effectuer une vente" | [x] |
| Tableau 7 | Dictionnaire des données — table `sales` | [x] |
| Tableau 8 | Dictionnaire des données — table `products` | [x] |
| Tableau 9 | Dictionnaire des données — table `customers` | [x] |
| Tableau 10 | Règles de gestion clés (RG) | [x] |
| Tableau 11 | Choix technologiques et justifications | [x] |
| Tableau 12 | Classification des modules analytiques (ML / BI / heuristique) | [x] |
| Tableau 13 | Variables du modèle de scoring crédit | [x] |
| Tableau 14 | Paramètres de l'algorithme Apriori | [x] |
| Tableau 15 | Résultats des tests unitaires pytest (93 tests) | [x] |
| Tableau 16 | Couverture fonctionnelle — état d'avancement | [x] |
| Tableau 17 | Environnement matériel et logiciel de développement | [x] |
| Tableau 18 | Estimation du coût de réalisation | [x] |

---

# TABLE DES MATIÈRES

PAGE DE GARDE ............................................................................................................. i  
DÉDICACE ....................................................................................................................... ii  
REMERCIEMENTS ......................................................................................................... iii  
RÉSUMÉ .......................................................................................................................... iv  
ABSTRACT ...................................................................................................................... v  
LISTE DES SIGLES ET ABRÉVIATIONS ..................................................................... vi  
LISTE DES FIGURES ..................................................................................................... viii  
LISTE DES TABLEAUX ................................................................................................. ix  
TABLE DES MATIÈRES ................................................................................................ x  
INTRODUCTION GÉNÉRALE ....................................................................................... 1  

**CHAPITRE 1 : PRÉSENTATION DU CONTEXTE ET ÉTUDE DE L'EXISTANT** ........... 4  
Introduction ...................................................................................................................... 4  
1.1 Présentation de l'UVBF ............................................................................................. 4  
1.2 Secteur cible : la quincaillerie au Burkina Faso ........................................................ 5  
&nbsp;&nbsp;&nbsp;&nbsp;1.2.1 État des lieux du secteur ........................................................................ 5  
&nbsp;&nbsp;&nbsp;&nbsp;1.2.2 Problèmes identifiés ............................................................................... 6  
1.3 Analyse des solutions existantes ................................................................................ 7  
&nbsp;&nbsp;&nbsp;&nbsp;1.3.1 Solutions ERP génériques (Odoo, Sage, Wave) ................................. 7  
&nbsp;&nbsp;&nbsp;&nbsp;1.3.2 Limites pour le contexte BF ................................................................... 8  
1.4 Solution proposée : GesCom-BF ............................................................................... 9  
&nbsp;&nbsp;&nbsp;&nbsp;1.4.1 Positionnement et valeur ajoutée .......................................................... 9  
&nbsp;&nbsp;&nbsp;&nbsp;1.4.2 Périmètre fonctionnel ............................................................................. 10  
1.5 Objectifs SMART ...................................................................................................... 11  
1.6 Gestion du projet ...................................................................................................... 12  
Conclusion du chapitre .................................................................................................... 13  

**CHAPITRE 2 : ANALYSE ET MODÉLISATION DU SYSTÈME** .................................... 14  
Introduction ...................................................................................................................... 14  
2.1 Acteurs du système et rôles ....................................................................................... 14  
2.2 Besoins fonctionnels ................................................................................................. 15  
2.3 Besoins non fonctionnels .......................................................................................... 17  
2.4 Modélisation UML .................................................................................................... 18  
&nbsp;&nbsp;&nbsp;&nbsp;2.4.1 Diagramme de cas d'utilisation global .............................................. 18  
&nbsp;&nbsp;&nbsp;&nbsp;2.4.2 Description détaillée de cas d'utilisation clés ................................. 20  
&nbsp;&nbsp;&nbsp;&nbsp;2.4.3 Diagramme de classes ......................................................................... 22  
&nbsp;&nbsp;&nbsp;&nbsp;2.4.4 Diagrammes de séquence .................................................................... 24  
&nbsp;&nbsp;&nbsp;&nbsp;2.4.5 Diagramme de déploiement ................................................................ 26  
2.5 Modélisation des données ......................................................................................... 27  
&nbsp;&nbsp;&nbsp;&nbsp;2.5.1 Modèle Conceptuel de Données (MCD) ......................................... 27  
&nbsp;&nbsp;&nbsp;&nbsp;2.5.2 Modèle Logique de Données (MLD) ................................................ 28  
&nbsp;&nbsp;&nbsp;&nbsp;2.5.3 Dictionnaire des données .................................................................... 29  
2.6 Règles de gestion clés ............................................................................................... 31  
Conclusion du chapitre .................................................................................................... 32  

**CHAPITRE 3 : ARCHITECTURE TECHNIQUE ET RÉALISATION** .............................. 33  
Introduction ...................................................................................................................... 33  
3.1 Architecture globale (3-tiers, API-first) ................................................................... 33  
3.2 Choix technologiques justifiés .................................................................................. 34  
&nbsp;&nbsp;&nbsp;&nbsp;3.2.1 Backend : Flask 3.0.3 + Blueprints + SQLAlchemy ...................... 34  
&nbsp;&nbsp;&nbsp;&nbsp;3.2.2 Frontend : React 18 + TypeScript + Vite (PWA) ........................... 36  
&nbsp;&nbsp;&nbsp;&nbsp;3.2.3 Base de données : MySQL 8.0 ......................................................... 37  
3.3 Sécurité applicative .................................................................................................. 38  
&nbsp;&nbsp;&nbsp;&nbsp;3.3.1 RBAC et authentification JWT .......................................................... 38  
&nbsp;&nbsp;&nbsp;&nbsp;3.3.2 Rate limiting (Flask-Limiter) .............................................................. 39  
&nbsp;&nbsp;&nbsp;&nbsp;3.3.3 Audit log et traçabilité .......................................................................... 40  
3.4 Mode hors-ligne (PWA) ........................................................................................... 41  
3.5 API REST — principaux endpoints .......................................................................... 42  
3.6 Architecture SaaS multi-tenant ................................................................................ 44  
&nbsp;&nbsp;&nbsp;&nbsp;3.6.1 Modèle shared database / tenant_id ................................................. 44  
&nbsp;&nbsp;&nbsp;&nbsp;3.6.2 État actuel (mono-tenant) et cible V2 ............................................... 45  
3.7 Présentation des interfaces ....................................................................................... 46  
&nbsp;&nbsp;&nbsp;&nbsp;3.7.1 Tableau de bord principal .................................................................... 46  
&nbsp;&nbsp;&nbsp;&nbsp;3.7.2 Module Ventes ...................................................................................... 47  
&nbsp;&nbsp;&nbsp;&nbsp;3.7.3 Module Stocks / Transferts .................................................................. 48  
&nbsp;&nbsp;&nbsp;&nbsp;3.7.4 Module Analytique (aperçu) ................................................................ 49  
Conclusion du chapitre .................................................................................................... 50  

**CHAPITRE 4 : MODULE D'INTELLIGENCE ARTIFICIELLE ET D'ANALYSE DE DONNÉES** ... 51  
Introduction ...................................................................................................................... 51  
4.1 Vue d'ensemble du module analytique ..................................................................... 51  
&nbsp;&nbsp;&nbsp;&nbsp;4.1.1 Classification honnête des techniques ............................................... 51  
&nbsp;&nbsp;&nbsp;&nbsp;4.1.2 Pipeline d'entraînement nocturne ....................................................... 52  
&nbsp;&nbsp;&nbsp;&nbsp;4.1.3 Gestion des modèles (MLflow) ........................................................... 53  
4.2 Prévision de demande — Prophet ............................................................................. 54  
&nbsp;&nbsp;&nbsp;&nbsp;4.2.1 Justification du choix ............................................................................ 54  
&nbsp;&nbsp;&nbsp;&nbsp;4.2.2 Architecture de la solution .................................................................... 55  
&nbsp;&nbsp;&nbsp;&nbsp;4.2.3 Indicateur de fiabilité data_confidence ................................................ 56  
4.3 Scoring crédit — Random Forest + SHAP ............................................................... 57  
&nbsp;&nbsp;&nbsp;&nbsp;4.3.1 Variables retenues et justification ...................................................... 57  
&nbsp;&nbsp;&nbsp;&nbsp;4.3.2 Modèle RF + validation croisée .......................................................... 58  
&nbsp;&nbsp;&nbsp;&nbsp;4.3.3 Explicabilité SHAP ............................................................................... 59  
4.4 Détection d'anomalies — Isolation Forest ................................................................ 60  
4.5 Segmentation clients RFM — K-Means ................................................................... 61  
&nbsp;&nbsp;&nbsp;&nbsp;4.5.1 Dimensions Récence / Fréquence / Montant ..................................... 61  
&nbsp;&nbsp;&nbsp;&nbsp;4.5.2 Détermination automatique de K ........................................................ 62  
4.6 Market Basket Analysis — Apriori ........................................................................... 63  
4.7 Modules complémentaires ........................................................................................ 64  
&nbsp;&nbsp;&nbsp;&nbsp;4.7.1 Classification ABC/XYZ (analytique BI) ........................................... 64  
&nbsp;&nbsp;&nbsp;&nbsp;4.7.2 Probabilité de churn (heuristique statistique) .................................... 65  
&nbsp;&nbsp;&nbsp;&nbsp;4.7.3 Élasticité prix ........................................................................................ 66  
&nbsp;&nbsp;&nbsp;&nbsp;4.7.4 Contexte africain BF ............................................................................ 67  
Conclusion du chapitre .................................................................................................... 68  

**CHAPITRE 5 : TESTS, DÉPLOIEMENT ET RÉSULTATS** ............................................ 69  
Introduction ...................................................................................................................... 69  
5.1 Stratégie de tests ....................................................................................................... 69  
&nbsp;&nbsp;&nbsp;&nbsp;5.1.1 Tests unitaires ML (pytest — 93 tests) .............................................. 69  
&nbsp;&nbsp;&nbsp;&nbsp;5.1.2 Tests d'intégration API ......................................................................... 71  
&nbsp;&nbsp;&nbsp;&nbsp;5.1.3 Tests de sécurité ................................................................................... 72  
5.2 Pipeline CI/CD (GitHub Actions) ............................................................................. 73  
5.3 Déploiement PythonAnywhere ................................................................................. 74  
&nbsp;&nbsp;&nbsp;&nbsp;5.3.1 Infrastructure retenue et justification ................................................. 74  
&nbsp;&nbsp;&nbsp;&nbsp;5.3.2 Configuration uWSGI / MySQL .......................................................... 75  
&nbsp;&nbsp;&nbsp;&nbsp;5.3.3 Contraintes et adaptations ................................................................... 76  
5.4 Monitoring et observabilité ...................................................................................... 77  
5.5 Résultats et métriques .............................................................................................. 78  
5.6 Difficultés rencontrées et solutions .......................................................................... 80  
Conclusion du chapitre .................................................................................................... 82  

**CONCLUSION GÉNÉRALE ET PERSPECTIVES** .......................................................... 83  
BIBLIOGRAPHIE ............................................................................................................. 86  
ANNEXES ........................................................................................................................ 89  

---

# INTRODUCTION GÉNÉRALE

## Contexte général

L'essor des technologies numériques transforme profondément les pratiques commerciales à travers le monde. En Afrique subsaharienne, et au Burkina Faso en particulier, cette transformation numérique avance à un rythme contrasté : si les grandes entreprises adoptent progressivement des solutions informatiques de gestion, les petites et moyennes entreprises (PME) du secteur commercial restent largement à l'écart de cette révolution.

Le secteur de la quincaillerie et des pièces détachées — pièces automobile, pièces motocycle, matériaux de construction et équipements BTP — illustre particulièrement bien cette réalité. Ces commerces, organisés le plus souvent autour d'un dépôt central et d'un ou plusieurs points de vente en boutique, font face à des défis opérationnels chroniques : stocks suivis sur des cahiers physiques ou des fichiers Excel non partagés, prix pratiqués de façon variable selon les clients (simples particuliers versus techniciens professionnels), remises accordées à l'oral sans traçabilité, et impossibilité totale d'anticiper les ruptures de stock ou d'analyser les performances sur données réelles.

C'est dans ce contexte que s'inscrit le présent mémoire, qui porte sur la conception et le développement d'une solution logicielle adaptée à ces réalités locales.

## Problématique

Les solutions informatiques de gestion existantes présentent toutes des limites significatives face aux besoins des quincailleries burkinabè. Les progiciels de gestion intégrés (ERP) généralistes comme Odoo ou Sage sont puissants, mais leur coût de licence, leur complexité d'installation et leur dépendance à une connexion internet stable les rendent inadaptés à la grande majorité des PME commerciales du pays. Les solutions artisanales à base d'Excel, quant à elles, ne permettent aucune centralisation des données entre plusieurs boutiques, aucune traçabilité fiable et aucune analyse prédictive.

Cette situation soulève une problématique centrale :

> **Comment doter les quincailleries et boutiques de pièces détachées du Burkina Faso d'un outil de gestion commerciale centralisé, fiable, accessible même en cas de coupure internet, et capable de transformer leurs données de vente en aide à la décision intelligente ?**

## Objectifs du mémoire

Ce mémoire vise à répondre à cette problématique en poursuivant les objectifs suivants.

**Objectif principal :** Concevoir et développer une application web SaaS de gestion commerciale et de stock, nommée **GesCom-BF**, adaptée aux contraintes opérationnelles et de connectivité des PME commerciales du Burkina Faso.

**Objectifs spécifiques :**

- Centraliser la gestion des stocks d'un dépôt central et de plusieurs boutiques en temps réel
- Sécuriser les accès par un système de rôles (Administrateur, Magasinier, Vendeur) avec authentification JWT
- Garantir la continuité de service hors-ligne grâce à une architecture Progressive Web App (PWA)
- Implémenter un module d'intelligence artificielle et d'analyse de données comprenant sept composants : prévision de demande (Prophet), scoring crédit (Random Forest + SHAP), détection d'anomalies (Isolation Forest), segmentation clients RFM (K-Means), analyse des associations de produits (Apriori), classification ABC/XYZ et estimation du churn
- Contextualiser les analyses au marché burkinabè (jours fériés locaux, crédit informel, indicateurs de trésorerie)
- Assurer la qualité du code par des tests automatisés (93 tests unitaires pytest) et un pipeline CI/CD

## Méthodologie adoptée

La réalisation de ce projet s'est appuyée sur une démarche méthodologique en deux volets complémentaires.

**Pour la modélisation et la conception**, nous avons adopté le processus **2TUP (Two Tracks Unified Process)**, une adaptation du Processus Unifié centrée sur la séparation entre la branche fonctionnelle (analyse des besoins, modélisation UML) et la branche technique (architecture, choix technologiques). Cette approche permet de traiter en parallèle les exigences métier et les contraintes techniques, avant de les réconcilier lors de la phase de conception détaillée. Le formalisme **UML 2.5** a été utilisé pour tous les diagrammes (cas d'utilisation, classes, séquences, déploiement).

**Pour le développement et l'implémentation**, nous avons adopté une organisation agile par **sprints de deux semaines**, permettant de livrer des fonctionnalités opérationnelles de façon itérative et de valider chaque module avant de passer au suivant. Cette approche a facilité la gestion de la complexité du projet, notamment pour l'intégration progressive des modules d'intelligence artificielle.

La combinaison de ces deux approches — rigueur de la modélisation 2TUP pour la conception, agilité des sprints pour l'implémentation — s'est révélée particulièrement adaptée à un projet de cette envergure réalisé en contexte académique individuel.

## Plan du mémoire

Ce mémoire est structuré en cinq chapitres, organisés de façon à accompagner le lecteur depuis la compréhension du contexte jusqu'aux résultats concrets de l'implémentation.

Le **premier chapitre** présente le contexte général du projet : le secteur de la quincaillerie au Burkina Faso, l'analyse des solutions existantes et leurs limites, ainsi que la définition des objectifs et du périmètre de GesCom-BF.

Le **deuxième chapitre** traite l'analyse et la modélisation du système : identification des acteurs et des besoins, formalisation des exigences fonctionnelles et non fonctionnelles, et production de l'ensemble des diagrammes UML (cas d'utilisation, classes, séquences, déploiement) ainsi que de la modélisation des données (MCD, MLD, dictionnaire).

Le **troisième chapitre** décrit l'architecture technique de la solution et sa réalisation : choix technologiques justifiés, sécurité applicative, mode hors-ligne PWA, API REST, architecture SaaS multi-tenant et présentation des interfaces utilisateur.

Le **quatrième chapitre**, qui constitue la contribution originale principale de ce mémoire, est entièrement consacré au module d'intelligence artificielle et d'analyse de données : présentation de chaque composant, justification des algorithmes retenus, description technique et résultats obtenus.

Le **cinquième chapitre** couvre la stratégie de tests, le pipeline CI/CD, le déploiement en production sur PythonAnywhere, le monitoring et les résultats mesurables du projet, ainsi que les difficultés rencontrées et les solutions apportées.

Le mémoire se clôt par une conclusion générale qui dresse le bilan des objectifs atteints, reconnaît honnêtement les limites du travail réalisé et trace les perspectives d'évolution du système vers une version V2 commercialisable.

---

*— Fin des pages préliminaires et de l'introduction générale —*
