# Plan de Propositions Correctives — GesCom-BF
## Objectif : transformer GesCom-BF en solution robuste, fiable et défendable

---

> **Dernière mise à jour :** 1er juillet 2026 — conformité code v2 post-corrections soutenance.

> **Légende priorités :**
> - 🔴 **P0 — Critique** : impact direct sur la fiabilité ou l'intégrité des données. À corriger avant toute mise en production réelle.
> - 🟠 **P1 — Élevé** : risque opérationnel significatif. À traiter dans les 30 premiers jours.
> - 🟡 **P2 — Moyen** : améliore la robustesse et l'adoption. À planifier à 60–90 jours.
> - 🟢 **P3 — Long terme** : évolutions stratégiques pour la version 2.0.

---

## TABLEAU DE PRIORISATION GLOBALE

| # | Problème identifié | Catégorie | Priorité | Statut | Impact |
|---|---|---|---|---|---|
| C1 | Score crédit fictif (SHA-256) présenté comme réel | IA / Données | 🔴 P0 | ✅ RÉSOLU | Intégrité décisionnelle |
| C2 | Absence de journal d'audit (audit log) | Sécurité | 🔴 P0 | ✅ EXISTAIT DÉJÀ (`AuditLog.record()`) | Traçabilité / Conformité |
| C3 | Pas de rate limiting sur le login | Sécurité | 🔴 P0 | ✅ RÉSOLU (Flask-Limiter 3.8.0, `memory://`) | Protection brute-force |
| C4 | JWT stocké en localStorage (XSS) | Sécurité | 🔴 P0 | ⏳ Non migré (httpOnly cookies) — documenté comme amélioration future | Vol de session |
| C5 | Entraînement ML bloquant (Celery sync) | Technique | 🟠 P1 | ✅ RÉSOLU — threads Python natifs + cron `scripts/cron_train_all.py` | Disponibilité API |
| C6 | Pas de stratégie backup/restore documentée | Technique | 🟠 P1 | ⏳ À documenter | Continuité de service |
| C7 | Migrations DB sans procédure de rollback | Technique | 🟠 P1 | ✅ 10 migrations Alembic dans `backend/migrations/versions/` | Intégrité des données |
| C8 | K-Means instable sur faibles volumes | IA / Données | 🟠 P1 | ✅ RÉSOLU — k optimal par Silhouette/Elbow + fallback quartiles | Confiance utilisateur |
| C9 | Feature Store non versionné | IA / Données | 🟠 P1 | ⏳ Amélioration future | Stabilité des modèles |
| C10 | Dérive des modèles non détectée | IA / Données | 🟠 P1 | ⏳ Amélioration future | Précision long terme |
| C11 | Absence de validation des données d'entrée ML | IA / Données | 🟠 P1 | ⏳ Amélioration future | Qualité des modèles |
| C12 | Pas de mode hors ligne (offline) | Produit | 🟡 P2 | ⏳ Hors scope soutenance | Adoption terrain |
| C13 | Interface non mobile-first | Produit | 🟡 P2 | ⏳ Hors scope soutenance | Adoption vendeurs |
| C14 | Onboarding manuel (pas de self-service) | Produit | 🟡 P2 | ⏳ Hors scope soutenance | Scalabilité commerciale |
| C15 | Point de défaillance unique (PythonAnywhere) | Infrastructure | 🟡 P2 | ✅ Sentry SDK optionnel activé (si `SENTRY_DSN`) | Disponibilité SaaS |
| C16 | Données financières non chiffrées au repos | Sécurité | 🟡 P2 | ⏳ Amélioration future | Confidentialité |
| C17 | Pas de module de facturation/abonnement | Business | 🟢 P3 | ⏳ Version 2.0 | Modèle SaaS complet |
| C18 | Pas de monitoring/alerting applicatif | Technique | 🟢 P3 | ✅ RÉSOLU — Sentry SDK + endpoint `/health` + CI 155 tests | Observabilité |

---

## PHASE 0 — CORRECTIONS CRITIQUES (P0)
### Semaine 1–2 : ce qui ne peut pas aller en production

---

### C1 — ✅ Score crédit fictif — RÉSOLU

**Problème résolu :** Le fallback SHA-256 a été **supprimé**. Quand les données de crédit sont insuffisantes, le système retourne `score: null, risk_level: "INDETERMINATE"` avec le message "Historique d'achats insuffisant pour calculer un score fiable". Le frontend affiche un badge gris "Données insuffisantes" au lieu d'un score trompeur.

**Ancienne description :** Le fallback SHA-256 générait un `taux_retard` déterministe à partir de l'ID client. Ce score n'avait aucun fondement dans le comportement réel du client.

**Impact :** Un responsable de crédit qui refuse un crédit sur la base d'un score fantôme prend une décision discriminatoire sans fondement réel.

**Solution : Remplacer le fallback par un état "données insuffisantes" explicite**

Au lieu de fabriquer un score, afficher clairement que le scoring n'est pas disponible :

```python
# Dans credit_scoring.py — remplacement du fallback SHA-256
def _no_data_fallback(customer_ids: list) -> list:
    """
    Retourne un résultat explicite signalant l'absence de données.
    Ne génère PAS de score fictif.
    """
    return [
        {
            "customer_id": cid,
            "score": None,
            "risk_level": "INDISPONIBLE",
            "confidence": 0.0,
            "reason": "Historique de crédit insuffisant — scoring non disponible",
            "data_available": False
        }
        for cid in customer_ids
    ]
```

**Côté frontend :** afficher un badge gris "Données insuffisantes" au lieu d'un score rouge/vert trompeur. Ajouter une info-bulle : *"Le scoring crédit nécessite un historique de paiement. Ce client n'en a pas encore."*

**Effort :** 2–4 heures · **Risque de régression :** Nul

---

### C2 — ✅ Journal d'audit — EXISTAIT DÉJÀ

**Statut :** `AuditLog` avec méthode `AuditLog.record()` est **déjà implémenté** dans `app/models/audit.py`. Ce point était déjà résolu avant le plan correctif.

**Ancienne description :** Aucune trace persistante de qui a fait quoi sur les opérations sensibles (octroi crédit, règlement, rejet remboursement, suppression).

**Impact :** Impossible de reconstituer la chaîne de responsabilité en cas de litige ou fraude interne.

**Solution : Modèle AuditLog + décorateur d'audit**

**Étape 1 — Modèle SQLAlchemy :**
```python
# app/models/audit_log.py
class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(100), nullable=False)   # "CREDIT_SETTLE", "REFUND_REJECT"…
    resource_type = db.Column(db.String(50), nullable=False)  # "credit", "refund"…
    resource_id = db.Column(db.Integer, nullable=True)
    old_value_json = db.Column(db.Text, nullable=True)   # état avant
    new_value_json = db.Column(db.Text, nullable=True)   # état après
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"), nullable=True)
```

**Étape 2 — Décorateur :**
```python
# app/utils/audit.py
from functools import wraps
from flask import g, request
from app.models.audit_log import AuditLog
from app import db

def audit(action: str, resource_type: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            try:
                log = AuditLog(
                    user_id=g.current_user.id,
                    action=action,
                    resource_type=resource_type,
                    ip_address=request.remote_addr,
                    branch_id=getattr(g.current_user, "branch_id", None)
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                pass  # L'audit ne doit jamais bloquer l'opération principale
            return result
        return wrapper
    return decorator

# Utilisation sur un endpoint :
@bp.route("/settle/<int:credit_id>", methods=["POST"])
@require_permission("credits.settle")
@audit("CREDIT_SETTLE", "credit")
def settle_credit(credit_id):
    ...
```

**Opérations à auditer en priorité :** `CREDIT_SETTLE`, `REFUND_REJECT`, `REFUND_APPROVE`, `USER_CREATE`, `USER_DELETE`, `ROLE_CHANGE`, `SALE_DELETE`, `STOCK_ADJUST`.

**Effort :** 1 jour · **Risque de régression :** Très faible (décorateur additif)

---

### C3 — ✅ Rate limiting — RÉSOLU

**Statut :** Flask-Limiter 3.8.0 est **installé et configuré** avec `storage_uri="memory://"` (pas Redis — pas disponible sur PythonAnywhere). Les endpoints `/auth/login` et `/auth/register` sont limités. L'IP réelle est lue via l'en-tête `CF-Connecting-IP` ou `X-Forwarded-For`.

**Solution implémentée :**

```python
# app/__init__.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Sans Redis — adapté PythonAnywhere
)

# Sur l'endpoint login :
@bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")  # 5 tentatives / minute / IP
def login():
    ...
```

**Bonus :** Ajouter un délai progressif après 3 échecs consécutifs (backoff) :
```python
import time
# Après 3 échecs : time.sleep(2 ** (nb_echecs - 3))
```

**Effort :** 2 heures · **Risque de régression :** Nul

---

### C4 — JWT stocké en localStorage (vulnérabilité XSS)

**Problème :** `localStorage` est accessible depuis n'importe quel script JavaScript de la page. Une injection XSS vole le token et donne accès permanent à la session.

**Solution : Migrer vers httpOnly cookies**

**Backend — Flask :**
```python
# À la connexion, set le cookie au lieu de renvoyer le token dans le body
from flask import make_response

@bp.route("/login", methods=["POST"])
def login():
    # ... validation
    access_token = create_access_token(identity=user.id)
    response = make_response(jsonify({"message": "Connexion réussie", "user": user_schema.dump(user)}))
    response.set_cookie(
        "access_token_cookie",
        value=access_token,
        httponly=True,       # Inaccessible depuis JS
        secure=True,         # HTTPS uniquement
        samesite="Strict",   # Protection CSRF
        max_age=3600         # 1 heure
    )
    return response
```

**Frontend — Axios :**
```typescript
// axios.ts — ajouter withCredentials pour envoyer les cookies
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,  // ← envoie les cookies httpOnly automatiquement
});
// Supprimer tout code qui lit/écrit localStorage pour le JWT
```

**Effort :** 4–6 heures · **Risque de régression :** Moyen (tester tous les endpoints protégés)

---

## PHASE 1 — CORRECTIONS ÉLEVÉES (P1)
### Semaines 3–6 : robustesse opérationnelle

---

### C5 — ✅ Entraînement ML non-bloquant — RÉSOLU

**Statut :** Celery et Redis ont été **supprimés** de la stack. Deux mécanismes remplacent l'ancien système bloquant :
1. **Threads Python natifs** (`threading.Thread`, daemon=True) pour l'entraînement à la demande via l'API
2. **Script `scripts/cron_train_all.py`** planifié via PythonAnywhere Tasks (quotidien 02:00) pour le réentraînement automatique

**Commande cron correcte :**
```
/home/<username>/.virtualenvs/gescom-bf/bin/python /home/<username>/gescom-bf/scripts/cron_train_all.py
```

**Solution implémentée (Solution A — Thread Python natif) :**

```python
# app/utils/async_task.py
import threading
from typing import Callable

def run_in_background(func: Callable, *args, **kwargs):
    """Lance une fonction dans un thread daemon — fallback sans Celery."""
    thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return {"status": "started", "message": "Entraînement lancé en arrière-plan"}

# Dans analytics/routes.py :
@bp.route("/ml/train/<model_type>", methods=["POST"])
@require_permission("analytics.train")
def train_model(model_type):
    result = run_in_background(_train_model_sync, model_type, branch_id)
    return jsonify(result), 202  # 202 Accepted — pas de blocage
```

**Option future (VPS) :** Si le projet migre sur un VPS avec Redis, Celery peut être réintroduit sans modifier le code métier. Pour l'instant, la solution threads + cron est la solution de production sur PythonAnywhere.

**Effort :** ✅ Résolu — Solution threads + cron en production

---

### C6 — Stratégie de backup et restauration

**Problème :** Aucune procédure documentée de sauvegarde ni de restauration. Une erreur de migration ou une corruption de données est irréversible.

**Solution : Script de backup automatisé + procédure de rollback**

```bash
#!/bin/bash
# scripts/backup.sh — à planifier en cron quotidien sur PythonAnywhere
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/user/backups"
DB_NAME="gescom_prod"

mkdir -p $BACKUP_DIR
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME \
  | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Garder les 30 derniers backups
ls -t $BACKUP_DIR/backup_*.sql.gz | tail -n +31 | xargs rm -f

echo "Backup $DATE terminé" >> $BACKUP_DIR/backup.log
```

**Procédure de rollback migration :**
```bash
# Avant toute migration en production :
flask db stamp head   # Marquer l'état actuel

# Si la migration échoue :
flask db downgrade -1  # Revenir d'un cran
# Ou rollback complet depuis le dernier backup :
gunzip -c backup_YYYYMMDD.sql.gz | mysql -u $DB_USER -p $DB_NAME
```

**Ajouter dans CLAUDE.md / README_PROD.md :** procédure step-by-step.

**Effort :** 4 heures · **Risque de régression :** Nul

---

### C7 (anciennement C8) — ✅ K-Means instable sur faibles volumes — RÉSOLU

**Statut :** Le k optimal est maintenant déterminé automatiquement via `evaluate_optimal_k()` (score de Silhouette + inertie Elbow). Fallback sur segmentation par quartiles si données insuffisantes. Endpoint `/analytics/rfm-segments/evaluate-k` expose les scores.

**Ancienne description :** K-Means avec k=4 sur un petit nombre de clients produisait des segments qui changeaient à chaque réentraînement.

**Solution 1 : Seuil minimum avant activation K-Means**

```python
# rfm_segmentation.py
MIN_CUSTOMERS_FOR_KMEANS = 30  # Seuil raisonnable pour 4 clusters

def segment(branch_id=None, ...):
    df = _get_rfm_data(branch_id)
    if len(df) < MIN_CUSTOMERS_FOR_KMEANS:
        return _rule_based_segmentation(df)  # Fallback règles quantiles
    return _kmeans_segmentation(df)
```

**Solution 2 : Segmentation par quantiles (règle des tiers) comme fallback**

```python
def _rule_based_segmentation(df):
    """
    Segmentation déterministe par quantiles RFM.
    Résultats stables, interprétables, pas de ML requis.
    """
    r_score = pd.qcut(df["recency"], q=3, labels=[3, 2, 1])   # moins = mieux
    f_score = pd.qcut(df["frequency"].rank(method="first"), q=3, labels=[1, 2, 3])
    m_score = pd.qcut(df["monetary"].rank(method="first"), q=3, labels=[1, 2, 3])
    rfm_score = r_score.astype(int) + f_score.astype(int) + m_score.astype(int)

    def assign_segment(score):
        if score >= 8:   return "CHAMPIONS"
        elif score >= 6: return "REGULIERS"
        elif score >= 4: return "A_RISQUE"
        else:            return "OCCASIONNELS"

    df["segment"] = rfm_score.apply(assign_segment)
    return df
```

**Solution 3 : `random_state` fixé pour la reproductibilité**

```python
# Si K-Means est quand même utilisé, fixer la graine :
KMeans(n_clusters=4, random_state=42, n_init=10)
```

**Effort :** 4 heures · **Risque de régression :** Faible

---

### C8 — Validation des données d'entrée ML

**Problème :** Aucune vérification des données avant leur utilisation dans les modèles. Valeurs aberrantes, nulls, données corrompues entrent silencieusement.

**Solution : Couche de validation avant tout entraînement**

```python
# app/ml/common.py — ajouter une fonction de validation
from dataclasses import dataclass
from typing import Optional

@dataclass
class DataQualityReport:
    is_valid: bool
    n_rows: int
    n_nulls: int
    n_outliers: int
    warnings: list
    blocking_issues: list

def validate_training_data(df, required_columns: list, min_rows: int) -> DataQualityReport:
    warnings = []
    blocking_issues = []

    # 1. Colonnes requises présentes ?
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        blocking_issues.append(f"Colonnes manquantes : {missing}")

    # 2. Volume suffisant ?
    if len(df) < min_rows:
        blocking_issues.append(f"Données insuffisantes : {len(df)} lignes (minimum : {min_rows})")

    # 3. Valeurs nulles excessives ?
    null_pct = df[required_columns].isnull().mean()
    for col, pct in null_pct.items():
        if pct > 0.3:
            warnings.append(f"Colonne '{col}' : {pct:.0%} de valeurs nulles")
        if pct > 0.7:
            blocking_issues.append(f"Colonne '{col}' inutilisable : {pct:.0%} de nulls")

    # 4. Valeurs aberrantes (montants négatifs, remises > 100%)
    if "montant_total" in df.columns:
        neg = (df["montant_total"] < 0).sum()
        if neg > 0:
            warnings.append(f"{neg} transactions avec montant négatif")
    if "remise_taux" in df.columns:
        invalid_discount = (df["remise_taux"] > 1.0).sum()
        if invalid_discount > 0:
            warnings.append(f"{invalid_discount} remises > 100%")

    return DataQualityReport(
        is_valid=len(blocking_issues) == 0,
        n_rows=len(df),
        n_nulls=df.isnull().sum().sum(),
        n_outliers=0,
        warnings=warnings,
        blocking_issues=blocking_issues
    )
```

**Effort :** 4–6 heures · **Risque de régression :** Nul (code additif)

---

### C9 — Feature Store non versionné

**Problème :** Si le schéma d'une table `fs_*` change, les modèles dépendants plantent silencieusement.

**Solution : Colonne `schema_version` + vérification à l'entraînement**

```sql
-- Ajouter à chaque table fs_*
ALTER TABLE fs_customer_rfm ADD COLUMN schema_version VARCHAR(10) DEFAULT '1.0';
ALTER TABLE fs_customer_credit_features ADD COLUMN schema_version VARCHAR(10) DEFAULT '1.0';
ALTER TABLE fs_transaction_features ADD COLUMN schema_version VARCHAR(10) DEFAULT '1.0';
```

```python
# app/ml/common.py
FEATURE_STORE_VERSIONS = {
    "fs_customer_rfm": "1.0",
    "fs_customer_credit_features": "1.0",
    "fs_transaction_features": "1.0",
}

def check_feature_store_version(table_name: str):
    expected = FEATURE_STORE_VERSIONS.get(table_name)
    actual = db.session.execute(
        text(f"SELECT schema_version FROM {table_name} LIMIT 1")
    ).scalar()
    if actual != expected:
        raise ValueError(
            f"Version du Feature Store incompatible : attendu {expected}, trouvé {actual}. "
            f"Relancer le pipeline ETL avant d'entraîner les modèles."
        )
```

**Effort :** 3 heures · **Risque de régression :** Faible

---

### C10 — Dérive des modèles non détectée

**Problème :** Un modèle entraîné en janvier est utilisé en juillet sans aucune alerte sur sa dégradation.

**Solution : Mécanisme de monitoring des prédictions**

**Étape 1 — Stocker la distribution des prédictions à l'entraînement :**
```python
# Dans register_model() — sauvegarder la distribution de référence
import json, numpy as np

def register_model(model_type, algorithm, metrics, ...):
    # ... code existant
    # Stocker la distribution des prédictions de référence
    if predictions_sample is not None:
        ref_distribution = {
            "mean": float(np.mean(predictions_sample)),
            "std": float(np.std(predictions_sample)),
            "p25": float(np.percentile(predictions_sample, 25)),
            "p75": float(np.percentile(predictions_sample, 75)),
            "trained_at": datetime.utcnow().isoformat()
        }
        ml_model.metrics_json = json.dumps({
            **json.loads(ml_model.metrics_json or "{}"),
            "reference_distribution": ref_distribution
        })
```

**Étape 2 — Vérification périodique de dérive :**
```python
def check_model_drift(model_type: str, current_predictions: list) -> dict:
    """Détecte si la distribution des prédictions a dérivé."""
    model = MLModel.query.filter_by(type=model_type, is_active=True).first()
    if not model: return {"drift_detected": False}

    metrics = json.loads(model.metrics_json or "{}")
    ref = metrics.get("reference_distribution")
    if not ref: return {"drift_detected": False}

    current_mean = np.mean(current_predictions)
    ref_mean = ref["mean"]
    ref_std = ref["std"]

    # Alerte si la moyenne actuelle dépasse 2 écarts-types de la référence
    z_score = abs(current_mean - ref_mean) / max(ref_std, 0.001)
    drift_detected = z_score > 2.0

    return {
        "drift_detected": drift_detected,
        "z_score": round(z_score, 2),
        "reference_mean": ref_mean,
        "current_mean": round(current_mean, 2),
        "recommendation": "Réentraîner le modèle" if drift_detected else "Modèle stable"
    }
```

**Exposer via endpoint :**
```python
GET /api/v1/analytics/ml/drift/<model_type>
→ {"drift_detected": true, "z_score": 2.8, "recommendation": "Réentraîner le modèle"}
```

**Effort :** 6–8 heures · **Risque de régression :** Faible

---

## PHASE 2 — CORRECTIONS MOYENNES (P2)
### Mois 2–3 : robustesse produit

---

### C11 — Pas de mode hors ligne

**Problème :** Connexion internet requise pour chaque vente. Coupures fréquentes = caisse bloquée.

**Solution : Progressive Web App (PWA) avec Service Worker**

**Architecture offline :**
```
Vente hors ligne → IndexedDB (navigateur) → Sync automatique quand connexion rétablie
```

**Étape 1 — Service Worker (vite-plugin-pwa) :**
```bash
npm install vite-plugin-pwa
```

```typescript
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts',
      manifest: {
        name: 'GesCom-BF',
        short_name: 'GesCom',
        theme_color: '#1a56db',
        display: 'standalone',
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          { urlPattern: /\/api\/v1\/products/, handler: 'CacheFirst' },
          { urlPattern: /\/api\/v1\/clients/, handler: 'CacheFirst' },
        ]
      }
    })
  ]
})
```

**Étape 2 — File d'attente des ventes hors ligne :**
```typescript
// hooks/useOfflineSales.ts
import { openDB } from 'idb'

const db = openDB('gescom-offline', 1, {
  upgrade(db) {
    db.createObjectStore('pending_sales', { keyPath: 'local_id', autoIncrement: true })
  }
})

export async function queueSaleOffline(sale: SalePayload) {
  const store = await db
  await (await store).add('pending_sales', { ...sale, queued_at: new Date().toISOString() })
}

export async function syncPendingSales(apiClient: AxiosInstance) {
  const store = await db
  const pending = await (await store).getAll('pending_sales')
  for (const sale of pending) {
    try {
      await apiClient.post('/api/v1/sales', sale)
      await (await store).delete('pending_sales', sale.local_id)
    } catch { break } // Arrêter si la connexion est perdue à nouveau
  }
}
```

**Indicateur visuel :** badge "Hors ligne — X ventes en attente de synchronisation" dans le header.

**Effort :** 3–5 jours · **Risque de régression :** Moyen

---

### C12 — Interface non mobile-first

**Problème :** Les vendeurs utilisent des smartphones. Un SPA React non optimisé mobile = adoption bloquée sur le terrain.

**Solution : Composants adaptatifs par contexte d'usage**

```typescript
// hooks/useBreakpoint.ts
export function useIsMobile() {
  return useMediaQuery("(max-width: 768px)")
}

// Pour les tables de données — version mobile = liste de cartes
function SalesTable({ sales }: Props) {
  const isMobile = useIsMobile()
  if (isMobile) return <SalesCardList sales={sales} />
  return <SalesDataTable sales={sales} />
}
```

**Priorité des pages à adapter :**
1. Page de vente (formulaire d'encaissement) — usage terrain quotidien
2. Dashboard vendeur — consulté sur smartphone
3. Module crédits — validation sur le terrain

**Effort :** 3–5 jours · **Risque de régression :** Faible

---

### C13 — Chiffrement des données sensibles au repos

**Problème :** Montants, scores de crédit, encours stockés en clair dans MySQL.

**Solution : Chiffrement au niveau applicatif pour les champs critiques**

```python
# app/utils/crypto.py
from cryptography.fernet import Fernet
import os, base64

_key = os.environ.get("FIELD_ENCRYPTION_KEY")
_fernet = Fernet(_key) if _key else None

def encrypt_field(value: str) -> str:
    if not _fernet or not value: return value
    return _fernet.encrypt(value.encode()).decode()

def decrypt_field(value: str) -> str:
    if not _fernet or not value: return value
    try:
        return _fernet.decrypt(value.encode()).decode()
    except Exception:
        return value  # Retourner la valeur brute si déchiffrement échoue

# Utilisation dans les modèles SQLAlchemy :
# Pour les champs les plus sensibles (encours_credit, score_credit)
# via SQLAlchemy TypeDecorator
from sqlalchemy import TypeDecorator, String

class EncryptedString(TypeDecorator):
    impl = String
    def process_bind_param(self, value, dialect):
        return encrypt_field(str(value)) if value else value
    def process_result_value(self, value, dialect):
        return decrypt_field(value) if value else value
```

**Effort :** 1 jour · **Risque de régression :** Moyen (tester toutes les requêtes sur les champs chiffrés)

---

### C14 — Point de défaillance unique (PythonAnywhere)

**Problème :** Backend + DB sur un seul hébergeur mutualisé. Indisponibilité PythonAnywhere = application totalement arrêtée.

**Solution progressive :**

**Niveau 1 (sans coût) : Page de maintenance statique**
- Héberger une page `maintenance.html` sur Netlify/Vercel (gratuit)
- En cas de panne, pointer le DNS vers cette page pour informer les utilisateurs

**Niveau 2 (faible coût) : Séparation base de données**
- Migrer MySQL vers PlanetScale ou Railway (plans gratuits disponibles)
- Le backend PythonAnywhere + la DB sont alors indépendants

**Niveau 3 (moyen terme) : Migration VPS**
```
Architecture cible :
VPS (DigitalOcean/Hetzner) → Nginx → Gunicorn Flask
                           → MySQL + Redis (Celery)
                           → Backups automatiques S3
```

**Effort :** Niveau 1 = 2 heures · Niveau 2 = 1 jour · Niveau 3 = 1 semaine

---

## PHASE 3 — ÉVOLUTIONS STRATÉGIQUES (P3)
### Mois 3–6 : vers un vrai SaaS

---

### C15 — Module de facturation / abonnement (SaaS complet)

**Pour que GesCom-BF soit un vrai SaaS**, il faut un cycle de vie commercial autonome.

**Architecture proposée :**

```
Inscription en ligne → Choix du plan → Paiement → Accès automatique
```

**Composants requis :**

| Composant | Solution recommandée | Coût |
|---|---|---|
| Paiement en ligne | CinetPay (Burkina Faso) ou Stripe (international) | Commission % |
| Gestion des abonnements | Table `subscriptions` + webhook paiement | Développement |
| Self-service onboarding | Formulaire d'inscription → création automatique structure + admin | Développement |
| Gestion des plans | Table `plans` (Basic/Pro/Enterprise) avec feature flags | Développement |

**Modèle de données :**
```sql
CREATE TABLE plans (
    id INT PRIMARY KEY,
    name VARCHAR(50),           -- 'BASIC', 'PRO', 'ENTERPRISE'
    max_branches INT,
    max_users INT,
    has_ml_module BOOLEAN,
    price_monthly_fcfa DECIMAL(10,2)
);

CREATE TABLE subscriptions (
    id INT PRIMARY KEY,
    structure_id INT REFERENCES structures(id),
    plan_id INT REFERENCES plans(id),
    status ENUM('TRIAL', 'ACTIVE', 'SUSPENDED', 'CANCELLED'),
    trial_ends_at DATETIME,
    current_period_ends_at DATETIME,
    created_at DATETIME DEFAULT NOW()
);
```

**Effort :** 2–3 semaines · **Impact business :** Transforme GesCom-BF en produit commercialisable

---

### C16/C18 — ✅ Monitoring et alerting applicatif — RÉSOLU

**Statut :** Sentry SDK est **implémenté** et s'active automatiquement si la variable d'environnement `SENTRY_DSN` est définie. L'endpoint `/health` est opérationnel. Le pipeline CI/CD (GitHub Actions) bloque si les 155 tests échouent.

**Ancienne description :** Aucune visibilité sur les erreurs en production, les temps de réponse, les modèles ML qui échouent.

**Solution : Sentry (free tier) + endpoint de santé**

```python
# app/__init__.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1,
    environment=os.environ.get("FLASK_ENV", "production")
)

# Endpoint de santé pour monitoring externe
@app.route("/health")
def health_check():
    try:
        db.session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "version": os.environ.get("APP_VERSION", "unknown"),
        "timestamp": datetime.utcnow().isoformat()
    }), 200 if db_status == "ok" else 503
```

**UptimeRobot (gratuit) :** pinger `/health` toutes les 5 minutes → alerte email si le service tombe.

**Effort :** 4 heures · **Risque de régression :** Nul

---

## ROADMAP DE MISE EN OEUVRE

```
PHASE P0 — RÉALISÉ (juillet 2026)
├── C1 : ✅ Score crédit SHA-256 → "INDETERMINATE" + message explicite
├── C2 : ✅ Audit log existait déjà (AuditLog.record())
├── C3 : ✅ Flask-Limiter 3.8.0 (memory://, sans Redis)
└── C5 : ✅ ML non-bloquant — threads Python + cron_train_all.py (PythonAnywhere Tasks)

PHASE P1 — RÉALISÉ (juillet 2026)
├── C7/C8 : ✅ K-Means k optimal Silhouette/Elbow + fallback quartiles
└── C18 : ✅ Sentry SDK optionnel + endpoint /health + CI 155 tests

PHASE P0 — À TRAITER (post-soutenance)
└── C4 : JWT → httpOnly cookies (4-6h, conflit frontend)

PHASES P1-P2 — AMÉLIORATIONS FUTURES
├── C6 : Script backup + procédure rollback
├── C9 : Versioning Feature Store
├── C10 : Détection dérive modèles
├── C11 : Validation données d'entrée ML
├── C12 : Interface mobile-first
├── C13 : Chiffrement champs sensibles
└── C14 : Séparation DB

PHASE P3 — ÉVOLUTIONS STRATÉGIQUES
├── C15 : Module facturation + self-service
└── C16 : Infrastructure redondante (VPS + PostgreSQL)
```

---

## RÉSUMÉ DE L'IMPACT ATTENDU

| Axe | Avant corrections | État actuel (v2, juillet 2026) | Cible future (VPS) |
|---|---|---|---|
| **Sécurité** | Brute-force possible, pas d'audit (erroné), score fictif | ✅ Rate limiting, AuditLog existait, score fictif supprimé | Données chiffrées, JWT httpOnly |
| **Fiabilité IA** | Score crédit fictif, ML bloquant, k=4 fixé | ✅ Score honnête, threads non-bloquants, k optimal Silhouette | Dérive détectée, qualité garantie |
| **Disponibilité** | Single point of failure | ✅ Sentry SDK + /health + CI 155 tests + cron quotidien | Infra redondante, PostgreSQL |
| **Tests** | ~93 tests | ✅ **155 tests** (127 ML unitaires + 17 intégration + 15 sécurité + 12 RBAC) | — |
| **Adoption** | Web only, connexion requise | Web only | Mobile, offline, self-service |
| **Modèle SaaS** | Web app hébergée | Web app robuste et défendable | SaaS facturable |

---

*Document généré le 23 juin 2026 — GesCom-BF Plan Correctif v1.0*  
*Mis à jour le 1er juillet 2026 — v2 post-corrections : statuts réalisés propagés.*
