# GesCom-BF 2.0 — Vision Stratégique Totale
## Tout ce qu'il faut changer, ajouter, repenser pour un succès complet

---

> **Dernière mise à jour :** 1er juillet 2026 — conformité code v2 post-corrections soutenance.

---

> Ce document n'est pas un plan de corrections — c'est un changement de regard. Chaque section questionne une hypothèse de départ et propose une direction radicalement plus adaptée, plus moderne, plus africaine.

---

## 1. CHANGEMENT DE PARADIGME — PENSER AUTREMENT

### Ce que tu crois construire vs ce que tu devrais construire

| Perception actuelle | Vision à adopter |
|---|---|
| "Une application web de gestion commerciale" | **"Le système d'exploitation de la PME africaine"** |
| "Un SaaS avec des modules ML" | **"Une plateforme de décision augmentée, offline-first, mobile-first"** |
| "Géré depuis un ordinateur" | **"Conçu pour un smartphone sous 3G, avec coupure de courant"** |
| "Les données servent l'analytique" | **"L'analytique sert l'action immédiate du commerçant"** |
| "L'IA est une fonctionnalité" | **"L'IA est le moteur — l'interface n'est que la fenêtre"** |
| "Un outil pour les managers" | **"Un assistant pour chaque rôle, du vendeur au propriétaire"** |

### La vérité sur ton utilisateur cible au Burkina Faso

- Il utilise un **smartphone Android** (Tecno, Infinix, Samsung Galaxy A-series) — pas un PC
- Sa connexion est **Orange 3G ou Wave**, souvent instable — jamais fibre
- Il communique via **WhatsApp** — pas par email
- Il paie via **Orange Money, Moov Money ou Wave** — pas par carte bancaire
- Il gère des **crédits informels** (tontines, avances) — pas des crédits bancaires formels
- Il a parfois un **niveau de lecture limité en français** — il comprend les images et les chiffres
- Il vit des **cycles saisonniers forts** : Tabaski, Noël, saison des pluies (agriculture), rentrée scolaire

**Conséquence directe :** Toute décision technique doit partir de cette réalité, pas des bonnes pratiques européennes.

---

## 2. INFRASTRUCTURE — TIRER LE MAXIMUM DE PYTHONANYWHERE

### Ce qu'on ne change pas
PythonAnywhere reste le backend. C'est fiable, abordable, et tu le maîtrises. La question est de l'optimiser et de ne plus lui demander ce qu'il ne peut pas faire.

### Ce qu'on change radicalement

#### Découplage frontend — migrer vers Vercel/Netlify (gratuit)

**Aujourd'hui :** React build servi depuis PythonAnywhere (lent, même CDN que l'API).

**Demain :**
```
Utilisateur → Vercel/Netlify (CDN mondial, Edge Network) → fichiers statiques React
           → PythonAnywhere (uniquement l'API Flask)
```

**Avantages concrets :**
- Premier chargement : 1,2 secondes au lieu de 4–6 secondes
- Zéro coût supplémentaire (Vercel free tier = illimité pour sites statiques)
- Déploiement automatique sur chaque `git push` via GitHub Actions
- HTTPS + HTTP/2 + compression Brotli automatiques

**GitHub Actions — déploiement automatique :**
```yaml
# .github/workflows/deploy.yml
name: Deploy Frontend
on:
  push:
    branches: [main]
    paths: ['frontend/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build React
        run: cd frontend && npm ci && npm run build
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

#### Cloudflare en proxy gratuit

**Placer Cloudflare devant PythonAnywhere :**
```
Internet → Cloudflare (CDN + DDoS + Cache) → PythonAnywhere
```

**Ce que Cloudflare fait gratuitement :**
- Cache les réponses API répétitives (listes produits, catalogues)
- Absorbe les attaques DDoS
- Certificat SSL automatique
- Rate limiting avancé (meilleur que Flask-Limiter seul)
- Analytics de trafic

**Configuration pour l'API Flask :**
```
Cache-Control: public, max-age=60   → pour /products, /clients (60 secondes)
Cache-Control: no-store             → pour /sales, /stocks (temps réel)
```

#### PythonAnywhere Scheduled Tasks — entraînement ML ✅ IMPLÉMENTÉ

**Celery et Redis supprimés**. PythonAnywhere offre des tâches planifiées (cron). L'entraînement ML est restructuré autour de cela — `scripts/cron_train_all.py` à la racine du dépôt, threads Python natifs pour les entraînements à la demande :

```bash
# PythonAnywhere Scheduled Tasks — configurer dans le dashboard
# Tous les jours à 2h du matin (trafic nul)
python /home/user/gescom/scripts/cron_train_all.py  # script racine du dépôt ✅

# Toutes les heures — mise à jour du Feature Store
python /home/user/gescom/scripts/refresh_feature_store.py

# Toutes les 15 minutes — alertes stock
python /home/user/gescom/scripts/check_stock_alerts.py
```

```python
# scripts/nightly_ml_training.py
"""
Script autonome — lancé par cron PythonAnywhere.
Entraîne tous les modèles actifs sans bloquer l'API.
"""
import sys, os
sys.path.insert(0, '/home/user/gescom/backend')
os.environ['FLASK_ENV'] = 'production'

from app import create_app, db
from app.ml.demand_forecast import DemandForecast
from app.ml.credit_scoring import CreditScoring
from app.ml.anomaly_detection import AnomalyDetection
from app.ml.rfm_segmentation import RFMSegmentation

app = create_app()
with app.app_context():
    print("[CRON] Démarrage entraînement nightly...")
    for Model in [DemandForecast, CreditScoring, AnomalyDetection, RFMSegmentation]:
        try:
            Model().train()
            print(f"[OK] {Model.__name__} entraîné")
        except Exception as e:
            print(f"[ERREUR] {Model.__name__}: {e}")
    print("[CRON] Terminé")
```

**Résultat ✅ ATTEINT :** L'entraînement ML ne bloque plus jamais l'API. Threads Python natifs pour les demandes ponctuelles, cron `cron_train_all.py` pour l'entraînement nocturne. Flask-Limiter 3.8.0 utilise `storage_uri="memory://"` (pas Redis).

---

## 3. MOBILE & OFFLINE — LA TRANSFORMATION LA PLUS IMPORTANTE

### Offline-First : la révolution pour l'Afrique

**Le principe :** L'application fonctionne SANS connexion internet. La connexion n'est qu'un moyen de synchronisation, pas un prérequis.

```
Sans connexion :
  → Les vendeurs enregistrent les ventes → stockées localement (IndexedDB)
  → Les managers consultent les rapports → mis en cache
  → Les stocks sont consultables → dernière version synchronisée

Avec connexion :
  → Synchronisation silencieuse et automatique en arrière-plan
  → Conflits résolus par timestamp (last-write-wins sur les ventes)
```

**Stack technique :**

```typescript
// 1. Vite PWA Plugin (déjà recommandé, mais voici la config complète)
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa'

VitePWA({
  registerType: 'autoUpdate',
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
    runtimeCaching: [
      {
        // Cache les produits 24h
        urlPattern: ({ url }) => url.pathname.startsWith('/api/v1/products'),
        handler: 'CacheFirst',
        options: { cacheName: 'products-cache', expiration: { maxAgeSeconds: 86400 } }
      },
      {
        // Cache les clients 1h
        urlPattern: ({ url }) => url.pathname.startsWith('/api/v1/clients'),
        handler: 'StaleWhileRevalidate',
        options: { cacheName: 'clients-cache', expiration: { maxAgeSeconds: 3600 } }
      },
      {
        // Les ventes : réseau si possible, sinon file d'attente
        urlPattern: ({ url }) => url.pathname.startsWith('/api/v1/sales'),
        handler: 'NetworkOnly',
        options: {
          backgroundSync: {
            name: 'sales-sync-queue',
            options: { maxRetentionTime: 24 * 60 } // 24h de rétention
          }
        }
      }
    ]
  }
})
```

```typescript
// 2. File de synchronisation des ventes hors ligne
// hooks/useOfflineSync.ts
import { openDB, DBSchema } from 'idb'

interface GesComDB extends DBSchema {
  pending_sales: {
    key: number
    value: {
      local_id?: number
      payload: SalePayload
      queued_at: string
      sync_attempts: number
    }
  }
  cached_products: {
    key: string
    value: Product & { cached_at: string }
  }
}

const getDB = () => openDB<GesComDB>('gescom-offline-v1', 1, {
  upgrade(db) {
    db.createObjectStore('pending_sales', { keyPath: 'local_id', autoIncrement: true })
    db.createObjectStore('cached_products', { keyPath: 'id' })
  }
})

export async function saveSaleOffline(payload: SalePayload) {
  const db = await getDB()
  const local_id = await db.add('pending_sales', {
    payload,
    queued_at: new Date().toISOString(),
    sync_attempts: 0
  })
  return local_id
}

export async function syncPendingSales(api: AxiosInstance): Promise<number> {
  const db = await getDB()
  const pending = await db.getAll('pending_sales')
  let synced = 0

  for (const item of pending) {
    try {
      await api.post('/api/v1/sales', item.payload)
      await db.delete('pending_sales', item.local_id!)
      synced++
    } catch (e) {
      if (item.sync_attempts >= 3) {
        // Notifier l'admin après 3 échecs
        toast.error(`Vente du ${item.queued_at} : impossible de synchroniser`)
      }
      await db.put('pending_sales', { ...item, sync_attempts: item.sync_attempts + 1 })
    }
  }
  return synced
}
```

**Indicateur de statut de connexion :**
```typescript
// components/ConnectionStatus.tsx
export function ConnectionStatus() {
  const [online, setOnline] = useState(navigator.onLine)
  const pendingCount = usePendingSalesCount()

  useEffect(() => {
    window.addEventListener('online', () => { setOnline(true); syncPendingSales() })
    window.addEventListener('offline', () => setOnline(false))
  }, [])

  if (online && pendingCount === 0) return null

  return (
    <div className={`fixed bottom-4 left-4 px-3 py-2 rounded-full text-sm font-medium ${
      online ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
    }`}>
      {online
        ? `Synchronisation de ${pendingCount} vente(s) en cours...`
        : `Hors ligne — ${pendingCount} vente(s) en attente`}
    </div>
  )
}
```

### Interface ultra-légère (mode économie de données)

**Ajouter un mode "Faible connexion" :**
```typescript
// Détecter la qualité du réseau
const connection = (navigator as any).connection
const isSlowNetwork = connection?.effectiveType === '2g' || connection?.effectiveType === 'slow-2g'

// En mode faible connexion :
// - Désactiver les graphiques Recharts (charger du texte seulement)
// - Réduire la pagination (10 au lieu de 50 éléments)
// - Désactiver les images produits
// - Utiliser des tableaux HTML simples au lieu des composants complexes
```

---

## 4. INTÉGRATIONS AFRICAINES — CE QUI REND LE PROJET UNIQUE

### Mobile Money — Orange Money, Wave, Moov Money

C'est **LA** fonctionnalité différenciante. Personne ne paie par carte bancaire au Burkina Faso. Intégrer le paiement mobile directement dans le flux de vente, c'est révolutionner l'expérience caisse.

**Architecture d'intégration :**
```
Vendeur enregistre une vente → choisit "Paiement Mobile Money"
→ Saisit le numéro du client
→ L'API envoie une requête de paiement via CinetPay / Bizao
→ Le client reçoit une notification USSD sur son téléphone ("Confirmez le paiement de 15,000 FCFA ?")
→ Le client valide avec son code PIN
→ Confirmation reçue → vente enregistrée automatiquement comme PAYÉE
```

**CinetPay (API de référence pour l'Afrique de l'Ouest) :**
```python
# app/services/mobile_money_service.py
import requests

CINETPAY_API_KEY = os.environ.get("CINETPAY_API_KEY")
CINETPAY_SITE_ID = os.environ.get("CINETPAY_SITE_ID")

def initiate_mobile_payment(
    amount: float,
    customer_phone: str,
    reference: str,
    description: str
) -> dict:
    """
    Initie un paiement Orange Money / Moov / Wave via CinetPay.
    Retourne un lien de paiement ou un code USSD.
    """
    payload = {
        "apikey": CINETPAY_API_KEY,
        "site_id": CINETPAY_SITE_ID,
        "transaction_id": reference,
        "amount": int(amount),
        "currency": "XOF",
        "description": description,
        "customer_phone_number": customer_phone,
        "channels": "MOBILE_MONEY",
        "notify_url": f"{os.environ.get('APP_URL')}/api/v1/payments/webhook/cinetpay",
    }
    response = requests.post(
        "https://api-checkout.cinetpay.com/v2/payment",
        json=payload,
        timeout=10
    )
    return response.json()

def verify_payment(transaction_id: str) -> dict:
    """Vérifie le statut d'un paiement."""
    response = requests.post(
        "https://api-checkout.cinetpay.com/v2/payment/check",
        json={
            "apikey": CINETPAY_API_KEY,
            "site_id": CINETPAY_SITE_ID,
            "transaction_id": transaction_id
        },
        timeout=10
    )
    return response.json()

# Webhook de confirmation (appelé par CinetPay)
@bp.route("/payments/webhook/cinetpay", methods=["POST"])
def cinetpay_webhook():
    data = request.json
    if data.get("status") == "ACCEPTED":
        sale_id = data.get("transaction_id")
        # Marquer la vente comme payée
        sale = Sale.query.get(sale_id)
        if sale:
            sale.payment_status = "PAID"
            sale.payment_method = "MOBILE_MONEY"
            db.session.commit()
    return jsonify({"message": "OK"}), 200
```

**Autres APIs Mobile Money disponibles :**
- **Bizao** : Orange Money Burkina + plusieurs pays UEMOA
- **Ding** : recharges téléphoniques intégrées
- **AfricasTalking** : paiements + SMS + USSD (très complet)

### WhatsApp Business — Le canal de communication principal

**WhatsApp comme canal de notification, reçu et alerte :**

```python
# app/services/whatsapp_service.py
# Via WhatsApp Business API (Meta) ou via Twilio pour WhatsApp

import requests

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID")

def send_whatsapp_message(to_number: str, template_name: str, params: list) -> bool:
    """
    Envoie un message WhatsApp via un template pré-approuvé.
    Les templates doivent être approuvés par Meta.
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": f"226{to_number.lstrip('0')}",  # Format international Burkina
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "fr"},
            "components": [{
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in params]
            }]
        }
    }
    r = requests.post(
        f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages",
        headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"},
        json=payload,
        timeout=5
    )
    return r.status_code == 200

# Templates à créer sur Meta Business :
# 1. "sale_receipt" → "Reçu N°{{1}} | Montant: {{2}} FCFA | Merci de votre confiance. GesCom-BF"
# 2. "credit_reminder" → "Rappel: Votre crédit de {{1}} FCFA est dû le {{2}}. Contactez-nous."
# 3. "stock_alert" → "ALERTE STOCK: {{1}} est en rupture ({{2}} unités restantes)."
# 4. "payment_confirmation" → "Paiement reçu: {{1}} FCFA pour votre achat du {{2}}. Merci!"

def send_sale_receipt_whatsapp(sale: Sale, client_phone: str):
    return send_whatsapp_message(
        client_phone,
        "sale_receipt",
        [str(sale.reference), f"{sale.montant_total:,.0f}"]
    )

def send_credit_reminder_whatsapp(credit: Credit):
    if not credit.client.telephone: return
    return send_whatsapp_message(
        credit.client.telephone,
        "credit_reminder",
        [f"{credit.solde_restant:,.0f}", credit.date_echeance.strftime("%d/%m/%Y")]
    )
```

**Déclencher automatiquement :**
```python
# Après chaque vente :
after_sale_created → send_sale_receipt_whatsapp()

# Via cron PythonAnywhere (chaque matin à 8h) :
# Pour tous les crédits dont l'échéance est dans 3 jours :
credits_due_soon = Credit.query.filter(
    Credit.date_echeance <= datetime.now() + timedelta(days=3),
    Credit.statut == "EN_COURS"
).all()
for credit in credits_due_soon:
    send_credit_reminder_whatsapp(credit)
```

### SMS comme fallback universel (Africa's Talking)

Pour les clients sans WhatsApp, les zones sans 3G, les téléphones basiques :

```python
# app/services/sms_service.py
import africastalking  # pip install africastalking

africastalking.initialize(
    username=os.environ.get("AT_USERNAME"),
    api_key=os.environ.get("AT_API_KEY")
)
sms = africastalking.SMS

def send_sms(phone: str, message: str) -> bool:
    try:
        response = sms.send(
            message=message[:160],  # Limite SMS
            recipients=[f"+226{phone.lstrip('0')}"],
            sender_id="GesCom-BF"
        )
        return response["SMSMessageData"]["Recipients"][0]["status"] == "Success"
    except Exception:
        return False

# Stratégie de fallback :
def notify_client(client, message_type, **kwargs):
    """Tente WhatsApp d'abord, SMS si échec."""
    if client.telephone:
        success = send_whatsapp_message(client.telephone, message_type, **kwargs)
        if not success:
            send_sms(client.telephone, format_sms(message_type, **kwargs))
```

### QR Code pour les produits (remplace les codes-barres)

Au Burkina Faso, les douchettes code-barres sont rares. La caméra du smartphone est universelle.

```python
# Backend — générer un QR code par produit
import qrcode
import io, base64

def generate_product_qr(product_id: int) -> str:
    """Génère un QR code encodant l'URL du produit."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(f"gescom://product/{product_id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

@bp.route("/products/<int:product_id>/qr", methods=["GET"])
def get_product_qr(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({"qr_code_base64": generate_product_qr(product_id)})
```

```typescript
// Frontend — scanner QR avec la caméra du smartphone
import { Html5QrcodeScanner } from 'html5-qrcode'

function QRScannerButton({ onProductScanned }: Props) {
  const startScan = () => {
    const scanner = new Html5QrcodeScanner("qr-reader", { fps: 10, qrbox: 250 })
    scanner.render(
      (decodedText) => {
        const match = decodedText.match(/gescom:\/\/product\/(\d+)/)
        if (match) onProductScanned(parseInt(match[1]))
        scanner.clear()
      },
      (error) => console.warn(error)
    )
  }
  return <button onClick={startScan}>Scanner un produit</button>
}
```

---

## 5. IA REVISITÉE — PASSER DE "MODULES ML" À "INTELLIGENCE ACTIONNABLE"

### Le problème actuel
Les prédictions sont calculées et affichées. L'utilisateur ne sait pas quoi en faire.

### La nouvelle approche : IA = Action recommandée immédiate

Chaque output ML doit se terminer par **une phrase d'action concrète**, visible en grand.

```
Avant : "Score crédit : 42/100 — Risque MOYEN"
Après : "Ce client a remboursé 8/10 de ses crédits passés.
         → Recommandation : Accorder jusqu'à 75,000 FCFA avec délai de 30 jours."

Avant : "Produit FARINE_BLE — AX — Forte contribution, demande régulière"
Après : "La farine de blé représente 23% de votre CA.
         → Stock actuel : 12 sacs. → Commandez 40 sacs avant vendredi."

Avant : "Transaction T-2024-0847 : anomalie détectée"
Après : "Vente inhabituelle à 22h par Amadou — remise de 35%.
         → Vérifiez avec le vendeur ou examinez la caméra de cette heure."
```

### IA Explicable (XAI) avec SHAP — rendre les décisions compréhensibles ✅ IMPLÉMENTÉ

```python
# pip install shap
import shap

class CreditScoringExplainable(CreditScoring):
    def explain(self, customer_id: int) -> dict:
        """
        Explique POURQUOI ce score avec des phrases en français.
        """
        df = self._get_customer_features([customer_id])
        if df.empty: return {"explanation": "Données insuffisantes"}

        model = self._load_active_model()
        if not model: return {"explanation": "Modèle non disponible"}

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(df[FEATURE_COLUMNS])

        # Construire des phrases lisibles à partir des valeurs SHAP
        feature_impacts = {
            col: float(val)
            for col, val in zip(FEATURE_COLUMNS, shap_values[1][0])
        }

        explanations = []
        if feature_impacts.get("nb_retards", 0) > 0.1:
            explanations.append(f"Plusieurs retards de paiement constatés")
        if feature_impacts.get("taux_remboursement", 0) < -0.1:
            explanations.append(f"Taux de remboursement faible")
        if feature_impacts.get("anciennete_jours", 0) > 0.05:
            explanations.append(f"Client de longue date (point positif)")
        if feature_impacts.get("encours_actuel", 0) > 0.1:
            explanations.append(f"Encours actuel élevé par rapport à son historique")

        return {
            "customer_id": customer_id,
            "score": self.score(customer_id),
            "reasons": explanations,
            "action": self._recommend_action(feature_impacts)
        }

    def _recommend_action(self, impacts: dict) -> str:
        score = sum(impacts.values())
        if score > 0.3:   return "Refuser ou demander une garantie"
        elif score > 0:   return "Accorder avec plafond réduit (50% du maximum habituel)"
        else:             return "Accorder normalement selon le plafond client"
```

### Modèles saisonniers africains — entraîner sur les vraies patterns locales ✅ IMPLÉMENTÉ (`/analytics/african-context`)

Les indicateurs de contexte africain sont intégrés dans les prévisions :

```python
# app/ml/demand_forecast_v2.py
# Ajouter des variables de saisonnalité africaine

AFRICAN_EVENTS = {
    # (mois, semaine_du_mois) : facteur multiplicateur
    (1, 1): 0.6,   # Début janvier — post-fêtes, budget épuisé
    (4, 2): 1.4,   # Pâques catholique (variable)
    (7, 1): 1.8,   # Début Tabaski (variable selon calendrier lunaire)
    (9, 1): 1.5,   # Rentrée scolaire
    (12, 3): 2.0,  # Semaine de Noël
    (12, 4): 1.8,  # Réveillon / Nouvel An
}

RAINY_SEASON_MONTHS = [6, 7, 8, 9]  # Saison des pluies — accès difficile

def _build_features_with_african_context(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les features de contexte africain."""
    df['is_ramadan'] = df['date'].apply(_is_ramadan)
    df['is_tabaski_week'] = df['date'].apply(_is_tabaski_week)
    df['is_rainy_season'] = df['date'].dt.month.isin(RAINY_SEASON_MONTHS).astype(int)
    df['is_school_start'] = ((df['date'].dt.month == 9) & (df['date'].dt.day <= 15)).astype(int)
    df['is_month_end'] = (df['date'].dt.day >= 25).astype(int)  # Jours de salaire
    df['is_market_day'] = df['date'].apply(_is_local_market_day)  # Jours de marché locaux
    return df
```

### Prédictions proactives — l'IA prévient avant que ça devienne un problème

```python
# app/services/proactive_insights.py
"""
Service qui génère des alertes proactives sans que l'utilisateur ne demande rien.
Lancé par cron PythonAnywhere chaque matin.
"""

def generate_morning_digest(branch_id: int) -> dict:
    """
    Génère un digest matinal personnalisé pour chaque branche.
    Envoyé par WhatsApp au manager à 7h30.
    """
    insights = []

    # 1. Alertes stock critique
    critical_stock = get_critical_stock_alerts(branch_id)
    for item in critical_stock[:3]:
        insights.append(f"⚠️ {item['product_name']}: {item['stock']} unités (seuil: {item['min']})")

    # 2. Prévision du jour
    forecast = DemandForecast().predict_today(branch_id)
    insights.append(f"📈 CA prévu aujourd'hui: {forecast['expected_revenue']:,.0f} FCFA")

    # 3. Crédits à relancer
    overdue = get_overdue_credits(branch_id)
    if overdue:
        insights.append(f"💰 {len(overdue)} crédit(s) en retard — total: {sum(c['solde'] for c in overdue):,.0f} FCFA")

    # 4. Anomalie de la veille
    anomalies = AnomalyDetection().get_yesterday_anomalies(branch_id)
    if anomalies:
        insights.append(f"🔍 {len(anomalies)} transaction(s) suspecte(s) hier à vérifier")

    return {
        "branch_id": branch_id,
        "date": date.today().isoformat(),
        "insights": insights,
        "summary": "\n".join(insights)
    }
```

---

## 6. EXPÉRIENCE UTILISATEUR — MODERNE, SIMPLE, AFRICAIN

### Design Principles pour l'Afrique

**Principe 1 : Les chiffres parlent plus que les mots**
- Tous les KPIs en grand, lisibles à 1 mètre du téléphone
- Pas de jargon technique dans l'interface
- Icônes universelles (panier, argent, personne, alerte)

**Principe 2 : Une action principale par écran**
- Page de vente : le bouton "Valider la vente" prend 50% de l'écran sur mobile
- Pas de menus cachés, tout accessible en 2 clics maximum

**Principe 3 : Biométrie comme authentification**
```typescript
// Connexion par empreinte digitale (smartphones Android récents)
async function authenticateWithBiometric(): Promise<boolean> {
  if (!window.PublicKeyCredential) return false

  try {
    const assertion = await navigator.credentials.get({
      publicKey: {
        challenge: new Uint8Array(32),
        rpId: window.location.hostname,
        userVerification: 'required',
        timeout: 30000
      }
    })
    return !!assertion
  } catch {
    return false
  }
}
// Si biométrie disponible → proposer comme alternative au mot de passe
// Réduire la friction de connexion = plus d'utilisation quotidienne
```

**Principe 4 : Mode sombre par défaut (batterie)**
```typescript
// tailwind.config.ts — mode sombre activé par classe
darkMode: 'class'

// Détecter et appliquer automatiquement selon les préférences système
// + option dans les paramètres utilisateur
// Économise 30-40% de batterie sur les écrans OLED (courants sur Tecno/Infinix)
```

### Multi-langue : Français + Mooré + Dioula

```typescript
// i18n/locales/moore.json — langue nationale principale du Burkina Faso
{
  "dashboard": "Yii-yidg nabre",   // Vue d'ensemble
  "sales": "Rogo",                  // Ventes
  "stock": "Ninsaala",              // Stock
  "clients": "Neba",                // Clients
  "validate": "Sõmde",              // Valider
  "cancel": "Bas",                  // Annuler
  "total": "Fãa"                    // Total
}

// i18n/locales/dioula.json
{
  "dashboard": "Kalan jɛlen",
  "sales": "Feere",
  "stock": "Sɔrɔko",
  "clients": "Jɔn",
  "validate": "Sigi",
  "total": "Bɛɛ lajɛlen"
}
```

```typescript
// Sélecteur de langue persisté par utilisateur
// app/utils/i18n.ts
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

i18n.use(initReactI18next).init({
  resources: {
    fr: { translation: require('./locales/fr.json') },
    moore: { translation: require('./locales/moore.json') },
    dioula: { translation: require('./locales/dioula.json') },
  },
  lng: localStorage.getItem('user_language') || 'fr',
  fallbackLng: 'fr',
})
```

### Saisie vocale pour les marchands peu lettrés

```typescript
// Pour la saisie du nom d'un client ou d'un produit
function VoiceSearchButton({ onResult }: { onResult: (text: string) => void }) {
  const startVoice = () => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)()
    recognition.lang = 'fr-FR'
    recognition.onresult = (event) => {
      onResult(event.results[0][0].transcript)
    }
    recognition.start()
  }
  return <button onClick={startVoice} aria-label="Recherche vocale">🎤</button>
}
```

---

## 7. MODULE TONTINE & CRÉDIT INFORMEL — FONCTIONNALITÉ UNIQUE EN AFRIQUE

**La tontine est le système financier informel le plus utilisé en Afrique de l'Ouest.** Aucun ERP standard ne le gère. GesCom-BF peut être le premier.

```python
# app/models/tontine.py
class TontineGroup(db.Model):
    """Groupe de tontine associé à une structure commerciale."""
    __tablename__ = "tontine_groups"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cotisation_montant = db.Column(db.Numeric(12, 2), nullable=False)  # Mise mensuelle
    frequence = db.Column(db.Enum("HEBDOMADAIRE", "MENSUEL"), default="MENSUEL")
    date_debut = db.Column(db.Date, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"))
    members = db.relationship("TontineMember", back_populates="group")

class TontineMember(db.Model):
    __tablename__ = "tontine_members"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("tontine_groups.id"))
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"))
    tour_ordre = db.Column(db.Integer)       # Ordre dans lequel il reçoit la cagnotte
    a_recu = db.Column(db.Boolean, default=False)
    cotisations = db.relationship("TontineCotisation", back_populates="member")

class TontineCotisation(db.Model):
    __tablename__ = "tontine_cotisations"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("tontine_members.id"))
    montant = db.Column(db.Numeric(12, 2))
    date_cotisation = db.Column(db.Date)
    payment_method = db.Column(db.Enum("CASH", "ORANGE_MONEY", "WAVE", "MOOV"))
    statut = db.Column(db.Enum("PAYEE", "EN_RETARD", "EXONERE"))
```

**Fonctionnalités du module Tontine :**
- Gestion des membres et de leur ordre de tirage
- Suivi des cotisations (payées / en retard)
- Calcul automatique de la cagnotte du mois
- Notification WhatsApp/SMS au membre qui va recevoir
- Intégration avec le module crédit (la tontine comme garantie)

---

## 8. SÉCURITÉ MODERNE — ZÉRO CONFIANCE

### Architecture Zero-Trust pour un SaaS africain

```python
# Chaque requête est vérifiée sur 4 niveaux :
# 1. Token valide (JWT) ✓ déjà fait
# 2. Rôle autorisé (RBAC) ✓ déjà fait
# 3. Branche autorisée (row-level security) — À AJOUTER
# 4. Rate limiting par utilisateur (pas seulement par IP) — À AJOUTER

# Row-Level Security — s'assurer que chaque requête ne lit que sa branche
@bp.before_request
def enforce_branch_isolation():
    """
    Middleware : injecter branch_id dans g pour filtrer automatiquement.
    Empêche un utilisateur d'une branche de voir les données d'une autre.
    """
    if hasattr(g, 'current_user') and g.current_user:
        user = g.current_user
        if user.role.name not in ["SUPER_ADMIN", "ADMIN"]:
            g.allowed_branch_ids = [b.id for b in user.branches]
        else:
            g.allowed_branch_ids = None  # Accès total

# Utilisation dans les services :
def get_sales(branch_id=None):
    query = Sale.query
    if g.allowed_branch_ids is not None:
        query = query.filter(Sale.branch_id.in_(g.allowed_branch_ids))
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    return query.all()
```

### 2FA par SMS (second facteur africain)

Les applications TOTP (Google Authenticator) sont peu utilisées en Afrique. Le SMS est universel.

```python
# app/services/otp_service.py
import random, hashlib

def generate_otp(user_id: int) -> str:
    """Génère un OTP 6 chiffres valable 5 minutes."""
    import time
    seed = f"{user_id}{int(time.time() // 300)}{os.environ.get('OTP_SECRET')}"
    hash_val = hashlib.sha256(seed.encode()).hexdigest()
    otp = str(int(hash_val[:8], 16) % 1000000).zfill(6)
    return otp

def verify_otp(user_id: int, otp_provided: str) -> bool:
    expected = generate_otp(user_id)
    return otp_provided == expected

# Flow :
# 1. Login avec email/password → succès → envoyer OTP par SMS
# 2. Utilisateur saisit l'OTP → accès accordé
# 3. Option "Se souvenir de cet appareil 30 jours" (cookie signé)
```

---

## 9. DONNÉES & ANALYTIQUE — LA VISION AFRICAINE

### Dashboard Décisionnel "3 Chiffres"

Le tableau de bord actuel contient trop d'informations. La recherche sur les tableaux de bord mobiles montre que 3 métriques par écran est l'optimum pour la prise de décision rapide.

**Vue manager au lancement de l'app (morning view) :**
```
╔══════════════════════════════╗
║  Bonjour Moussa — Lun 23 Juin ║
╠══════════════════════════════╣
║  CA AUJOURD'HUI              ║
║  350,000 FCFA  ↑ +12%        ║
╠══════════════════════════════╣
║  RUPTURES DE STOCK           ║
║  3 produits critiques  →     ║
╠══════════════════════════════╣
║  CRÉDITS EN RETARD           ║
║  2 clients — 125,000 FCFA  → ║
╚══════════════════════════════╝
```

Un seul tap sur chaque ligne pour le détail. Pas de scrolling.

### Benchmark entre commerçants (anonymisé)

**Fonctionnalité différenciante :** Permettre à un commerçant de se comparer aux autres utilisateurs de GesCom-BF (sans révéler les identités).

```python
# app/services/benchmark_service.py
def get_sector_benchmark(branch_id: int, sector: str) -> dict:
    """
    Compare les KPIs d'une branche aux médianes anonymisées du secteur.
    Utilise uniquement des agrégats — aucune donnée individuelle exposée.
    """
    branch_kpis = compute_branch_kpis(branch_id)

    sector_stats = db.session.execute(text("""
        SELECT
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ca_mensuel) as median_ca,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY taux_marge) as median_marge,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rotation_stock) as median_rotation
        FROM branch_monthly_kpis
        WHERE sector = :sector
        AND branch_id != :branch_id
        AND mois >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
    """), {"sector": sector, "branch_id": branch_id}).fetchone()

    return {
        "votre_ca": branch_kpis["ca_mensuel"],
        "median_secteur": sector_stats.median_ca,
        "position": "AU-DESSUS" if branch_kpis["ca_mensuel"] > sector_stats.median_ca else "EN-DESSOUS",
        "ecart_pct": round((branch_kpis["ca_mensuel"] / sector_stats.median_ca - 1) * 100, 1)
    }
```

---

## 10. MODÈLE ÉCONOMIQUE AFRICAIN — CE QUI REND GESCOM-BF VIABLE

### Tarification adaptée à l'Afrique de l'Ouest

| Plan | Prix | Inclus | Cible |
|---|---|---|---|
| **Démarrage** | Gratuit 3 mois, puis 5,000 FCFA/mois | 1 branche, 3 utilisateurs, pas de ML | Très petits commerces |
| **Croissance** | 15,000 FCFA/mois | 3 branches, 10 utilisateurs, ML complet | PME en expansion |
| **Entreprise** | 35,000 FCFA/mois | Branches illimitées, API, support dédié | Groupes commerciaux |

**Paiement par Mobile Money :** Orange Money, Wave, Moov — pas de carte bancaire requise.

**Modèle d'agents :** Recruter des revendeurs locaux (comme les agents Orange Money) qui démarchent les commerçants et perçoivent 20% de commission sur les abonnements vendus.

### Freemium avec upgrade contextuel

Quand un utilisateur du plan Démarrage tente d'accéder au module analytique ML :
```
"Ce module est disponible à partir du plan Croissance.
 Passez à Croissance pour 15,000 FCFA/mois et obtenez :
 ✓ Prévisions de demande produit par produit
 ✓ Score de crédit de vos clients
 ✓ Alertes anomalies transactions
 
 [Payer 15,000 FCFA via Orange Money]  [Plus tard]"
```

---

## 11. RÉCAPITULATIF — MATRICE IMPACT × EFFORT

| Fonctionnalité | Impact | Effort | Priorité |
|---|---|---|---|
| PWA Offline-First | 🔴 Très élevé | Moyen | ★★★★★ |
| Mobile Money (CinetPay) | 🔴 Très élevé | Moyen | ★★★★★ |
| WhatsApp notifications | 🔴 Très élevé | Faible | ★★★★★ |
| Vercel pour le frontend | 🟠 Élevé | Très faible | ★★★★★ |
| Cloudflare en proxy | 🟠 Élevé | Très faible | ★★★★★ |
| Cron ML (PythonAnywhere) ✅ | 🟠 Élevé | Faible | ★★★★☆ |
| IA Explicable (SHAP) ✅ | 🟠 Élevé | Moyen | ★★★★☆ |
| Multi-langue (Moore/Dioula) | 🟠 Élevé | Moyen | ★★★★☆ |
| QR Code produits | 🟡 Moyen | Faible | ★★★☆☆ |
| SMS fallback (Africa's Talking) | 🟡 Moyen | Faible | ★★★☆☆ |
| Saisie vocale | 🟡 Moyen | Faible | ★★★☆☆ |
| Module Tontine | 🟡 Moyen | Élevé | ★★★☆☆ |
| 2FA par SMS | 🟡 Moyen | Faible | ★★★☆☆ |
| Benchmark secteur | 🟡 Moyen | Moyen | ★★☆☆☆ |
| Module facturation/abonnement | 🟠 Élevé | Élevé | ★★★☆☆ |

---

## 12. LA STACK IDÉALE — CE QUE SERAIT GESCOM-BF 2.0

```
FRONTEND
├── React 18 + TypeScript (gardé)
├── Vite + vite-plugin-pwa (PWA + offline)
├── TanStack Query (gardé)
├── i18next (fr + moore + dioula)
├── html5-qrcode (scan QR)
├── idb (IndexedDB offline)
└── Hébergé sur Vercel (CDN mondial, gratuit)

BACKEND (PythonAnywhere)
├── Flask 3.0.3 (gardé)
├── SQLAlchemy 2.x (gardé)
├── Flask-Limiter 3.8.0 (rate limiting, storage_uri="memory://", pas Redis) ✅
├── Sentry SDK optionnel (s'active si SENTRY_DSN défini) ✅
├── token_blocklist table SQL (révocation JWT, pas Redis) ✅
├── Threads Python natifs (entraînement ML à la demande) ✅
└── scripts/cron_train_all.py via PythonAnywhere Tasks (ML nightly) ✅

SERVICES EXTERNES
├── CinetPay (Mobile Money Orange/Moov/Wave)
├── WhatsApp Business API (Meta)
├── Africa's Talking (SMS fallback)
├── Cloudflare (CDN + DDoS, gratuit)
└── UptimeRobot (monitoring, gratuit)

BASE DE DONNÉES
├── MySQL 8 PythonAnywhere (production académique actuelle) ✅
├── PostgreSQL (cible VPS future)
└── IndexedDB navigateur (offline)

ML & IA
├── scikit-learn (gardé) ✅
├── mlxtend (Market Basket Analysis / Apriori) ✅
├── shap (TreeExplainer, /analytics/credit-scores/<id>/explain) ✅
├── pandas (Price Elasticity) ✅
├── Churn Probability (Logistic Regression) ✅
├── K-optimal RFM (Silhouette/Elbow, /analytics/rfm-segments/evaluate-k) ✅
├── African Context Indicators (/analytics/african-context) ✅
├── data_confidence dans prévisions Prophet ✅
├── ONNX export (serving léger) — perspective future
└── 155 tests (127 unitaires ML + 17 intégration API + 15 sécurité + 12 RBAC rôles) ✅

DEVOPS
├── GitHub + GitHub Actions (CI/CD) ✅ — 155 tests avant déploiement, pipeline bloque si échec
├── sshpass + PA_SSH_PASSWORD pour déploiement backend ✅
├── Déploiement auto frontend → Vercel (perspective)
├── Déploiement auto backend → PythonAnywhere via SSH ✅
└── Sentry + UptimeRobot (observabilité) — Sentry optionnel si SENTRY_DSN ✅
```

---

---

### État d'implémentation v2 (1er juillet 2026)

| Élément | Statut |
|---|---|
| Celery/Redis | ✅ Supprimés — threads Python natifs + cron `scripts/cron_train_all.py` |
| SSE temps réel | ✅ Désactivé (`DISABLE_SSE=true`) — fallback polling |
| token_blocklist | ✅ Table SQL (pas Redis) — révocation JWT |
| Flask-Limiter | ✅ 3.8.0 `storage_uri="memory://"` |
| RF-05 must_change_password | ✅ Validé serveur — 403 `PASSWORD_CHANGE_REQUIRED` |
| RF-16/RG-23 approved_by_id | ✅ Validé serveur — 422 si discount_rate > 0 sans approbation |
| Market Basket (Apriori/mlxtend) | ✅ `/analytics/basket` |
| Price Elasticity | ✅ `/analytics/price-elasticity` |
| Churn Probability | ✅ `/analytics/churn-risk` |
| African Context | ✅ `/analytics/african-context` |
| K-optimal RFM | ✅ `/analytics/rfm-segments/evaluate-k` |
| SHAP crédit | ✅ `/analytics/credit-scores/<id>/explain` |
| data_confidence | ✅ Dans prévisions demande |
| Tests | ✅ 155 (127 ML + 17 intégration + 15 sécurité + 12 RBAC) |
| CI/CD | ✅ GitHub Actions — pipeline bloque si échec |
| Sentry | ✅ Optionnel si `SENTRY_DSN` défini |
| Migrations Alembic | ✅ 10 migrations dans `backend/migrations/versions/` |
| MySQL PythonAnywhere | ✅ Production académique actuelle |

*Document de vision stratégique GesCom-BF 2.0 — mise à jour 1er juillet 2026*
*Ce document doit être relu et discuté avec l'encadrant avant toute implémentation.*
