# 25. Déploiement, CI/CD & Continuité d'activité

## 25.1 Architecture de déploiement (Docker Compose)

```mermaid
flowchart TB
    subgraph "Hôte de production (VPS / Cloud)"
        N[Nginx\nReverse proxy + TLS]
        F[Frontend React\n(build statique servi par Nginx)]
        A1[API Flask - Gunicorn\nworker 1]
        A2[API Flask - Gunicorn\nworker 2]
        W[Celery Worker]
        B[Celery Beat]
        R[(Redis)]
        P[(PostgreSQL)]
        M[MLflow Server]
    end

    Internet -->|HTTPS 443| N
    N -->|/| F
    N -->|/api| A1
    N -->|/api| A2
    N -->|/ws| A1
    A1 & A2 --> P
    A1 & A2 --> R
    W --> P
    W --> R
    B --> R
    W -.artefacts.-> M
```

## 25.2 Docker Compose (extrait)

```yaml
# docker-compose.prod.yml (extrait)
services:
  nginx:
    image: nginx:1.27-alpine
    ports: ["443:443", "80:80"]
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certs:/etc/nginx/certs:ro
      - frontend_build:/usr/share/nginx/html:ro
    depends_on: [api]

  api:
    build: ./backend
    command: gunicorn -w 4 -b 0.0.0.0:8000 --timeout 60 wsgi:app
    env_file: .env.prod
    depends_on: [db, redis]
    deploy:
      replicas: 2

  worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    env_file: .env.prod
    depends_on: [db, redis]

  beat:
    build: ./backend
    command: celery -A app.celery_app beat --loglevel=info
    env_file: .env.prod
    depends_on: [redis]

  db:
    image: postgres:16-alpine
    volumes: ["pgdata:/var/lib/postgresql/data"]
    env_file: .env.prod

  redis:
    image: redis:7-alpine
    volumes: ["redisdata:/data"]

  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.12.1
    command: mlflow server --host 0.0.0.0 --backend-store-uri postgresql://... --default-artifact-root /mlruns
    volumes: ["mlruns:/mlruns"]

volumes:
  pgdata:
  redisdata:
  mlruns:
  frontend_build:
```

## 25.2.1 Configuration Docker Compose dev (`docker-compose.yml`)

Le service `api` en développement local utilise `flask run` avec `--no-reload` pour éviter les redémarrages intempestifs liés au rechargeur Werkzeug sur les volumes WSL2 (cf. §9.9.1) :

```yaml
api:
  command: >
    sh -c "flask db upgrade && python -m app.seed &&
           flask run --host=0.0.0.0 --port=5000 --no-reload"
```

> **À noter** : `--no-reload` désactive le rechargeur automatique de code. Après modification d'un fichier Python, relancer le conteneur : `docker compose restart api`.

Le service `worker` (Celery) est configuré avec `broker_connection_retry_on_startup=True` dans `backend/app/celery_app.py` pour supprimer l'avertissement de dépréciation Celery 5.3+ (`CPendingDeprecationWarning`).

## 25.3 Environnements

| Environnement | Usage | Données | Déploiement |
|---|---|---|---|
| **Local (dev)** | Développement quotidien | Jeu de données synthétique réduit | `docker-compose.yml`, `--no-reload` (rechargeur désactivé) |
| **CI** | Validation automatique des PR | Base de test éphémère (conteneur jetable) | GitHub Actions |
| **Staging** | Recette / démonstration jury | Jeu de données synthétique complet | `docker-compose.staging.yml` sur VPS dédié |
| **Production** | Exploitation réelle (post-soutenance) | Données réelles tenants | `docker-compose.prod.yml`, sauvegardes actives |

## 25.4 Pipeline CI/CD (GitHub Actions)

```mermaid
flowchart LR
    A[Push / Pull Request] --> B[Lint\nflake8, eslint]
    B --> C[Tests unitaires\nbackend + frontend]
    C --> D[Tests intégration\nAPI + DB conteneurisée]
    D --> E[Tests E2E\nPlaywright]
    E --> F[Scan sécurité\npip-audit, npm audit]
    F --> G{Branche main ?}
    G -- Oui --> H[Build images Docker]
    H --> I[Push registre\n(GHCR)]
    I --> J[Déploiement Staging\n(automatique)]
    J --> K[Déploiement Production\n(manuel, approbation)]
    G -- Non --> Z[Fin - statut PR]
```

| Étape | Déclencheur | Action |
|---|---|---|
| Lint + tests | Chaque push / PR | Bloquant — PR non mergeable si échec |
| Build images | Push sur `main` | Construit `backend:sha`, `frontend:sha` |
| Déploiement staging | Push sur `main` réussi | `docker compose -f docker-compose.staging.yml up -d` via SSH |
| Déploiement production | Tag `v*.*.*` + approbation manuelle (environnement GitHub protégé) | Migration Alembic (toutes les bases tenants) puis rolling update |

## 25.5 Migrations multi-tenant (Alembic)

```python
# scripts/migrate_all_tenants.py
from app import create_app, db
from app.models import Company
from alembic.config import Config
from alembic import command

app = create_app()
with app.app_context():
    companies = Company.query.all()
    for company in companies:
        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", db.engine.url.render_as_string(hide_password=False))
        cfg.attributes["schema"] = company.schema_name
        command.upgrade(cfg, "head")
        print(f"Migration appliquée : {company.schema_name}")
```

Exécuté en étape de déploiement avant le redémarrage des conteneurs `api`/`worker` — chaque schéma tenant est migré individuellement, avec rollback automatique de l'étape de déploiement en cas d'échec sur un schéma.

## 25.6 Stratégie de sauvegarde (RNF-11, RNF-12, RNF-13)

| Élément | Fréquence | Méthode | Rétention | RPO / RTO |
|---|---|---|---|---|
| PostgreSQL (toutes bases) | Quotidienne (03h00) | `pg_dump` par tenant + dump global, chiffré (GPG) | 30 jours glissants + 12 sauvegardes mensuelles | RPO ≤ 24h |
| Volumes Redis | Quotidienne | Snapshot RDB | 7 jours | RPO ≤ 24h (cache reconstructible) |
| Artefacts MLflow | Hebdomadaire | Sync vers stockage objet (S3-compatible) | 90 jours | RPO ≤ 7j |
| Configuration / secrets | À chaque changement | Coffre-fort secrets (Vault / variables CI chiffrées) | Versionné | - |

```bash
#!/bin/bash
# scripts/backup_postgres.sh
DATE=$(date +%Y%m%d)
for SCHEMA in $(psql -At -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%'"); do
  pg_dump -n "$SCHEMA" gescom_bf | gzip | gpg --encrypt -r backup@gescom-bf.bf \
    > "/backups/${DATE}_${SCHEMA}.sql.gz.gpg"
done
# Rotation : suppression des sauvegardes > 30 jours (sauf 1er du mois)
find /backups -name "*.sql.gz.gpg" -mtime +30 ! -name "*-01_*" -delete
```

## 25.7 Plan de Reprise d'Activité (PRA) / Plan de Continuité d'Activité (PCA)

| Scénario de sinistre | Procédure de reprise | RTO cible |
|---|---|---|
| Panne serveur applicatif (API/Celery) | Redéploiement automatique sur infrastructure de secours via `docker compose up` + restauration dernière sauvegarde DB | < 4h |
| Corruption base de données d'un tenant | Restauration du dump `pg_dump` du schéma concerné le plus récent, rejoue des migrations si nécessaire | < 4h |
| Perte du serveur Redis | Reconstruction du cache à la volée (non bloquant pour les données critiques, files Celery re-créées) | < 1h |
| Perte totale du site (catastrophe) | Reconstitution sur nouvel hôte depuis sauvegardes chiffrées hors-site (stockage objet distant) | < 24h (RPO ≤ 24h respecté) |

### 25.7.1 Procédure de restauration (extrait)

```bash
# 1. Provisionner un nouvel hôte, installer Docker
# 2. Récupérer la dernière sauvegarde chiffrée
gpg --decrypt backup_20260613_tenant_abc.sql.gz.gpg | gunzip > restore.sql

# 3. Recréer le schéma et restaurer
psql gescom_bf -c "CREATE SCHEMA tenant_abc;"
psql gescom_bf -d gescom_bf -f restore.sql

# 4. Rejouer les migrations Alembic pour aligner le schéma
python scripts/migrate_all_tenants.py --schema tenant_abc

# 5. Relancer les services
docker compose -f docker-compose.prod.yml up -d
```

### 25.7.2 Test de restauration (exercice périodique)

> **Bonne pratique documentée** : un exercice de restauration complet (sauvegarde → environnement isolé → restauration → vérification d'intégrité applicative) doit être réalisé **trimestriellement** et consigné (date, durée réelle constatée, écarts vs RTO/RPO cibles) — traçabilité présentable au jury et aux futurs clients SaaS.

## 25.8 Observabilité du déploiement

Voir `28-MONITORING-OBSERVABILITE.md` pour le détail des logs, métriques et alertes opérationnelles (santé des conteneurs, files Celery, latence API).

## 25.9 Déploiement alternatif : PythonAnywhere (hébergement mono-processus)

Pour une mise en production légère (sans VPS Docker), l'application peut être
déployée sur **PythonAnywhere**, plan **"Developer"** (~10 $/mois). Cette
cible impose une architecture simplifiée par rapport à la §25.1 — pas de
conteneurs, pas de worker Celery/Redis dédié, et une base **MySQL** (la seule
base de données managée proposée par PythonAnywhere, PostgreSQL n'étant pas
disponible).

Conséquence directe : l'application est déployée en **mode mono-tenant**
(une seule base de données = le tenant applicatif "public"). Le mécanisme
multi-tenant *schema-per-tenant* décrit en §27 reste présent dans le code
mais n'est actif que sur PostgreSQL — cf. `app/utils/db_dialect.py`,
`app/models/company.py` (`_PUBLIC_SCHEMA_ARGS`), `app/utils/tenant.py`
(`set_search_path` devient un no-op sur MySQL) et
`app/services/tenant_provisioning.py` (l'inscription self-service RF-01
renvoie une erreur 503 explicite sur ce déploiement).

### 25.9.1 Contraintes et adaptations

| Composant (architecture VPS) | Sur PythonAnywhere | Adaptation |
|---|---|---|
| PostgreSQL (conteneur `db`) | Non disponible | Base **MySQL managée incluse** (onglet "Databases"), pilote `PyMySQL`, accessible via `DATABASE_URL=mysql+pymysql://...` |
| Multi-tenant *schema-per-tenant* (§27) | `CREATE SCHEMA` / `SET search_path` indisponibles sur MySQL | **Mode mono-tenant** : une seule base = tenant `public` (cf. `_PUBLIC_SCHEMA_ARGS`, `set_search_path` no-op). L'inscription self-service de nouvelles entreprises (RF-01) est désactivée (503) |
| Celery worker + beat + Redis | Non disponibles | Commandes **Flask CLI** (`flask etl-daily`, `flask ml-train-all`, `flask ml-detect-anomalies`, cf. `backend/app/cli.py`) exécutées en synchrone via `.run()`, planifiées par les **"Scheduled tasks"** de PythonAnywhere |
| Nginx + build frontend statique | Géré par l'app Flask (uWSGI) | Build `frontend/dist` servi directement par Flask via `SERVE_FRONTEND_DIST` (cf. `app/__init__.py: register_frontend`) — même domaine, pas de CORS |
| Reverse proxy HTTPS | Fourni par PythonAnywhere | `PREFERRED_URL_SCHEME=https` (déjà dans `ProdConfig`) |
| SSE (`/reports/dashboard/stream`) | Streaming potentiellement bufferisé par le proxy uWSGI | Le frontend (`useDashboardStream`) retombe automatiquement sur le **polling** (`reportsApi.realtime`) si le flux SSE ne s'établit pas — aucune action requise, mais à vérifier après déploiement |
| Connexions MySQL persistantes | Fermées par le serveur après `wait_timeout` ("MySQL server has gone away") | `SQLALCHEMY_ENGINE_OPTIONS` (`app/config.py`) : `pool_pre_ping=True` + `pool_recycle=280` (déjà configuré, aucune action requise) |

### 25.9.2 Préparation du compte, de la base MySQL et du code

1. Souscrire à un compte PythonAnywhere, plan **"Developer"** (inclut 1 app
   web, MySQL, consoles, SSH, 20 tâches planifiées, 1 tâche "always-on").
2. Créer la base MySQL — onglet **Databases** :
   - Définir un mot de passe MySQL (bouton **"Set password"** — différent du
     mot de passe du compte PythonAnywhere) ;
   - Créer une base, ex. `gescom_bf` → nom complet `<utilisateur>$gescom_bf` ;
   - Noter l'hôte : `<utilisateur>.mysql.pythonanywhere-services.com`.
3. Dans une console Bash PythonAnywhere :

   ```bash
   cd ~
   git clone <url-du-depot> gescom-bf
   cd gescom-bf/backend

   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt   # installe notamment PyMySQL (driver MySQL)
   ```

### 25.9.3 Configuration (`.env`)

1. Copier le modèle dédié et l'adapter :

   ```bash
   cp .env.pythonanywhere.example .env
   nano .env   # DATABASE_URL (MySQL), SECRET_KEY, JWT_SECRET_KEY, SERVE_FRONTEND_DIST, ...
   ```

2. `DATABASE_URL` au format :

   ```
   mysql+pymysql://<utilisateur>:<motdepasse-mysql>@<utilisateur>.mysql.pythonanywhere-services.com/<utilisateur>$gescom_bf?charset=utf8mb4
   ```

3. Générer des secrets aléatoires (`SECRET_KEY`, `JWT_SECRET_KEY`) :

   ```bash
   # SECRET_KEY (Flask sessions)
   python3 -c "import secrets; print(secrets.token_urlsafe(48))"

   # JWT_SECRET_KEY — minimum 32 octets (256 bits recommandés)
   # token_hex(32) produit 64 caractères hex = 256 bits
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

   > **Important** : Flask-JWT-Extended émet un `InsecureKeyLengthWarning` si `JWT_SECRET_KEY` fait moins de 32 octets. La commande `token_hex(32)` produit une clé de 64 caractères (256 bits) qui satisfait cette exigence. Ne jamais utiliser la valeur par défaut `"dev-jwt-secret"` en production.

   Variables JWT à configurer dans `.env` :

   ```env
   JWT_SECRET_KEY=<64 caractères hex générés ci-dessus>
   JWT_ACCESS_TOKEN_EXPIRES_MINUTES=60   # durée de vie du token d'accès (60 min recommandé)
   JWT_REFRESH_TOKEN_EXPIRES_DAYS=7
   ```

Cf. `backend/.env.pythonanywhere.example` pour la liste complète des
variables (DB MySQL, frontend, ML/MLflow, dashboard temps réel...).

### 25.9.4 Fichier WSGI

PythonAnywhere génère un fichier `/var/www/<utilisateur>_pythonanywhere_com_wsgi.py`
édité depuis l'onglet **Web**. Remplacer son contenu par celui de
`backend/deploy/pythonanywhere_wsgi.py` (adapter `PROJECT_HOME`), qui :

- ajoute `backend/` au `sys.path` ;
- charge le `.env` de production via `load_dotenv()` ;
- expose `application = create_app("production")`.

Dans l'onglet **Web** :

- **Source code** / **Working directory** : `/home/<utilisateur>/gescom-bf/backend`
- **Virtualenv** : `/home/<utilisateur>/gescom-bf/backend/venv`

### 25.9.5 Base de données : migrations et amorçage

```bash
cd ~/gescom-bf/backend
source venv/bin/activate
export FLASK_APP=wsgi.py
export FLASK_ENV=production

flask db upgrade        # applique toutes les migrations Alembic sur la base MySQL mono-tenant
flask seed               # amorce RBAC, sites, catalogue, démo (idempotent, cf. app/seed.py)
# flask seed-demo        # optionnel : jeu de données de démonstration (cf. donnees-demo/)
```

> Sur MySQL, `flask db upgrade` crée toutes les tables (y compris
> `companies`/`user_index`) directement dans la base
> `<utilisateur>$gescom_bf` — sans `CREATE SCHEMA` (spécifique à PostgreSQL,
> cf. `migrations/versions/b2c3d4e5f6a7_companies_registry.py`).
>
> **CHECK constraints** : MySQL ne les applique réellement qu'à partir de la
> version **8.0.16** (MariaDB 10.2.1+) ; sur une version antérieure, elles
> sont acceptées syntaxiquement mais ignorées silencieusement. Les
> validations métier (prix positifs, statuts d'abonnement, taux de remise,
> etc.) sont de toute façon **revalidées côté application** (services Flask)
> — défense en profondeur, sans dépendance stricte au moteur de base.

### 25.9.6 Build et publication du frontend

Le build Vite est généré **localement ou en CI** (Node.js n'est pas requis
sur PythonAnywhere), puis uploadé :

```bash
# En local
cd frontend
npm ci
npm run build        # génère frontend/dist/

# Upload vers PythonAnywhere (ex. via git, ou rsync/scp)
# Le dossier doit correspondre à SERVE_FRONTEND_DIST défini dans .env
```

Une fois `SERVE_FRONTEND_DIST=/home/<utilisateur>/gescom-bf/frontend/dist`
défini dans `.env` et l'application rechargée, Flask sert le SPA (avec
fallback `index.html` pour le routage client) et l'API sous le même
domaine — `VITE_API_URL` doit rester vide (le client utilise `/api/v1`
relatif, cf. `frontend/src/api/client.ts`).

### 25.9.7 Tâches planifiées (remplacement de Celery beat)

Onglet **Tasks** de PythonAnywhere — ajouter des tâches planifiées
équivalentes au `beat_schedule` de `app/celery_app.py` :

| Fréquence (UTC) | Commande | Rôle |
|---|---|---|
| Quotidienne, 02h00 | `cd ~/gescom-bf/backend && venv/bin/flask etl-daily` | Pipeline ETL (extraction → validation → feature store, §21.6) |
| Quotidienne, 02h30 | `cd ~/gescom-bf/backend && venv/bin/flask ml-train-all` | Réentraînement des modèles (demande, scoring crédit, anomalies, ABC/XYZ, RFM — RF-25 à RF-28) |
| Horaire (si plan suffisant) | `cd ~/gescom-bf/backend && venv/bin/flask ml-detect-anomalies` | Détection d'anomalies sur les ventes récentes (RF-28), sinon couverte par `ml-train-all` |

> Le nombre de tâches planifiées simultanées dépend du plan PythonAnywhere ;
> sur un plan limité, regrouper dans `ml-train-all` (déjà le cas par défaut).

### 25.9.8 Vérification post-déploiement

- `GET https://<utilisateur>.pythonanywhere.com/health` → `{"status": "ok"}`
- Connexion avec le compte créé par `flask seed` (cf. `SEED_ADMIN_EMAIL` /
  `SEED_ADMIN_PASSWORD`), puis changement de mot de passe imposé (RF-05).
- Dashboard (`/reports/dashboard`) : vérifier que les données s'affichent en
  temps réel (SSE) ou via le badge de polling (fallback automatique, §25.9.1).
- Logs d'erreurs : onglet **Web** -> **Log files** (`error.log`, `server.log`).
