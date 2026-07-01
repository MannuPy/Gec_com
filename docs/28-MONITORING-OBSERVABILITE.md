# 28. Monitoring & Observabilité

## 28.1 Objectifs

- Garantir la **disponibilité** annoncée (RNF-02 : 99,5 %) via une détection rapide des incidents.
- Fournir aux administrateurs technique une **vue d'ensemble de la santé du système** (API, base de données, entraînements ML, modèles IA).
- Tracer les **événements de sécurité** (cf. `18-SECURITE.md`) et les **anomalies métier** (cf. `20-MACHINE-LEARNING.md` §20.5) dans un même socle d'observabilité.

## 28.2 Architecture d'observabilité

```mermaid
flowchart TB
    subgraph "Applications"
        API[API Flask]
        WRK[Threads ML / Cron PythonAnywhere]
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

Tous les services émettent des logs JSON sur `stdout`. Sur PythonAnywhere, ces logs sont visibles dans l'onglet **Web → Log files** (`server.log`, `error.log`) ; sur un VPS Docker, ils sont collectés par le driver de logging Docker vers Loki.

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
| `request_id` | Identifiant unique de requête (propagé via header `X-Request-ID`), permet de corréler logs API ↔ threads ↔ frontend |
| `tenant` | Schéma tenant concerné — essentiel pour le support multi-tenant |
| `event` | Code d'événement métier (aligné avec les types de `audit_logs`, cf. `16-CONTRAINTES-SQL.md`) |

## 28.4 Métriques applicatives clés (Prometheus)

| Métrique | Type | Description | Lien RNF |
|---|---|---|---|
| `http_request_duration_seconds` | Histogram | Latence des endpoints API par route/méthode | RNF-01 (p95 < 200 ms) |
| `http_requests_total{status}` | Counter | Nombre de requêtes par code de statut | RNF-02 (taux d'erreur) |
| `ml_train_duration_seconds` | Histogram | Durée d'entraînement ML par type de modèle (cron + threads) | RNF-17 |
| `db_connections_active` | Gauge | Connexions MySQL actives (PythonAnywhere) | RNF-06 (volumétrie) |
| `sync_offline_sales_pending` | Gauge | Nombre de ventes offline en attente de sync, tous tenants | RG-28-30 |
| `ml_prediction_lag_hours` | Gauge | Âge de la dernière exécution réussie par type de modèle | RNF-17 (fraîcheur des prédictions) |

## 28.5 Endpoint de santé (`/health`)

```json
// GET /health — réponse réelle (code 200 si ok, 503 si dégradé)
{
  "status": "ok",
  "version": "dev",
  "uptime_s": 4521.3,
  "db": "ok",
  "ml_models_actifs": 5,
  "timestamp_utc": "2026-06-24T10:15:30Z"
}
```

Implémenté dans `app/__init__.py` — effectue un `SELECT 1` sur la DB et compte les modèles ML actifs. Répond en **503** si la base est indisponible.

Utilisé par : UptimeRobot (supervision externe), pipeline CI/CD (smoke test post-déploiement), tableau de bord administrateur.

## 28.6 Règles d'alerte (Alertmanager — exemples)

| Alerte | Condition | Sévérité | Action |
|---|---|---|---|
| `APIHighLatency` | p95 latence > 200 ms pendant 5 min | WARNING | Notification admin technique |
| `APIHighErrorRate` | Taux d'erreurs 5xx > 1 % pendant 5 min | CRITICAL | Notification immédiate (email + webhook) |
| `MLPredictionStale` | `ml_prediction_lag_hours` > 36h (modèle hebdo attendu chaque semaine) | WARNING | Vérifier le script cron `cron_train_all.py` sur PythonAnywhere |
| `OfflineSyncBacklog` | `sync_offline_sales_pending` > 500 sur un tenant pendant 1h | WARNING | Investiguer connectivité boutique |
| `DatabaseDown` | `/health` → `database: error` | CRITICAL | Déclenchement procédure PRA (`25-DEPLOIEMENT-CICD.md`) |

## 28.7 Tableaux de bord Grafana (proposition)

| Dashboard | Contenu |
|---|---|
| **Vue Opérations** | Latence API, taux d'erreurs, charge CPU/mémoire conteneurs, connexions DB |
| **Vue IA / Entraînement** | Durée des entraînements ML (cron + threads), fraîcheur des prédictions, taux de succès par type de modèle |
| **Vue Multi-tenant** | Nombre de tenants actifs, ventes offline en attente par tenant, volumétrie par schéma |
| **Vue Sécurité** | Tentatives de connexion échouées, accès refusés (403), activité par rôle |

## 28.8 Gestion des erreurs applicatives (Sentry)

- **Frontend** : capture des exceptions JS non gérées, erreurs de rendu React, avec contexte utilisateur (rôle, tenant — sans données personnelles sensibles, cf. RGPD/`18-SECURITE.md`).
- **Backend** : capture des exceptions non gérées par Flask (au-delà des `ApiError` métier déjà gérées), avec `request_id` pour corrélation avec les logs structurés.

```python
# app/__init__.py — initialisation Sentry (optionnel, activé si SENTRY_DSN est défini)
_sentry_dsn = app.config.get("SENTRY_DSN") or os.environ.get("SENTRY_DSN")
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
            environment=os.environ.get("FLASK_ENV", "production"),
            release=os.environ.get("APP_VERSION", "dev"),
        )
    except ImportError:
        app.logger.warning("sentry-sdk non installé — monitoring Sentry désactivé")
```

> **Note** : si `SENTRY_DSN` n'est pas défini dans les variables d'environnement, Sentry ne s'initialise pas — le backend fonctionne normalement sans monitoring d'erreurs distant.

## 28.9 Rétention et conformité

| Donnée | Rétention | Justification |
|---|---|---|
| Logs applicatifs (Loki) | 30 jours | Suffisant pour le débogage opérationnel |
| Journal d'audit (`audit_logs`) | 1 an minimum (table partitionnée par mois, cf. `16-CONTRAINTES-SQL.md`) | RNF-18, traçabilité métier/légale |
| Métriques Prometheus | 90 jours (résoluti