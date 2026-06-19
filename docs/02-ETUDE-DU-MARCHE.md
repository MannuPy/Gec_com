# 2. Étude du marché & Analyse de l'existant

## 2.1 Objectif

Justifier le choix de développer une solution sur-mesure plutôt que d'adopter une solution existante, en comparant les alternatives du marché sur des critères pertinents au contexte burkinabè.

## 2.2 Solutions concurrentes analysées

| Solution | Type | Forces | Faiblesses (contexte BF) |
|---|---|---|---|
| **Odoo** | ERP open-source modulaire | Très complet (CRM, achats, stock, compta) ; écosystème large | Lourd, courbe d'apprentissage élevée, hébergement coûteux, dépendance internet forte, personnalisation IA limitée sans développement lourd |
| **Sage 100 / Sage Compta** | ERP commercial | Robuste, reconnu en Afrique francophone | Licence coûteuse, peu adapté multi-boutiques avec dépôt central, pas de mode offline natif, pas d'IA intégrée |
| **Wave (POS)** | Solution de caisse simplifiée | Simple d'utilisation, gratuit | Pas de gestion de dépôt central/transferts, pas d'analytics avancés, pas de personnalisation |
| **Excel / Cahiers papier** | Solution artisanale | Coût nul, flexible | Pas de centralisation, pas de traçabilité, erreurs fréquentes, pas d'analyse de données, pas de sécurité |
| **Loyverse POS** | POS mobile | Multi-boutiques basique, gratuit en entrée | Fonctions avancées payantes en devises étrangères, pas d'IA, pas de gestion fine du crédit informel |

## 2.3 Tableau comparatif multicritères

| Critère | Odoo | Sage | Wave/Loyverse | Excel | **GesCom-BF (notre solution)** |
|---|---|---|---|---|---|
| Coût d'acquisition | Élevé | Élevé | Faible à moyen | Nul | Faible (SaaS adapté) |
| Gestion dépôt central + boutiques | Oui (complexe à configurer) | Partiel | Non | Manuel | **Oui, natif** |
| Mode hors-ligne | Non | Non | Partiel | N/A | **Oui (PWA + sync)** |
| Tarification double (client/technicien) | Configurable (complexe) | Configurable | Non | Manuel | **Natif** |
| Gestion des remises encadrées | Générique | Générique | Limitée | Manuel | **Natif (5/10/15/20 %)** |
| Prévision de rupture de stock (IA) | Module payant tiers | Non | Non | Non | **Natif (Prophet/XGBoost)** |
| Scoring crédit informel | Non | Non | Non | Non | **Natif (innovation)** |
| Détection d'anomalies (remises, ventes) | Non | Non | Non | Non | **Natif (Isolation Forest)** |
| Multilingue (français/mooré) | Non | Non | Non | N/A | **Natif** |
| Architecture multi-tenant SaaS | Possible (Odoo.sh, coûteux) | Non | Oui (limité) | N/A | **Natif (schema-per-tenant)** |
| Hébergement local / souveraineté des données | Selon offre | Selon offre | Cloud étranger | Local | **Flexible (Docker, local possible)** |

## 2.4 Justification des choix technologiques

| Choix | Justification |
|---|---|
| **Flask (Python)** | Léger, flexible, écosystème riche pour l'IA (scikit-learn, Prophet, XGBoost) déjà en Python — évite une rupture de stack entre backend et data science |
| **PostgreSQL** | Open-source, robuste, supporte le **schema-per-tenant** nativement (multi-tenant SaaS), JSONB pour flexibilité, extensions (pg_cron, TimescaleDB possible pour séries temporelles) |
| **SQLAlchemy + Alembic** | ORM mature, migrations versionnées indispensables pour un schéma évolutif multi-tenant |
| **React + TypeScript + Vite** | Écosystème moderne, typage fort réduisant les bugs, Vite pour un build rapide, compatible PWA |
| **Redis + Celery** | File de tâches asynchrones pour les calculs ML (entraînement Prophet/XGBoost) et les alertes, sans bloquer l'API |
| **JWT** | Authentification stateless adaptée à une architecture API séparée frontend/backend, avec refresh tokens pour gestion offline |
| **Docker / Nginx / Gunicorn** | Déploiement reproductible, isolation, scalabilité horizontale par tenant si nécessaire |
| **Prophet + XGBoost** | Prophet pour la saisonnalité (fêtes, saison des pluies) avec peu de données ; XGBoost pour affiner avec variables exogènes (promotions, jours fériés) |
| **Scikit-learn (scoring, clustering, Isolation Forest)** | Bibliothèque standard, modèles interprétables (régression logistique, Random Forest) adaptés à un jury non-spécialiste |

## 2.5 Opportunités identifiées (synthèse marché)

1. **Aucun acteur** ne propose une offre combinant gestion dépôt/boutiques + mode offline + IA contextualisée au marché ouest-africain.
2. La **digitalisation des PME** est une priorité affichée par les politiques publiques burkinabè (stratégie nationale de transformation digitale) → opportunité de subventions / partenariats.
3. Le **crédit informel** est une réalité non adressée par les ERP existants — différenciateur fort.
4. La **connectivité intermittente** rend tout produit "cloud-only" risqué — l'architecture offline-first est un argument commercial majeur.

## 2.6 Positionnement de GesCom-BF

```
Axe 1 : Complexité fonctionnelle  (faible → élevée)
Axe 2 : Adaptation au contexte local (faible → élevée)

         Élevée  |  Odoo, Sage          |  GesCom-BF
Adaptation       |  (génériques)        |  (sur-mesure + IA)
locale           |----------------------|----------------------
         Faible  |  Excel/Cahiers       |  Wave/Loyverse
                 |  (artisanal)         |  (POS basique)
                 +----------------------+----------------------
                     Faible                  Élevée
                     Complexité fonctionnelle
```

GesCom-BF se positionne comme une solution **à forte adaptation locale et complexité fonctionnelle maîtrisée** (modulaire, pas de sur-ingénierie), avec un **