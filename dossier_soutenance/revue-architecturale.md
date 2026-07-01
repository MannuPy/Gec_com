# Revue Architecturale Complète — GesCom-BF
## Ce que je referais, modifierais, supprimerais ou ajouterais domaine par domaine

---

> **Dernière mise à jour :** 1er juillet 2026 — conformité code v2 post-corrections soutenance.

---

> **Contexte :** PythonAnywhere comme contrainte d'hébergement fixe. Pas de Redis, pas de Celery persistant (supprimés), pas de WebSockets natifs, MySQL uniquement. SSE désactivé (`DISABLE_SSE=true`), fallback polling. Chaque décision tient compte de cette réalité.
>
> **Légende importance :**
> - 🔴 **Critique** — change la fiabilité ou la sécurité fondamentale
> - 🟠 **Important** — améliore significativement la qualité
> - 🟡 **Mineur** — confort, lisibilité, performance marginale

---

## 1. ARCHITECTURE BACKEND (Flask)

### Ce que je garderais
- **Flask 3.x** — léger, bien adapté à PythonAnywhere WSGI, parfait pour une API REST
- **Architecture en Blueprints** — bonne séparation des préoccupations, facilite les tests
- **SQLAlchemy 2.x** — ORM mature, protection injection SQL, portabilité
- **Pattern Routes → Services → Modèles** — propre, testable

### Ce que je modifierais

| Modification | Importance | Pourquoi |
|---|---|---|
| Séparer `config.py` en `config/base.py`, `config/production.py`, `config/testing.py` | 🟠 Important | Évite les erreurs de config entre environnements |
| Ajouter `flask-compress` pour la compression GZIP des réponses API | 🟠 Important | -60% de taille des réponses JSON sur 3G |
| Standardiser le format d'erreur API en un seul objet `{"error": {"code": "...", "message": "...", "field": "..."}}` | 🟠 Important | Le frontend gère les erreurs de façon uniforme |
| Remplacer `marshmallow` par `Pydantic v2` | 🟡 Mineur | Validation plus rapide, meilleure intégration TypeScript (génération de types auto) |
| Ajouter middleware de logging structuré (JSON) | 🟡 Mineur | Logs lisibles par Sentry et autres outils |

### Ce que je supprimerais
- **Le stub Celery complet** (`task.delay()` avec fallback sync) — ✅ SUPPRIMÉ. Remplacé par threads Python natifs pour l'entraînement ML à la demande + `scripts/cron_train_all.py` planifié via PythonAnywhere Tasks. Plus honnête et plus stable.
- **Les imports conditionnels de sklearn dispersés dans chaque module ML** — centraliser dans `app/ml/backend.py` un seul flag `HAS_SKLEARN`.

### Ce que j'ajouterais

```python
# app/middleware/request_logger.py — AJOUT CRITIQUE
import time, json
from flask import g, request

def setup_request_logging(app):
    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        duration_ms = round((time.time() - g.start_time) * 1000, 2)
        log = {
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "user_id": getattr(g, 'current_user_id', None),
            "branch_id": getattr(g, 'current_branch_id', None),
            "ip": request.remote_addr,
        }
        app.logger.info(json.dumps(log))
        return response
```

```python
# app/utils/response.py — Format de réponse standardisé
def success(data, message=None, status=200, meta=None):
    body = {"success": True, "data": data}
    if message: body["message"] = message
    if meta: body["meta"] = meta  # pagination, totaux
    return jsonify(body), status

def error(code: str, message: str, field: str = None, status: int = 400):
    body = {"success": False, "error": {"code": code, "message": message}}
    if field: body["error"]["field"] = field
    return jsonify(body), status

# Utilisation uniforme dans tous les blueprints :
# return success(schema.dump(obj), status=201)
# return error("CREDIT_LIMIT_EXCEEDED", "Plafond de crédit dépassé", field="montant", status=422)
```

---

## 2. BASE DE DONNÉES

### Ce que je garderais
- **MySQL 8** — seul choix viable sur PythonAnywhere, bien maîtrisé
- **Structure multi-branches** avec `branch_id` sur toutes les tables transactionnelles
- **Soft delete** avec `is_active` sur les entités critiques (produits, clients)
- **`created_at` / `updated_at`** sur toutes les tables

### Ce que je modifierais

**🔴 Ajouter des index manquants critiques :**
```sql
-- Ces requêtes sont exécutées des milliers de fois — sans index, tout ralentit
CREATE INDEX idx_sales_branch_date ON sales(branch_id, created_at);
CREATE INDEX idx_sale_items_product ON sale_items(product_id);
CREATE INDEX idx_credits_client_status ON credits(client_id, statut);
CREATE INDEX idx_stock_movements_branch_product ON stock_movements(branch_id, product_id, created_at);
CREATE INDEX idx_predictions_type_entity ON predictions(prediction_type, entity_id, created_at);
CREATE INDEX idx_audit_logs_user_date ON audit_logs(user_id, created_at);

-- Index composites pour les filtres dashboard (branch + période)
CREATE INDEX idx_sales_branch_date_status ON sales(branch_id, created_at, statut);
```

**🟠 Ajouter les colonnes manquantes aux tables existantes :**
```sql
-- Table sales — colonnes importantes absentes
ALTER TABLE sales
  ADD COLUMN payment_method ENUM('CASH','ORANGE_MONEY','WAVE','MOOV','CREDIT') DEFAULT 'CASH',
  ADD COLUMN payment_status ENUM('PENDING','PAID','PARTIAL') DEFAULT 'PAID',
  ADD COLUMN payment_reference VARCHAR(100) NULL,  -- référence transaction mobile money
  ADD COLUMN notes TEXT NULL;

-- Table clients — pour le scoring et les notifications
ALTER TABLE clients
  ADD COLUMN telephone VARCHAR(20) NULL,
  ADD COLUMN whatsapp_opt_in BOOLEAN DEFAULT FALSE,
  ADD COLUMN sms_opt_in BOOLEAN DEFAULT TRUE,
  ADD COLUMN secteur_activite VARCHAR(100) NULL;  -- pour le benchmark

-- Table products — pour le QR et la gestion avancée
ALTER TABLE products
  ADD COLUMN qr_code_url VARCHAR(500) NULL,
  ADD COLUMN unite_mesure VARCHAR(20) DEFAULT 'unité',
  ADD COLUMN fournisseur_principal VARCHAR(100) NULL;
```

**🟠 Revoir le schéma du Feature Store :**
```sql
-- Ajouter versioning et metadata
ALTER TABLE fs_customer_rfm
  ADD COLUMN schema_version VARCHAR(10) DEFAULT '1.0',
  ADD COLUMN computed_at DATETIME DEFAULT NOW(),
  ADD COLUMN data_quality_score FLOAT DEFAULT 1.0;  -- 0 à 1, fiabilité de la feature

-- Table de suivi des recalculs Feature Store
CREATE TABLE feature_store_runs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  table_name VARCHAR(100) NOT NULL,
  schema_version VARCHAR(10) NOT NULL,
  rows_computed INT,
  duration_seconds FLOAT,
  status ENUM('SUCCESS','PARTIAL','FAILED'),
  error_message TEXT NULL,
  started_at DATETIME,
  finished_at DATETIME
);
```

### Ce que je supprimerais
- **Les colonnes redondantes** — vérifier qu'aucun champ n'est calculable à partir d'autres (ex. si `solde_restant = montant_initial - SUM(paiements)`, ne pas le stocker sauf si c'est une colonne calculée avec trigger)
- **Les `VARCHAR(500)` sur des champs qui n'ont jamais besoin de plus de 50 caractères** — gaspillage d'espace d'index

### Ce que j'ajouterais

**🔴 Table `audit_logs` (absente actuellement) :**
```sql
CREATE TABLE audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id),
  action VARCHAR(100) NOT NULL,        -- 'CREDIT_SETTLE', 'SALE_DELETE', 'USER_CREATE'
  resource_type VARCHAR(50) NOT NULL,  -- 'credit', 'sale', 'user'
  resource_id INT NULL,
  branch_id INT NULL REFERENCES branches(id),
  old_value_json JSON NULL,
  new_value_json JSON NULL,
  ip_address VARCHAR(45) NULL,
  user_agent VARCHAR(255) NULL,
  created_at DATETIME DEFAULT NOW(),
  INDEX idx_audit_resource (resource_type, resource_id),
  INDEX idx_audit_user_date (user_id, created_at),
  INDEX idx_audit_branch_date (branch_id, created_at)
) ENGINE=InnoDB;
```

**🟠 Table `notifications` pour le centre de notifications in-app :**
```sql
CREATE TABLE notifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id),
  type VARCHAR(50) NOT NULL,          -- 'STOCK_ALERT', 'CREDIT_OVERDUE', 'ML_DRIFT'
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  action_url VARCHAR(500) NULL,       -- lien vers la page concernée
  is_read BOOLEAN DEFAULT FALSE,
  delivered_via SET('IN_APP','WHATSAPP','SMS'),
  created_at DATETIME DEFAULT NOW(),
  read_at DATETIME NULL,
  INDEX idx_notif_user_unread (user_id, is_read, created_at)
);
```

**🟡 Vues SQL matérialisées pour les rapports fréquents :**
```sql
-- Vue mensuelle des KPIs par branche (recalculée par cron)
CREATE TABLE mv_branch_monthly_kpis (
  branch_id INT NOT NULL,
  mois DATE NOT NULL,
  ca_total DECIMAL(15,2),
  nb_transactions INT,
  panier_moyen DECIMAL(12,2),
  taux_marge DECIMAL(5,2),
  nb_clients_actifs INT,
  nb_nouveaux_clients INT,
  computed_at DATETIME DEFAULT NOW(),
  PRIMARY KEY (branch_id, mois)
);
```

---

## 3. AUTHENTIFICATION & SÉCURITÉ

### Ce que je garderais
- **Flask-JWT-Extended** — mature, bien intégré
- **Structure des rôles et permissions** — le système RBAC est bien pensé
- **Le décorateur `@require_permission`** — élégant, réutilisable

### Ce que je modifierais

**🔴 JWT en httpOnly Cookie plutôt que Authorization header :**
```python
# app/blueprints/auth/routes.py
from flask import make_response

@bp.post("/login")
@limiter.limit("5 per minute")
def login():
    # ... validation email/password
    access_token = create_access_token(identity=user.id, additional_claims={
        "role": user.role.name,
        "branch_ids": [b.id for b in user.branches]
    })
    refresh_token = create_refresh_token(identity=user.id)

    resp = make_response(jsonify({
        "user": UserSchema().dump(user),
        "message": "Connexion réussie"
    }))
    resp.set_cookie("access_token", access_token,
        httponly=True, secure=True, samesite="Strict", max_age=3600)
    resp.set_cookie("refresh_token", refresh_token,
        httponly=True, secure=True, samesite="Strict", max_age=86400 * 30)
    return resp

@bp.post("/logout")
def logout():
    resp = make_response(jsonify({"message": "Déconnecté"}))
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    return resp
```

**🔴 Rotation automatique du refresh token :**
```python
# À chaque utilisation du refresh token, émettre un nouveau
@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    # Invalider l'ancien refresh token (token blacklist en DB)
    jti = get_jwt()["jti"]
    blacklist = TokenBlacklist(jti=jti, expires_at=datetime.utcnow() + timedelta(days=30))
    db.session.add(blacklist)
    # Émettre de nouveaux tokens
    new_access = create_access_token(identity=user_id)
    new_refresh = create_refresh_token(identity=user_id)
    # ... set cookies
```

**🟠 Row-Level Security automatique :**
```python
# app/middleware/branch_isolation.py
from flask import g
from functools import wraps

def with_branch_filter(query_model):
    """
    Injecte automatiquement le filtre branch_id sur toutes les requêtes.
    Empêche un utilisateur d'accéder aux données d'une autre branche.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = g.current_user
            if user.role.name in ["SUPER_ADMIN", "ADMIN"]:
                g.branch_filter = None  # Pas de filtre
            else:
                g.branch_filter = [b.id for b in user.branches]
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Dans chaque service :
def get_query_with_branch_filter(model):
    query = model.query
    if g.branch_filter is not None:
        query = query.filter(model.branch_id.in_(g.branch_filter))
    return query
```

### Ce que je supprimerais
- **La permission wildcard `"*"` comme seul mécanisme super-admin** — trop binaire. Ajouter un niveau intermédiaire "STRUCTURE_ADMIN" avec accès à plusieurs branches mais pas à l'administration globale.
- **Les tokens JWT longs sans rotation** — dangereux si compromis.

### Ce que j'ajouterais

**🔴 Table `token_blocklist` des tokens révoqués ✅ IMPLÉMENTÉE :**
```sql
-- Déjà en production (migration Alembic appliquée)
-- Nom exact : token_blocklist (pas token_blacklist)
CREATE TABLE token_blocklist (
  id INT AUTO_INCREMENT PRIMARY KEY,
  jti VARCHAR(36) NOT NULL UNIQUE,  -- JWT ID
  user_id VARCHAR(36) NOT NULL,
  created_at DATETIME DEFAULT NOW(),
  expires_at DATETIME NOT NULL,
  INDEX idx_blocklist_jti (jti),
  INDEX idx_blocklist_expires (expires_at)  -- Pour le nettoyage cron
);
-- Remplace Redis pour la révocation JWT — Flask-Limiter 3.8.0 utilise storage_uri="memory://"
```

**🟠 OTP par SMS pour les opérations sensibles :**
```python
# Pas pour chaque login — seulement pour les actions à fort enjeu :
# - Remboursement > 100,000 FCFA
# - Suppression d'un utilisateur
# - Modification du plafond de crédit d'un client

@bp.post("/credits/settle/<int:credit_id>")
@require_permission("credits.settle")
@require_otp_if_above(threshold=100_000, amount_field="montant")
def settle_credit(credit_id):
    ...
```

**🟡 Session device tracking :**
```sql
CREATE TABLE user_sessions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id),
  device_fingerprint VARCHAR(255),  -- hash user-agent + IP + écran
  device_label VARCHAR(100),         -- "Samsung Galaxy A32 - Burkina"
  last_seen DATETIME,
  is_trusted BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT NOW()
);
-- Permet d'afficher "Appareils connectés" dans les paramètres utilisateur
```

---

## 4. MODULE VENTES

### Ce que je garderais
- La logique de transaction atomique (vente + mise à jour stock en une transaction)
- Le calcul des remises et du montant total
- L'historique des ventes avec filtres

### Ce que je modifierais

**🟠 Ajouter le mode de paiement comme champ de première classe :**
```python
# Ce n'est pas un champ optionnel — c'est central pour la compta
class SaleSchema(ma.Schema):
    payment_method = ma.fields.String(
        required=True,
        validate=ma.validate.OneOf(["CASH", "ORANGE_MONEY", "WAVE", "MOOV", "CREDIT", "CHEQUE"])
    )
    payment_reference = ma.fields.String(load_default=None)  # N° transaction mobile money
    client_id = ma.fields.Integer(load_default=None)  # Vente anonyme autorisée
```

**🟠 Reçu numérique généré automatiquement :**
```python
# Après chaque vente validée, générer et envoyer le reçu
@bp.post("/")
def create_sale():
    # ... logique existante
    sale = SaleService.create(data)
    db.session.commit()

    # Reçu asynchrone (ne bloque pas la réponse)
    if sale.client and sale.client.telephone:
        threading.Thread(
            target=send_whatsapp_receipt,
            args=(sale,),
            daemon=True
        ).start()

    return success(SaleSchema().dump(sale), status=201)
```

**🟡 Numéro de référence lisible (pas juste l'ID) :**
```python
# Au lieu de : sale.id = 1247
# Générer : sale.reference = "VTE-2026-001247"
def generate_reference(branch_code: str, year: int, sequence: int) -> str:
    return f"VTE-{year}-{str(sequence).zfill(6)}"
# Affiché sur le reçu, cherchable, reconnaissable par le client
```

### Ce que je supprimerais
- Les ventes sans `client_id` obligatoire sur les grandes transactions (> seuil configurable) — pour l'analytique, une vente anonyme n'apprend rien sur la clientèle.

### Ce que j'ajouterais

**🟠 Ventes en mode hors ligne avec file de synchronisation :**
```python
# Endpoint d'acceptation des ventes offline
@bp.post("/bulk-sync")
@require_permission("sales.create")
def bulk_sync_offline_sales():
    """
    Reçoit un tableau de ventes créées hors ligne.
    Déduplique par client_local_id, valide chacune, et retourne le résultat.
    """
    sales_data = request.json.get("sales", [])
    results = []
    for sale_data in sales_data:
        local_id = sale_data.pop("local_id", None)
        try:
            sale = SaleService.create(sale_data)
            db.session.commit()
            results.append({"local_id": local_id, "server_id": sale.id, "status": "synced"})
        except Exception as e:
            db.session.rollback()
            results.append({"local_id": local_id, "status": "error", "message": str(e)})
    return success(results)
```

**🟡 Annulation de vente avec motif obligatoire + audit :**
```python
@bp.delete("/<int:sale_id>")
@require_permission("sales.delete")
@audit("SALE_CANCEL", "sale")
def cancel_sale(sale_id):
    motif = request.json.get("motif")
    if not motif or len(motif) < 10:
        return error("MOTIF_REQUIRED", "Un motif d'annulation de minimum 10 caractères est requis")
    # ... annulation + remise en stock
```

---

## 5. MODULE STOCKS

### Ce que je garderais
- Le suivi des mouvements avec `type` (entrée/sortie/ajustement)
- Les alertes sur `seuil_min`
- L'historique des mouvements par produit

### Ce que je modifierais

**🟠 Alertes stock proactives par WhatsApp/SMS (pas juste dans l'interface) :**
```python
# scripts/check_stock_alerts.py — lancé par cron PythonAnywhere toutes les heures
def check_and_notify_stock_alerts():
    critical = db.session.execute(text("""
        SELECT p.name, s.quantite, p.seuil_min, b.name as branch_name,
               m.telephone as manager_phone
        FROM stocks s
        JOIN products p ON s.product_id = p.id
        JOIN branches b ON s.branch_id = b.id
        JOIN users m ON b.manager_id = m.id
        WHERE s.quantite <= p.seuil_min
        AND s.alert_sent_at < DATE_SUB(NOW(), INTERVAL 6 HOUR)  -- max 1 alerte/6h
    """)).fetchall()

    for row in critical:
        send_whatsapp_message(
            row.manager_phone,
            "stock_alert",
            [row.name, str(row.quantite), row.branch_name]
        )
        # Marquer l'alerte comme envoyée
        db.session.execute(text(
            "UPDATE stocks SET alert_sent_at = NOW() WHERE ..."
        ))
```

**🟡 Mouvements de stock avec `raison` structurée :**
```python
class StockMovementReason(enum.Enum):
    SALE = "VENTE"
    PURCHASE = "ACHAT_FOURNISSEUR"
    RETURN = "RETOUR_CLIENT"
    LOSS = "PERTE_CASSE"
    INVENTORY = "INVENTAIRE"
    TRANSFER = "TRANSFERT_BRANCHE"
    ADJUSTMENT = "AJUSTEMENT_MANUEL"
# Actuellement tout est dans un champ texte libre — difficile à analyser
```

### Ce que j'ajouterais

**🟠 Transferts inter-branches avec validation :**
```python
# Une branche peut demander du stock à une autre branche
# Workflow : DEMANDE → APPROUVEE → EN_TRANSIT → RECUE

class StockTransfer(db.Model):
    source_branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"))
    target_branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    quantite_demandee = db.Column(db.Integer)
    quantite_envoyee = db.Column(db.Integer, nullable=True)
    statut = db.Column(db.Enum("DEMANDE","APPROUVEE","REFUSEE","EN_TRANSIT","RECUE"))
    notes = db.Column(db.Text, nullable=True)
```

**🟡 Inventaire périodique avec écart automatique :**
```python
# L'utilisateur fait son inventaire physique → le système calcule l'écart
class Inventory(db.Model):
    branch_id, date_inventaire, statut = ...

class InventoryItem(db.Model):
    inventory_id, product_id = ...
    quantite_theorique = db.Column(db.Integer)  # selon le système
    quantite_comptee = db.Column(db.Integer)    # saisie par l'agent
    ecart = db.Column(db.Integer)               # calculé automatiquement
    valeur_ecart = db.Column(db.Numeric(12,2))  # en FCFA
```

---

## 6. MODULE CRÉDITS

### Ce que je garderais
- Le workflow de remboursement partiel/total
- L'historique des paiements par crédit
- Le calcul du solde restant

### Ce que je modifierais

**🔴 Retirer le scoring SHA-256 du flux décisionnel :**
```python
# Remplacer l'affichage du score fictif par l'état réel des données
def get_credit_profile(client_id: int) -> dict:
    history = get_repayment_history(client_id)
    if len(history) < 3:
        return {
            "scoring_available": False,
            "message": "Historique insuffisant — minimum 3 crédits remboursés requis",
            "raw_stats": {
                "nb_credits": len(history),
                "encours_actuel": get_current_balance(client_id)
            }
        }
    # Sinon, scoring ML si disponible
    return CreditScoring().score(client_id)
```

**🟠 Plafond de crédit configurable par client (pas global) :**
```python
# Actuellement le plafond est global ou par rôle
# Ajouter un champ sur le client :
ALTER TABLE clients ADD COLUMN credit_limit DECIMAL(12,2) DEFAULT 50000;
ALTER TABLE clients ADD COLUMN credit_limit_set_by INT REFERENCES users(id);
ALTER TABLE clients ADD COLUMN credit_limit_set_at DATETIME;
# Piste d'audit : qui a autorisé ce plafond et quand
```

**🟠 Relances automatiques des crédits en retard :**
```python
# scripts/credit_reminders.py — cron PythonAnywhere à 8h chaque matin
def send_daily_credit_reminders():
    overdue = Credit.query.filter(
        Credit.date_echeance < date.today(),
        Credit.statut == "EN_COURS",
        Credit.derniere_relance < date.today() - timedelta(days=3)  # max 1 relance / 3 jours
    ).all()

    for credit in overdue:
        if credit.client.telephone:
            send_whatsapp_message(credit.client.telephone, "credit_overdue", [
                f"{credit.solde_restant:,.0f}",
                credit.date_echeance.strftime("%d/%m/%Y"),
                credit.branch.name
            ])
            credit.derniere_relance = date.today()
    db.session.commit()
```

### Ce que je supprimerais
- La distinction `bon_payeur` binaire dans le scoring — trop simpliste. Remplacer par une note de 0 à 5 avec description narrative.

### Ce que j'ajouterais

**🟠 Garanties sur les crédits :**
```sql
CREATE TABLE credit_guarantees (
  id INT AUTO_INCREMENT PRIMARY KEY,
  credit_id INT NOT NULL REFERENCES credits(id),
  type ENUM('BIEN_PHYSIQUE','CAUTION_MORALE','DEPOT_ESPECES','AUTRE'),
  description TEXT NOT NULL,
  valeur_estimee DECIMAL(12,2) NULL,
  created_by INT REFERENCES users(id),
  created_at DATETIME DEFAULT NOW()
);
```

**🟡 Échelonnement automatique :**
```python
# Générer automatiquement les échéances lors de l'octroi
def create_repayment_schedule(credit_id, nb_echeances, premiere_echeance):
    credit = Credit.query.get(credit_id)
    montant_par_echeance = credit.montant / nb_echeances
    for i in range(nb_echeances):
        echeance = CreditEcheance(
            credit_id=credit_id,
            numero=i + 1,
            montant_du=montant_par_echeance,
            date_echeance=premiere_echeance + relativedelta(months=i),
            statut="EN_ATTENTE"
        )
        db.session.add(echeance)
```

---

## 7. MODULE REMBOURSEMENTS

### Ce que je garderais
- Le workflow approbation/rejet avec motif
- La distinction AVOIR_EMIS / ANNULEE
- Le polling automatique des remboursements en attente

### Ce que je modifierais

**🟠 Délai maximum de traitement configurable :**
```python
# Un remboursement en attente depuis > X jours génère une alerte au manager
REFUND_SLA_HOURS = int(os.environ.get("REFUND_SLA_HOURS", 48))

# Dans le cron PythonAnywhere :
overdue_refunds = Refund.query.filter(
    Refund.statut == "EN_ATTENTE",
    Refund.created_at < datetime.utcnow() - timedelta(hours=REFUND_SLA_HOURS)
).all()
# Notifier le manager par WhatsApp
```

**🟡 Photo du produit retourné :**
```python
# Sur mobile, le vendeur peut prendre une photo du produit défectueux
# Stockée dans un bucket S3 ou Cloudinary (gratuit jusqu'à 25GB)
@bp.post("/<int:refund_id>/photo")
def upload_refund_photo(refund_id):
    file = request.files.get("photo")
    url = upload_to_cloudinary(file, folder="refunds")
    refund.photo_url = url
    db.session.commit()
    return success({"photo_url": url})
```

### Ce que je supprimerais
- Rien — le module est bien conçu dans l'ensemble.

### Ce que j'ajouterais

**🟡 Statistiques de qualité produit :**
```python
# Rapport mensuel : top produits les plus retournés
GET /api/v1/refunds/analytics?branch_id=1&periode=30j
→ {
    "top_returned_products": [{"product": "...", "count": 12, "taux_retour": "3.2%"}],
    "taux_global": "1.8%",
    "raisons_principales": ["produit_defectueux", "erreur_livraison"]
  }
```

---

## 8. MODULE COMPTABILITÉ

### Ce que je garderais
- La vue journal de caisse avec solde cumulatif
- Les agrégats recettes/dépenses par période
- La comparaison par branches

### Ce que je modifierais

**🟠 Plan comptable simplifié adapté au contexte SYSCOHADA :**
```python
# Catégoriser les opérations selon les classes SYSCOHADA simplifiées
COMPTE_CLASSES = {
    "RECETTE_VENTE": {"code": "7011", "libelle": "Ventes de marchandises"},
    "RECETTE_CREDIT": {"code": "7021", "libelle": "Recouvrement créances"},
    "DEPENSE_ACHAT": {"code": "6011", "libelle": "Achats de marchandises"},
    "DEPENSE_SALAIRE": {"code": "6611", "libelle": "Salaires et traitements"},
    "DEPENSE_LOYER": {"code": "6222", "libelle": "Loyers"},
    "DEPENSE_CHARGE": {"code": "6098", "libelle": "Autres charges"},
}
# Permet à un comptable de faire le lien avec la vraie comptabilité
```

**🟠 Export au format comptable standard (CSV SYSCOHADA) :**
```python
@bp.get("/export/syscohada")
@require_permission("compta.export")
def export_syscohada():
    """
    Exporte les opérations dans un format importable par les logiciels de compta
    utilisés par les experts-comptables burkinabè (Saari, Ciel Compta).
    """
    # Format : Date;Numéro pièce;Compte;Libellé;Débit;Crédit
    ...
```

### Ce que j'ajouterais

**🟠 Gestion des dépenses opérationnelles :**
```python
# Actuellement seules les recettes sont automatiques
# Les dépenses doivent pouvoir être saisies manuellement
class OperationalExpense(db.Model):
    branch_id, amount, category, description = ...
    payment_method = ...
    justificatif_url = ...  # Photo de la facture
    approved_by = ...       # Workflow validation
```

**🟡 Prévision budgétaire mensuelle :**
```python
# Le manager fixe un budget mensuel → comparaison réel vs budget
class MonthlyBudget(db.Model):
    branch_id, mois = ...
    budget_ca = db.Column(db.Numeric(15,2))
    budget_depenses = db.Column(db.Numeric(15,2))
    notes = db.Column(db.Text, nullable=True)
# → Afficher "Vous avez atteint 73% de votre objectif CA ce mois"
```

---

## 9. MODULE RAPPORTS

### Ce que je garderais
- Les exports PDF et XLSX
- Le tableau de bord dashboard principal
- La comparaison entre branches (RadarChart)

### Ce que je modifierais

**🟠 SSE remplacé par polling intelligent pour PythonAnywhere ✅ IMPLÉMENTÉ (`DISABLE_SSE=true`, fallback polling) :**
```python
# SSE (Server-Sent Events) est problématique sur PythonAnywhere shared hosting
# (connexions longues bloquent les workers WSGI)
# Remplacer par polling toutes les 30 secondes avec ETag pour éviter les transferts inutiles

@bp.get("/dashboard/realtime")
def dashboard_realtime():
    data = compute_dashboard_realtime()
    data_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    if request.headers.get("If-None-Match") == data_hash:
        return "", 304  # Pas changé — zéro transfert de données

    response = jsonify(data)
    response.headers["ETag"] = data_hash
    response.headers["Cache-Control"] = "no-cache"
    return response

# Frontend — polling avec ETag
# setInterval(() => refetch avec ETag header, 30_000)
```

**🟠 Rapports planifiables et reçus par email/WhatsApp :**
```python
# Le manager configure : "Envoie-moi le rapport hebdomadaire chaque lundi à 8h"
class ReportSchedule(db.Model):
    user_id, branch_id = ...
    report_type = db.Column(db.Enum("DAILY","WEEKLY","MONTHLY"))
    delivery_channel = db.Column(db.Enum("WHATSAPP","SMS","EMAIL"))
    day_of_week = db.Column(db.Integer, nullable=True)  # 0=lundi
    time_hhmm = db.Column(db.String(5), default="08:00")
    is_active = db.Column(db.Boolean, default=True)
# → Cron PythonAnywhere génère et envoie selon le planning
```

### Ce que je supprimerais
- **La génération PDF lourde pour les rapports simples** — utiliser des tableaux HTML bien mis en page et laisser le navigateur imprimer en PDF (`window.print()` avec CSS `@media print`). Plus rapide, pas de dépendance ReportLab pour les cas simples.

### Ce que j'ajouterais

**🟡 Dashboard comparatif temporel :**
```python
# Comparer automatiquement avec la même période l'an passé
GET /api/v1/reports/dashboard?branch_id=1&from=2026-01-01&to=2026-06-30&compare_previous=true
→ {
    "current_period": {"ca": 5_200_000},
    "previous_period": {"ca": 4_100_000},
    "evolution_pct": +26.8
  }
```

---

## 10. MODULE ANALYTIQUE & ML

### Ce que je garderais
- Le registre de modèles (`ml_models` + `predictions`)
- La dégradation gracieuse (fallback si sklearn indisponible)
- La structure Feature Store (à améliorer, mais le concept est bon)
- ABC/XYZ — l'algorithme est correct et utile

### Ce que je modifierais

**🔴 Entraînement ML → Scripts cron nocturnes (plus de train-on-demand bloquant) ✅ IMPLÉMENTÉ :**
```python
# scripts/nightly_ml.py — exécuté par PythonAnywhere Scheduled Tasks à 2h AM
MODELS_TO_TRAIN = [
    ("demand_forecast", DemandForecast),
    ("credit_scoring", CreditScoring),
    ("anomaly_detection", AnomalyDetection),
    ("rfm_segmentation", RFMSegmentation),
]

with app.app_context():
    for model_name, ModelClass in MODELS_TO_TRAIN:
        try:
            t0 = time.time()
            result = ModelClass().train()
            duration = round(time.time() - t0, 1)
            log_training_run(model_name, "SUCCESS", duration, result.get("metrics"))
        except Exception as e:
            log_training_run(model_name, "FAILED", 0, {"error": str(e)})
            sentry_sdk.capture_exception(e)
```

**🔴 Scoring crédit — supprimer le fallback SHA-256, afficher "données insuffisantes" ✅ IMPLÉMENTÉ :**
Fallback SHA-256 supprimé — le système retourne "données insuffisantes" si l'historique est trop court.

**🟠 SHAP pour l'explicabilité du scoring crédit ✅ IMPLÉMENTÉ :**
```python
# shap lib (TreeExplainer) — endpoint /analytics/credit-scores/<id>/explain
import shap

def explain_credit_score(customer_id: int) -> dict:
    model = _load_active_rf_model()
    features = _get_customer_features(customer_id)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(features)
    # Résultats exposés via /analytics/credit-scores/<id>/explain
```

**🟠 Prévision demande — variables africaines ✅ IMPLÉMENTÉES (`/analytics/african-context`) :**
```python
# Saison des pluies, Tabaski, Ramadan, rentrée scolaire, jours de marché — data_confidence inclus
def _build_features(df):
    df["is_tabaski_period"] = df["date"].apply(is_tabaski_period)
    df["is_ramadan"] = df["date"].apply(is_ramadan)
    df["is_rainy_season"] = df["date"].dt.month.isin([6,7,8,9]).astype(int)
    df["is_school_start"] = ((df["date"].dt.month==9) & (df["date"].dt.day<=20)).astype(int)
    df["is_payday_week"] = (df["date"].dt.day >= 25).astype(int)
    return df
```

**🟠 Rapport de qualité des données avant chaque entraînement :**
```python
# Afficher dans l'interface : "Dernière évaluation ML — 23 juin 2026 à 2h15"
# "Qualité des données : 94% (47 valeurs nulles corrigées, 3 aberrations exclues)"
```

### Ce que je supprimerais
- **L'endpoint `POST /ml/train` en deux versions (URL param + JSON body)** — garder seulement la version JSON body. La duplication crée de la confusion.
- **Le calcul CLV dans le endpoint analytics** — le sortir dans un service dédié `CLVService` avec sa propre logique et ses propres tests.

### Nouveaux modules ML ajoutés (tous ✅ IMPLÉMENTÉS)
- **Market Basket Analysis** : algorithme Apriori (mlxtend), endpoint `/analytics/basket`
- **Price Elasticity** : pandas, endpoint `/analytics/price-elasticity`
- **Churn Probability** : Logistic Regression, endpoint `/analytics/churn-risk`
- **African Context Indicators** : saisonnalité BF, endpoint `/analytics/african-context`
- **K-optimal RFM** : méthode Silhouette/Elbow, endpoint `/analytics/rfm-segments/evaluate-k`
- **SHAP Explicabilité crédit** : `shap.TreeExplainer`, endpoint `/analytics/credit-scores/<id>/explain`
- **`data_confidence`** dans les prévisions de demande

### Ce que j'ajouterais

**🟠 Détection de dérive automatique (drift monitoring) :**
```python
# Après chaque batch de prédictions nocturnes, comparer avec le modèle de référence
def check_drift_after_training(model_type: str, new_predictions: list):
    ref_distribution = get_reference_distribution(model_type)
    current_mean = np.mean(new_predictions)
    z = abs(current_mean - ref_distribution["mean"]) / ref_distribution["std"]
    if z > 2.0:
        notify_admin(f"DRIFT DÉTECTÉ sur {model_type} — réentraînement recommandé")
```

**🟠 Score de confiance affiché sur chaque prédiction :**
```python
# Toute prédiction exposée à l'utilisateur doit indiquer sa fiabilité
{
  "customer_id": 42,
  "score": 67,
  "risk_level": "MOYEN",
  "confidence": 0.82,          # 82% de confiance
  "data_points_used": 15,      # basé sur 15 transactions
  "model_age_days": 3,         # modèle entraîné il y a 3 jours
  "explanation": "Client régulier avec 2 retards mineurs sur 15 crédits"
}
```

**🟡 Dashboard de santé des modèles ML (pour l'admin) :**
```
GET /api/v1/analytics/ml/health
→ {
    "models": [
      {"type": "demand_forecast", "last_trained": "2026-06-23T02:15", "status": "OK", "mae": 12.3},
      {"type": "credit_scoring", "last_trained": "2026-06-23T02:18", "status": "DRIFT", "accuracy": 0.71},
    ]
  }
```

---

## 11. FRONTEND (React + TypeScript)

### Ce que je garderais
- React 18 + TypeScript — bon choix
- TanStack Query — excellent pour la gestion du cache serveur
- Recharts — sufficient pour les besoins actuels
- Architecture feature-based (`features/sales`, `features/analytics`…)

### Ce que je modifierais

**🔴 Héberger sur Vercel (pas depuis PythonAnywhere) :**
```bash
# vercel.json à la racine du projet frontend
{
  "rewrites": [{ "source": "/api/(.*)", "destination": "https://yourusername.pythonanywhere.com/api/$1" }],
  "headers": [{ "source": "/(.*)", "headers": [{"key": "X-Frame-Options", "value": "DENY"}] }]
}
# + GitHub Actions pour déploiement automatique à chaque push sur main
```

**🟠 Gestion d'erreur globale centralisée :**
```typescript
// api/interceptors.ts — intercepteur Axios global
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const { status, data } = error.response ?? {}
    switch (status) {
      case 401: return redirectToLogin()
      case 403: return toast.error("Accès non autorisé pour votre rôle")
      case 422: return handleValidationError(data?.error)
      case 429: return toast.error("Trop de requêtes. Veuillez patienter.")
      case 500: return toast.error("Erreur serveur. L'équipe technique a été alertée.")
      default:  return toast.error(data?.error?.message ?? "Erreur inattendue")
    }
    return Promise.reject(error)
  }
)
```

**🟠 Composant de tableau universel avec tri, filtre, pagination côté serveur :**
```typescript
// components/DataTable/ServerDataTable.tsx
// Un seul composant réutilisable dans tous les modules
// Évite de réécrire le tri/filtre/pagination pour chaque liste
interface ServerDataTableProps<T> {
  queryKey: string[]
  fetchFn: (params: TableParams) => Promise<PaginatedResponse<T>>
  columns: ColumnDef<T>[]
  searchPlaceholder?: string
  exportable?: boolean
}
```

**🟡 Skeleton loading au lieu des spinners :**
```typescript
// Plus professionnel et moins anxiogène
// Au lieu de <Spinner /> pendant le chargement :
function SalesSkeleton() {
  return Array(5).fill(0).map((_, i) => (
    <div key={i} className="animate-pulse h-12 bg-gray-100 rounded mb-2" />
  ))
}
```

### Ce que je supprimerais
- **Les `console.log` de debug** laissés dans le code de production — les remplacer par un logger configurable (`import { logger } from '@/utils/logger'`)
- **Les `any` TypeScript** — les remplacer par des types précis. Un `any` est une dette technique.
- **Les appels API directement dans les composants** — tout passer par des hooks TanStack Query dédiés

### Ce que j'ajouterais

**🔴 PWA + Offline (voir vision stratégique) :**
```bash
npm install vite-plugin-pwa idb
```

**🟠 i18n multi-langue :**
```bash
npm install i18next react-i18next
# Fichiers de traduction : fr.json, moore.json, dioula.json
```

**🟠 Mode économie de données (Low-Data Mode) :**
```typescript
// Détecter automatiquement la qualité du réseau
const connection = (navigator as any).connection
const isSlowNetwork = ['slow-2g', '2g'].includes(connection?.effectiveType)

// En mode lent : désactiver les graphiques, réduire la pagination
const { data: sales } = useQuery({
  queryKey: ['sales'],
  queryFn: () => fetchSales({ limit: isSlowNetwork ? 10 : 50, charts: !isSlowNetwork })
})
```

**🟡 QR Scanner intégré :**
```bash
npm install html5-qrcode
# Scanner QR produit depuis la page de vente sur mobile
```

**🟡 Mode sombre adaptatif :**
```typescript
// Économise la batterie sur les écrans OLED (courants sur Tecno/Infinix/Samsung)
// Respecte les préférences système + option manuelle
```

---

## 12. INFRASTRUCTURE & DEVOPS

### Ce que je garderais
- PythonAnywhere comme backend hosting
- GitHub pour le versioning

### Ce que je modifierais

**🔴 Cloudflare en proxy devant PythonAnywhere :**
```
Internet → Cloudflare (gratuit) → PythonAnywhere
Avantages : DDoS protection, cache, SSL, compression, rate limiting avancé
Configuration : 10 minutes sur cloudflare.com
```

**🟠 GitHub Actions pour le CI/CD ✅ IMPLÉMENTÉ (155 tests avant déploiement, `sshpass` + `PA_SSH_PASSWORD`) :**
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on: push: branches: [main, develop]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: python -m pytest backend/tests/ --tb=short  # 155 tests — pipeline bloque si échec

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - run: cd frontend && npm ci && npm run type-check && npm run lint

  deploy-frontend:
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: cd frontend && npm run build
      - uses: amondnet/vercel-action@v25

  deploy-backend:
    needs: [test-backend]
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to PythonAnywhere via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ssh.pythonanywhere.com
          username: ${{ secrets.PA_USERNAME }}
          password: ${{ secrets.PA_PASSWORD }}
          script: |
            cd /home/${{ secrets.PA_USERNAME }}/gescom
            git pull origin main
            pip install -r requirements.txt --quiet
            touch /var/www/${{ secrets.PA_USERNAME }}_pythonanywhere_com_wsgi.py
```

**🟠 Variables d'environnement documentées et validées au démarrage :**
```python
# app/config/validator.py
REQUIRED_ENV_VARS = [
    "SECRET_KEY", "DATABASE_URL", "JWT_SECRET_KEY",
    "CINETPAY_API_KEY", "WHATSAPP_TOKEN", "SENTRY_DSN",
    "FIELD_ENCRYPTION_KEY"
]

def validate_environment():
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        raise EnvironmentError(
            f"Variables d'environnement manquantes : {', '.join(missing)}\n"
            f"Consultez .env.example pour la liste complète."
        )
# Appelé dans create_app() — l'application refuse de démarrer si une variable manque
```

### Ce que j'ajouterais

**🟠 Sentry pour le monitoring des erreurs ✅ IMPLÉMENTÉ (SDK optionnel, s'active si `SENTRY_DSN` défini) :**
```python
import sentry_sdk
sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"), traces_sample_rate=0.1)
# Gratuit jusqu'à 5000 erreurs/mois — optionnel, conditionnel à SENTRY_DSN
```

**🟠 Endpoint /health pour UptimeRobot :**
```python
@app.get("/health")
def health():
    try: db.session.execute(text("SELECT 1")); db_ok = True
    except: db_ok = False
    status = 200 if db_ok else 503
    return jsonify({"db": "ok" if db_ok else "error", "version": APP_VERSION}), status
# UptimeRobot ping toutes les 5 minutes → alerte email/SMS si 503
```

**🟡 Script de backup quotidien :**
```bash
# PythonAnywhere Scheduled Tasks — 3h du matin
#!/bin/bash
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME | gzip > ~/backups/backup_$(date +%Y%m%d).sql.gz
ls -t ~/backups/*.sql.gz | tail -n +31 | xargs rm -f  # Garder 30 jours
```

---

## RÉCAPITULATIF GLOBAL — CE QUE JE REFERAIS EN PREMIER

Si je recréais le projet from scratch, les décisions que je prendrais dès le jour 1 :

| Ordre | Décision | Impact |
|---|---|---|
| 1 | Frontend sur Vercel, backend sur PythonAnywhere, Cloudflare devant | Architecture performante sans coût |
| 2 | JWT en httpOnly cookies dès le début | Sécurité fondamentale |
| 3 | `AuditLog` dans le modèle de données initial | Traçabilité sans refactoring |
| 4 | Format de réponse API standardisé `{success, data, error, meta}` | Cohérence totale frontend/backend |
| 5 | ML via threads Python natifs (à la demande) + cron `scripts/cron_train_all.py` (PythonAnywhere Tasks) — Celery/Redis supprimés ✅ | Stabilité PythonAnywhere |
| 6 | Scoring crédit : "données insuffisantes" si < 5 crédits historiques | Honnêteté décisionnelle |
| 7 | Service Worker + IndexedDB dès le scaffolding | Offline-first architectural |
| 8 | Index DB définis dans les migrations initiales | Performance sans refactoring |
| 9 | Variables d'environnement validées au démarrage | Déploiements sûrs |
| 10 | WhatsApp comme canal de notification primaire | Adoption africaine |

---

### Champs DB ajoutés (✅ migrés via Alembic, 10 migrations dans `backend/migrations/versions/`)
- `users.must_change_password BOOLEAN DEFAULT TRUE` — RF-05 validé serveur
- `sales.approved_by_id VARCHAR(36) NULL` (FK vers `users.id`) — RF-16/RG-23 validé serveur
- Table `token_blocklist` (id, jti, user_id, created_at, expires_at) — révocation JWT sans Redis

---

*Revue architecturale GesCom-BF — mise à jour 1er juillet 2026*
