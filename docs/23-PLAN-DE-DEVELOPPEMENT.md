# 23. Plan de développement — Méthodologie Agile

## 23.1 Méthodologie retenue

**Scrum**, adapté à un projet académique en solo/petite équipe :

- Sprints de **2 semaines**.
- Rôles : Product Owner (encadreur académique / vision projet), Scrum Master + Développeur (étudiant), Parties prenantes (jury, utilisateurs pilotes).
- Cérémonies : Sprint Planning (début de sprint), Daily (auto-suivi journalier via journal de bord), Sprint Review (démonstration), Sprint Retrospective (amélioration continue).
- Outils : backlog géré dans un board Kanban (GitHub Projects / Trello), code versionné Git (GitFlow simplifié : `main`, `develop`, `feature/*`).

## 23.2 Backlog produit — Epics

| Epic | RF associées | Sprints |
|---|---|---|
| E1 — Socle technique & Authentification | RF-01 à RF-05, RNF-07 à RNF-09 | Sprint 1-2 |
| E2 — Catalogue & Référentiels | RF-06 à RF-10 | Sprint 2-3 |
| E3 — Stock, Dépôt & Transferts | RF-11 à RF-14 | Sprint 3-4 |
| E4 — Ventes (cœur métier) | RF-15 à RF-19 | Sprint 4-5 |
| E5 — Mode Offline-First (PWA) | RF-20, RNF-10 | Sprint 6-7 |
| E6 — Inventaires | RF-21 à RF-23 | Sprint 5-6 |
| E7 — Rapports & Dashboard | RF-24, RF-29 | Sprint 9-10 |
| E8 — Module IA (prévisions, scoring, anomalies, ABC/XYZ) | RF-25 à RF-28 | Sprint 8-10 |
| E9 — Audit & Sécurité avancée | RF-30 à RF-32 | Sprint 2, continu |
| E10 — Multi-tenant SaaS | - | Sprint 1, 11 |
| E11 — Tests, CI/CD, Documentation finale | RNF-14, RNF-15 | Continu + Sprint 12 |

## 23.3 Planning des sprints (12 sprints = 24 semaines ≈ 6 mois)

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    title Planning Agile - GesCom-BF (12 sprints)
    section Cadrage
    Sprint 0 - Setup, MCD/MLD/MPD, archi : s0, 2026-01-05, 1w
    section Sprints
    Sprint 1 - Auth, multi-tenant, RBAC      : s1, after s0, 2w
    Sprint 2 - Utilisateurs, audit de base   : s2, after s1, 2w
    Sprint 3 - Produits, catégories, stock dépôt : s3, after s2, 2w
    Sprint 4 - Transferts                     : s4, after s3, 2w
    Sprint 5 - Ventes (coeur, remises)        : s5, after s4, 2w
    Sprint 6 - Inventaires                    : s6, after s5, 2w
    Sprint 7 - PWA offline (sync ventes)      : s7, after s6, 2w
    Sprint 8 - ETL + Prophet/XGBoost           : s8, after s7, 2w
    Sprint 9 - Scoring crédit + anomalies      : s9, after s8, 2w
    Sprint 10 - Dashboard BI + ABC/XYZ         : s10, after s9, 2w
    Sprint 11 - Multi-tenant avancé + sécurité : s11, after s10, 2w
    Sprint 12 - Tests, CI/CD, doc finale       : s12, after s11, 2w
```

## 23.4 Détail des sprints — livrables

| Sprint | Objectif | Livrables | Definition of Done |
|---|---|---|---|
| 0 | Cadrage | MCD/MLD/MPD, architecture, environnement Docker | Schéma validé, `docker-compose up` fonctionnel |
| 1 | Authentification & multi-tenant | Login JWT, RBAC, schema-per-tenant | Tests d'intégration auth passants, isolation tenant vérifiée |
| 2 | Utilisateurs & audit | CRUD utilisateurs/rôles, table `audit_logs` | Toute action critique journalisée |
| 3 | Produits & stock dépôt | CRUD produits, réceptions fournisseurs, stock dépôt | Contraintes prix (RG-08 à RG-10) testées |
| 4 | Transferts | Création/réception transferts | Cycle d'état complet testé (BROUILLON→RECU) |
| 5 | Ventes | Saisie vente, remises encadrées, crédit | RG-22/RG-23/RG-25 testées |
| 6 | Inventaires | Comptage, écarts, ajustements | RG-33 testée |
| 7 | PWA offline | Service Worker, IndexedDB, sync | Scénario coupure réseau démontré |
| 8 | ETL + prévisions | Pipeline ETL, Prophet/XGBoost | Métriques RMSE/MAE documentées (cf. `20-MACHINE-LEARNING.md`) |
| 9 | Scoring & anomalies | Random Forest scoring, Isolation Forest | Métriques précision/rappel documentées |
| 10 | Dashboard BI | Tableau de bord temps réel, export PDF | WebSocket fonctionnel, export PDF généré |
| 11 | Multi-tenant avancé & sécurité | Migrations multi-schéma, durcissement sécurité | Audit sécurité (cf. `18-SECURITE.md`) réalisé |
| 12 | Tests & documentation | Couverture ≥ 80 %, documentation soutenance | CI verte, documentation `docs/` complète |

## 23.5 Suivi d'avancement (exemple de tableau de burndown)

| Sprint | Story points planifiés | Story points réalisés | Vélocité cumulée |
|---|---|---|---|
| 1 | 20 | 18 | 18 |
| 2 | 18 | 18 | 36 |
| 3 | 22 | 20 | 56 |
| ... | ... | ... | ... |

> Ce tableau est à compléter au fil du projet réel et présenté en soutenance pour démonstrer la démarche itérative (mesure de vélocité, ajustement du backlog).

## 23.6 Définition des rôles dans l'équipe (projet académique)

| Rôle Scrum | Porteur | Responsabilité |
|---|---|---|
| Product Owner | Encadreur / vision métier | Priorisation backlog, validation des incréments |
| Développeur Full-Stack & Data | Étudiant (porteur du projet) | Développement backend, frontend, modèles IA |
| Scrum Master | Étudiant (auto-organisation) | Suivi du planning, gestion des blocages |
| Utilisateurs pilotes | Quincaillerie partenaire (si disponible) | Retours UX, validation terrain (UC-11, écran caissier) |

## 23.7 Gestion des risques projet

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Absence de données réelles pour entraîner les modèles IA | Élevée | Moyen | Jeu de données synthétique documenté (`20-MACHINE-LEARNING.md` §20.6) |
| Complexité du mode offline sous-estimée | Moyenne | Élevé | Sprint dédié (7), prototype précoce |
| Dérive de planning sur le module IA | Moyenne | Moyen | Sprints 8-10 dédiés, backlog IA priorisé MoSCoW |
| Multi-tenant ajoutant de la complexité transverse | Moyenne | Moyen | Architecture schema-per-tenant posée dès Sprint 0-1 |
