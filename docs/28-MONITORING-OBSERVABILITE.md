# 28. Monitoring & Observabilité

## 28.1 Objectifs

- Garantir la **disponibilité** annoncée (RNF-02 : 99,5 %) via une détection rapide des incidents.
- Fournir aux administrateurs technique une **vue d'ensemble de la santé du système** (API, base de données, files Celery, modèles IA).
- Tracer les **événements de sécurité** (cf. `18-SECURITE.md`) et les **anomalies métier** (cf. `20-MACHINE-LEARNING.md` §20.5) dans un même socle d'observabilité.

## 28.2 Architecture d'observabilité

```mermaid
flowchart TB
    subgraph "Applications"
        API[API Flask]
        WRK[Celery Workers]
        FE[Frontend React]
    end

    subgraph "Collecte"
        LOGS[Logs structurés JSON\n(stdout -> Docker logging driver)]
        METRICS[Métriques applicatives\n(Prometheus client)]
        SENTRY[Erreurs front/back\n(Sentry SDK)]
    end

    subgraph "Stockage & visualisation"
        LOKI[(Loki - logs)]
        PROM[(Prometheus - métriques)]
        GRAF[Grafana - dashboards]
    end

    API & WRK & FE --> LOGS --> LOKI
    API & WRK --> METRICS --> PROM
    API & FE --> SENTRY
    LOKI --> GRAF
    PROM --> GRAF
    PROM -->|règles d'alerte| ALERT[Alertmanager]
    ALERT -->|email / webhook| ADMIN[Administrateur technique]
```

> **Périmètre académique** : la stack Prometheus/Loki/Grafana est proposée comme **cible recommandée**. Pour la phase de soutenance, un sous-ensemble minimal (logs structurés + endpoint `/health` + tableau de bord applicatif `22-DASHBOARD-BI.md`) suffit à démontrer la démarche ; la stack complète est documentée comme **perspective de mise en production** (`31-CONCLUSION-PERSPECTIVES.md`).

## 28.3 Logs structurés

Tous les services émettent des logs JSON sur `stdout` (collectés par le driver de logging Docker) :

```json
{
  "timestamp": "2026-06-14T08:32:10Z",
  "level": "INFO",
  "service": "api",
  "tenant": "tenant_abc",
  "request_id": "a1b2c3d4",
  "user_id": "uuid-user",
  "event": "SALE_CREATED",
  "sale_id": "uuid-sale",
  "duration_ms": 87
}
```

| Champ | Description |
|---|---|
| `request_id` | Identifiant unique de requête (propagé via header `X-Request-ID`), permet de corréler logs API ↔ Celery ↔ frontend |
| `tenant` | Schéma tenant concerné — essentiel pour le support multi-tenant |
| `event` | Code d'événement métier (aligné avec les types de `audit_logs`, cf. `16-CONTRAINTES-SQL.md`) |

## 28.4 Métriques applicatives clés (Prometheus)

| Métrique | Type | Description | Lien RNF |
|---|---|---|---|
| `http_request_duration_seconds` | Histogram | Latence des endpoints API par route/méthode | RNF-01 (p95 < 200 ms) |
| `http_requests_total{status}` | Counter | Nombre de requêtes par code de statut | RNF-02 (taux d'erreur) |
| `celery_task_duration_seconds` | Histogram | Durée des tâches Celery (ETL, prévisions) | RNF-17 |
| `celery_queue_length` | Gauge | Nombre de tâches en attente dans Redis | Détection de saturation |
| `db_connections_active` | Gauge | Connexions PostgreSQL actives | RNF-06 (volumétrie) |
| `sync_offline_sales_pending` | Gauge | Nombre de ventes offline en attente de sync, tous tenants | RG-28-30 |
| `ml_prediction_lag_hours` | Gauge | Âge de la dernière exécution réussie par type de modèle | RNF-17 (fraîcheur des prédictions) |

## 28.5 Endpoint de santé (`/health`)

```yaml
/health:
  get:
    summary: Vérification de l'état de santé de l'application
    security: []   # endpoint public, non authentifié
    responses:
      '200':
        content:
          application/json:
            schema:
              type: object
              properties:
                status: { type: string, enum: [ok, degraded, down] }
                checks:
                  type: object
                  properties:
                    database: { type: string, enum: [ok, error] }
                    redis: { type: string, enum: [ok, error] }
                    celery_workers: { type: integer, description: "nombre de workers actifs" }
```

Utilisé par : l'orchestrateur Docker (`healthcheck`), un service de supervision externe (UptimeRobot ou équivalent), et le tableau de bord administrateur.

## 28.6 Règles d'alerte (Alertmanager — exemples)

| Alerte | Condition | Sévérité | Action |
|---|---|---|---|
| `APIHighLatency` | p95 latence > 200 ms pendant 5 min | WARNING | Notification admin technique |
| `APIHighErrorRate` | Taux d'erreurs 5xx > 1 % pendant 5 min | CRITICAL | Notification immédiate (email + webhook) |
| `CeleryQueueBacklog` | `celery_queue_length` > 100 pendant 10 min | WARNING | Vérifier capacité des workers |
| `MLPredictionStale` | `ml_prediction_lag_hours` > 36h (modèle hebdo attendu chaque semaine) | WARNING | Vérifier la tâche `recompute_stock_predictions` |
| `OfflineSyncBacklog` | `sync_offline_sales_pending` > 500 sur un tenant pendant 1h | WARNING | Investiguer connectivité boutique |
| `DatabaseDown` | `/health` → `database: error` | CRITICAL | Déclenchement procédure PRA (`25-DEPLOIEMENT-CICD.md`) |

## 28.7 Tableaux de bord Grafana (proposition)

| Dashboard | Contenu |
|---|---|
| **Vue Opérations** | Latence API, taux d'erreurs, charge CPU/mémoire conteneurs, connexions DB |
| **Vue Celery / IA** | Durée des tâches, fraîcheur des prédictions par tenant, taux de succès des entraînements |
| **Vue Multi-tenant** | Nombre de tenants actifs, ventes offline en attente par tenant, volumétrie par schéma |
| **Vue Sécurité** | Tentatives de connexion échouées, accès refusés (403), activité par rôle |

## 28.8 Gestion des erreurs applicatives (Sentry)

- **Frontend** : capture des exceptions JS non gérées, erreurs de rendu React, avec contexte utilisateur (rôle, tenant — sans données personnelles sensibles, cf. RGPD/`18-SECURITE.md`).
- **Backend** : capture des exceptions non gérées par Flask (au-delà des `ApiError` métier déjà gérées), avec `request_id` pour corrélation avec les logs structurés.

```python
# app/__init__.py (extrait)
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=app.config["SENTRY_DSN"],
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
)
```

## 28.9 Rétention et conformité

| Donnée | Rétention | Justification |
|---|---|---|
| Logs applicatifs (Loki) | 30 jours | Suffisant pour le débogage opérationnel |
| Journal d'audit (`audit_logs`) | 1 an minimum (table partitionnée par mois, cf. `16-CONTRAINTES-SQL.md`) | RNF-18, traçabilité métier/légale |
| Métriques Prometheus | 90 jours (résolution native), agrégats au-delà | Analyse de tendances |
| Erreurs Sentry | 90 jours | Politique par défaut Sentry, ajustable |
