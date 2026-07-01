# 17. Spécification API REST (OpenAPI 3.0)

## 17.1 Conventions générales

| Aspect | Convention |
|---|---|
| Base URL | `https://api.gescom-bf.com/api/v1` |
| Versioning | Préfixe d'URL `/v1` ; les changements non rétro-compatibles créent `/v2` |
| Format | JSON (`Content-Type: application/json`) |
| Authentification | `Authorization: Bearer <access_token>` (JWT) |
| Pagination | `?page=1&per_page=20`, réponse enveloppée `{ "data": [...], "meta": {"page", "per_page", "total"} }` |
| Erreurs | Format uniforme `{ "error": { "code": "...", "message": "..." } }` (cf. `09-BACKEND-FLASK.md` §9.6) |
| Dates | ISO 8601 UTC (`2026-06-14T10:30:00Z`) |
| Idempotence (sync offline) | En-tête `Idempotency-Key` ou `offline_uuid` dans le corps |

## 17.2 Document OpenAPI — extrait global

```yaml
openapi: 3.0.3
info:
  title: GesCom-BF API
  version: "1.0.0"
  description: API REST pour la gestion commerciale et de stock (quincailleries BF)
servers:
  - url: https://api.gescom-bf.com/api/v1
    description: Production
  - url: https://staging-api.gescom-bf.com/api/v1
    description: Staging

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Error:
      type: object
      properties:
        error:
          type: object
          properties:
            code: { type: string, example: "INSUFFICIENT_STOCK" }
            message: { type: string, example: "Stock insuffisant pour ce produit" }

    LoginRequest:
      type: object
      required: [email, password]
      properties:
        email: { type: string, format: email }
        password: { type: string, format: password }

    LoginResponse:
      type: object
      properties:
        access_token: { type: string }
        refresh_token: { type: string }
        user:
          type: object
          properties:
            id: { type: string, format: uuid }
            full_name: { type: string }
            role: { type: string, example: "VENDEUR" }
            branch_id: { type: string, format: uuid, nullable: true }
            permissions:
              type: array
              items: { type: string }

    Product:
      type: object
      properties:
        id: { type: string, format: uuid }
        name: { type: string }
        name_moore: { type: string, nullable: true }
        reference: { type: string }
        category_id: { type: string, format: uuid }
        brand_id: { type: string, format: uuid }
        purchase_price: { type: number, format: decimal }
        retail_price: { type: number, format: decimal }
        technician_price: { type: number, format: decimal }
        is_active: { type: boolean }

    StockItem:
      type: object
      properties:
        product_id: { type: string, format: uuid }
        branch_id: { type: string, format: uuid }
        quantity: { type: integer }
        min_stock: { type: integer }

    SaleLineInput:
      type: object
      required: [product_id, quantity]
      properties:
        product_id: { type: string, format: uuid }
        quantity: { type: integer, minimum: 1 }

    SaleCreateRequest:
      type: object
      required: [lines, channel]
      properties:
        lines:
          type: array
          items: { $ref: '#/components/schemas/SaleLineInput' }
        customer_id: { type: string, format: uuid, nullable: true }
        is_credit: { type: boolean, default: false }
        discount_rate:
          type: integer
          enum: [0, 5, 10, 15, 20]
          default: 0
        approved_by_id:
          type: string
          format: uuid
          nullable: true
          description: >
            UUID de l'administrateur ayant approuvé la remise.
            **Obligatoire si discount_rate > 0** (validé serveur — 422 sinon, RG-23).
        channel: { type: string, enum: [ONLINE, OFFLINE] }
        offline_uuid: { type: string, format: uuid, nullable: true }
        client_created_at: { type: string, format: date-time, nullable: true }

    Sale:
      type: object
      properties:
        id: { type: string, format: uuid }
        status: { type: string, enum: [VALIDEE, EN_ATTENTE_SYNC, EN_CONFLIT, ANNULEE, AVOIR_EMIS] }
        total_amount: { type: number }
        created_at: { type: string, format: date-time }

paths:

  /auth/login:
    post:
      summary: Authentification utilisateur
      tags: [Auth]
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/LoginRequest' }
      responses:
        '200':
          description: Authentification réussie
          content:
            application/json:
              schema: { $ref: '#/components/schemas/LoginResponse' }
        '401':
          description: Identifiants invalides
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Error' }
        '403':
          description: Compte désactivé
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Error' }

  /auth/refresh:
    post:
      summary: Rafraîchir l'access token via le refresh token (cookie httpOnly)
      tags: [Auth]
      security: [ { bearerAuth: [] } ]
      responses:
        '200':
          description: Nouveau token
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token: { type: string }
        '401':
          description: Refresh token invalide ou expiré
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Error' }

  /auth/logout:
    post:
      summary: Déconnexion (invalide le refresh token)
      tags: [Auth]
      security: [ { bearerAuth: [] } ]
      responses:
        '204': { description: Déconnexion réussie }

  /products:
    get:
      summary: Lister les produits
      tags: [Products]
      security: [ { bearerAuth: [] } ]
      parameters:
        - in: query
          name: search
          schema: { type: string }
          description: Recherche tolérante aux fautes (trigram)
        - in: query
          name: category_id
          schema: { type: string, format: uuid }
        - in: query
          name: page
          schema: { type: integer, default: 1 }
        - in: query
          name: per_page
          schema: { type: integer, default: 20 }
      responses:
        '200':
          description: Liste paginée des produits
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items: { $ref: '#/components/schemas/Product' }
                  meta:
                    type: object
                    properties:
                      page: { type: integer }
                      per_page: { type: integer }
                      total: { type: integer }

    post:
      summary: Créer un produit
      tags: [Products]
      security: [ { bearerAuth: [] } ]
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/Product' }
      responses:
        '201':
          description: Produit créé
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Product' }
        '400':
          description: Validation échouée (ex. technician_price > retail_price)
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Error' }
        '403':
          description: Accès refusé (RBAC)
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Error' }

  /stock:
    get:
      summary: Consulter le stock (filtré par site)
      tags: [Stock]
      security: [ { bearerAuth: [] } ]
      parameters:
        - in: query
          name: branch_id
          schema: { type: string, format: uuid }
        - in: query
          name: below_min
          schema: { type: boolean }
          description: Filtrer les produits sous le seuil minimum
      responses:
        '200':
          description: Liste des stocks
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/StockItem' }

  /transfers:
    post:
      summary: Créer un transfert (dépôt -> boutique ou boutique -> boutique)
      tags: [Transfers]
      security: [ { bearerAuth: [] } ]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [source_branch_id, dest_branch_id, lines]
              properties:
                source_branch_id: { type: string, format: uuid }
                dest_branch_id: { type: string, format: uuid }
                lines:
                  type: array
                  items:
                    type: object
                    properties:
                      product_id: { type: string, format: uuid }
                      quantity: { type: integer, minimum: 1 }
      responses:
        '201': { description: Transfert créé (statut EN_TRANSIT) }
        '409':
          description: Stock source insuffisant
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Error' }

  /transfers/{id}/receive:
    post:
      summary: Confirmer la réception d'un transfert
      tags: [Transfers]
      security: [ { bearerAuth: [] } ]
      parameters:
        - in: path
          name: id
          required: true
          schema: { type: string, format: uuid }
      responses:
        '200': { description: Transfert reçu (statut RECU), stock destination mis à jour }
        '404': { description: Transfert introuvable }

  /sales:
    post:
      summary: Enregistrer une vente
      tags: [Sales]
      security: [ { bearerAuth: [] } ]
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/SaleCreateRequest' }
      responses:
        '201':
          description: Vente enregistrée
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Sale' }
        '409':
          description: Stock insuffisant
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Error' }
        '422':
          description: Remise sans approbation administrateur
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Error' }

  /sales/refunds/pending:
    get:
      summary: Lister les avoirs en attente d'approbation
      tags: [Sales]
      security: [ { bearerAuth: [] } ]
      description: Retourne toutes les ventes au statut `EN_ATTENTE_APPROBATION`. Requiert `sales:refund`.
      responses:
        '200':
          description: Liste des avoirs en attente
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Sale' }

  /sales/{id}/refund/approve:
    patch:
      summary: Approuver un avoir en attente
      tags: [Sales]
      security: [ { bearerAuth: [] } ]
      description: Passe à `AVOIR_EMIS`, réintègre le stock et met à jour l'encours client si paiement à crédit (RG-27). Requiert `sales:refund`.
      parameters:
        - in: path
          name: id
          required: true
          schema: { type: string, format: uuid }
      responses:
        '200':
          description: Avoir approuvé
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Sale' }
        '409': { description: L'avoir n'est pas au statut EN_ATTENTE_APPROBATION }

  /sales/{id}/refund/reject:
    patch:
      summary: Rejeter un avoir en attente
      tags: [Sales]
      security: [ { bearerAuth: [] } ]
      description: Passe à `ANNULEE`. Aucune modification de stock ni d'encours. Requiert `sales:refund`.
      parameters:
        - in: path
          name: id
          required: true
          schema: { type: string, format: uuid }
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                reason: { type: string, description: Motif du rejet (optionnel) }
      responses:
        '200':
          description: Avoir rejeté
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Sale' }

  /sales/credits:
    get:
      summary: Lister les clients avec encours crédit non nul
      tags: [Sales]
      security: [ { bearerAuth: [] } ]
      description: Retourne les clients avec `credit_balance > 0`, triés par encours décroissant. Filtrable par `branch_id` et `customer_type`.
      parameters:
        - in: query
          name: branch_id
          schema: { type: string, format: uuid }
        - in: query
          name: customer_type
          schema: { type: string, enum: [SIMPLE, TECHNICIEN] }
      responses:
        '200':
          description: Liste des clients avec encours
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Customer' }

  /sales/customers/{customer_id}/settle:
    post:
      summary: Régler (partiellement ou totalement) l'encours crédit d'un client
      tags: [Sales]
      security: [ { bearerAuth: [] } ]
      description: Réduit `credit_balance` du montant indiqué. Si `amount > credit_balance`, règle la totalité. Génère un `AuditLog CREDIT_SETTLED`. Requiert `customers:write` et `sales:create`.
      parameters:
        - in: path
          name: customer_id
          required: true
          schema: { type: string, format: uuid }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [amount]
              properties:
                amount: { type: string, description: Montant à régler (Decimal en chaîne, ex. "5000.00") }
                note: { type: string, description: Commentaire optionnel (archivé dans l'audit) }
      responses:
        '200':
          description: Remboursement enregistré
          content:
            application/json:
              schema:
                type: object
                properties:
                  customer_id: { type: string, format: uuid }
                  amount_settled: { type: string }
                  new_credit_balance: { type: string }

  /analytics/ml/train:
    post:
      summary: Déclencher l'entraînement d'un modèle ML (payload JSON)
      tags: [Analytics]
      security: [ { bearerAuth: [] } ]
      description: |
        Alias body-param de `POST /analytics/ml/train/{model_type}`.
        Accepte le type de modèle dans le corps JSON — format utilisé par le client frontend.
        Par défaut synchrone ; `"async": true` délègue à Celery (avec repli synchrone si le broker est indisponible).
        Requiert `ml:train`.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [model_type]
              properties:
                model_type:
                  type: string
                  enum: [DEMAND_FORECAST, CREDIT_SCORING, ANOMALY_DETECTION, ABC_XYZ, RFM_SEGMENTATION, MARKET_BASKET]
                async:
                  type: boolean
                  default: false
      responses:
        '200':
          description: Entraînement terminé (synchrone)
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string, enum: [ok] }
                  model_type: { type: string }
                  result: { type: object }
        '202':
          description: Entraînement planifié (Celery async)
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string, enum: [queued] }
                  task_id: { type: string }
                  model_type: { type: string }
        '400': { description: Type de modèle inconnu ou manquant }


  /analytics/credit-scores/{customer_id}/explain:
    get:
      summary: "Explication SHAP du score crédit d'un client"
      tags: [Analytics]
      security: [ { bearerAuth: [] } ]
      description: |
        Retourne les facteurs les plus influents sur le score de solvabilité via SHAP TreeExplainer.
        Requiert que le modèle Random Forest ait été entraîné et son artefact sauvegardé.
        Requiert `analytics:read`.
      parameters:
        - in: path
          name: customer_id
          required: true
          schema: { type: string, format: uuid }
      responses:
        '200':
          description: Explication SHAP
          content:
            application/json:
              schema:
                type: object
                properties:
                  customer_id: { type: string }
                  score: { type: number }
                  risk_level: { type: string, enum: [FAIBLE, MOYEN, ELEVE] }
                  shap_factors:
                    type: array
                    items:
                      type: object
                      properties:
                        feature: { type: string }
                        label_fr: { type: string }
                        shap_value: { type: number }
                        direction: { type: string, enum: [positif, negatif] }
        '503': { description: Modèle ou artefact SHAP non disponible }

  /analytics/rfm-segments/evaluate-k:
    get:
      summary: Évaluation du nombre optimal de clusters K-Means (Silhouette + Elbow)
      tags: [Analytics]
      security: [ { bearerAuth: [] } ]
      description: |
        Teste k=2 à 8 clusters sur les données RFM actuelles.
        Retourne silhouette_score, davies_bouldin_score et inertia par k pour
        permettre au jury de visualiser la courbe de coude (Elbow).
        Requiert `analytics:read`.
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  k_optimal: { type: integer }
                  methode: { type: string }
                  evaluation:
                    type: array
                    items:
                      type: object
                      properties:
                        k: { type: integer }
                        silhouette: { type: number }
                        davies_bouldin: { type: number }
                        inertia: { type: number }

  /analytics/churn-risk:
    get:
      summary: Probabilité de churn par segment RFM
      tags: [Analytics]
      security: [ { bearerAuth: [] } ]
      description: |
        Calcule P(churn) = 1 - exp(-λ × recency) avec demi-vie = médiane de récence.
        Ajustement par fréquence. Retourne risk_level (LOW/MEDIUM/HIGH) et action recommandée.
        Requiert `analytics:read`.
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  customers:
                    type: array
                    items:
                      type: object
                      properties:
                        customer_id: { type: string }
                        churn_probability: { type: number, minimum: 0, maximum: 1 }
                        churn_risk: { type: string, enum: [LOW, MEDIUM, HIGH] }
                        churn_action: { type: string }

  /analytics/basket:
    get:
      summary: Règles d'association produits (Market Basket Analysis)
      tags: [Analytics]
      security: [ { bearerAuth: [] } ]
      description: |
        Retourne les règles d'association issues de l'algorithme Apriori (mlxtend).
        Si mlxtend est absent ou aucune règle trouvée, repli sur co-occurrence.
        Requiert `analytics:read`.
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  rules:
                    type: array
                    items:
                      type: object
                      properties:
                        antecedents: { type: array, items: { type: string } }
                        consequents: { type: array, items: { type: string } }
                        support: { type: number }
                        confidence: { type: number }
                        lift: { type: number }
                  algorithm: { type: string, enum: [APRIORI, CO_OCCURRENCE_FALLBACK] }
                  trained_at: { type: string, format: date-time }

  /analytics/basket/train:
    post:
      summary: Entraîner le modèle Market Basket
      tags: [Analytics]
      security: [ { bearerAuth: [] } ]
      description: |
        Lance l'entraînement dans un thread asynchrone avec contexte Flask propre.
        Réponse immédiate 202 — résultat consultable via GET /analytics/basket.
        Requiert `ml:train`.
      responses:
        '202':
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string, enum: [started] }
                  model_type: { type: string, example: MARKET_BASKET }

  /analytics/price-elasticity:
    get:
      summary: Analyse d'élasticité prix / remises
      tags: [Analytics]
      security: [ { bearerAuth: [] } ]
      description: |
        Régression log-log : ln(quantité) = α + β × ln(1 - taux_remise).
        β est l'élasticité : β < -1 = demande élastique (baisser la remise réduit les ventes).
        Recommandations de politique de remise incluses.
        Données source : Sale.discount_rate (entier 0,5,10,15,20) + SaleLine.unit_price_applied.
        Requiert `analytics:read`.
      parameters:
        - in: query
          name: months
          schema: { type: integer, default: 6 }
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  elasticity: { type: number }
                  interpretation: { type: string }
                  r_squared: { type: number }
                  recommandation_politique: { type: string }
                  par_taux:
                    type: array
                    items:
                      type: object
                      properties:
                        taux_remise_pct: { type: integer }
                        quantite_moyenne: { type: number }
                        nb_ventes: { type: integer }

  /analytics/african-context:
    get:
      summary: Contexte économique africain — Burkina Faso
      tags: [Analytics]
      security: [ { bearerAuth: [] } ]
      description: |
        Features contextuelles africaines calculées en temps réel :
        - Événements calendaires actifs (Tabaski, saison des pluies, rentrée, semaine de paie)
        - Boost weekend vendredi/samedi (marché hebdomadaire BF)
        - Indice stress trésorerie (taux de retard CustomerPayment sur 90j)
        - Propension crédit informel (clients actifs sans historique de paiement formel)
        Requiert `analytics:read`.
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  date: { type: string, format: date }
                  saison_pluies: { type: boolean }
                  active_contexts:
                    type: array
                    items:
                      type: object
                      properties:
                        event: { type: string }
                        label: { type: string }
                        impact: { type: string }
                        stock_recommendation: { type: string }
                  weekend_boost:
                    type: object
                    properties:
                      actif: { type: boolean }
                      jour: { type: string }
                      boost_estime_pct: { type: integer }
                  stress_tresorerie:
                    type: object
                    properties:
                      indice_stress_tresorerie: { type: number, minimum: 0, maximum: 1 }
                      niveau: { type: string, enum: [LOW, MEDIUM, HIGH] }
                      taux_retard_pct: { type: number }
                  credit_informel:
                    type: object
                    properties:
                      propension_credit_informel: { type: number, minimum: 0, maximum: 1 }
                      pct: { type: number }
                      interpretation: { type: string }

  /sync/sales:
    post:
      summary: Synchroniser un lot de ventes saisies hors-ligne
      tags: [Sync]
      security: [ { bearerAuth: [] } ]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                sales:
                  type: array
                  items: { $ref: '#/components/schemas/SaleCreateRequest' }
      responses:
        '200':
          description: Résultat de synchronisation par vente
          content:
            application/json:
              schema:
                type: object
                properties:
                  results:
                    type: array
                    items:
                      type: object
                      properties:
                        offline_uuid: { type: string, format: uuid }
                        status: { type: string, enum: [VALIDEE, EN_CONFLIT, DEJA_SYNCHRONISE] }
                        sale_id: { type: string, format: uuid }

  /ai/stock-predictions:
    get:
      summary: Lister les prévisions de rupture de stock
      tags: [AI]
      security: [ { bearerAuth: [] } ]
      parameters:
        - in: query
          name: branch_id
          schema: { type: string, format: uuid }
        - in: query
          name: horizon_days
          schema: { type: integer, enum: [7, 14, 30], default: 7 }
      responses:
        '200':
          description: Liste des prévisions
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    product_id: { type: string, format: uuid }
                    branch_id: { type: string, format: uuid }
                    predicted_stockout_date: { type: string, format: date, nullable: true }
                    recommended_order_qty: { type: integer }
                    model_version: { type: string }

  /ai/credit-score/{customer_id}:
    get:
      summary: Obtenir le score de solvabilité d'un client
      tags: [AI]
      security: [ { bearerAuth: [] } ]
      parameters:
        - in: path
          name: customer_id
          required: true
          schema: { type: string, format: uuid }
      responses:
        '200':
          description: Score de solvabilité
          content:
            application/json:
              schema:
                type: object
                properties:
                  customer_id: { type: string, format: uuid }
                  score: { type: number, minimum: 0, maximum: 100 }
                  risk_level: { type: string, enum: [FAIBLE, MOYEN, ELEVE] }
                  model_version: { type: string }

  /users/audit-logs:
    get:
      summary: Consulter les journaux d'audit applicatif (RF-26)
      tags: [Users]
      security: [ { bearerAuth: [] } ]
      description: Exposé sous `/users/audit-logs` (blueprint `users`). Requiert `users:read`.
      parameters:
        - in: query
          name: user_id
          schema: { type: string, format: uuid }
        - in: query
          name: event_type
          schema: { type: string }
        - in: query
          name: page
          schema: { type: integer, default: 1 }
        - in: query
          name: per_page
          schema: { type: integer, default: 50, maximum: 200 }
      responses:
        '200':
          description: Liste paginée des logs
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items: { type: object }
                  meta:
                    type: object
                    properties:
                      page: { type: integer }
                      per_page: { type: integer }
                      total: { type: integer }
        '403': { description: Accès réservé à l'administrateur }
```

## 17.3 Codes d'erreur applicatifs (référence croisée RG)

| Code | HTTP | Règle de gestion | Module |
|---|---|---|---|
| `INVALID_CREDENTIALS` | 401 | - | Auth |
| `TOKEN_EXPIRED` | 401 | RG-36 | Auth |
| `ACCOUNT_DISABLED` | 403 | - | Auth |
| `FORBIDDEN` | 403 | RBAC | Tous |
| `VALIDATION_ERROR` | 400 | RG-08 à RG-10, RG-22 | Produits, Ventes |
| `INSUFFICIENT_STOCK` | 409 | RG-18, RG-24 | Transferts, Ventes |
| `DISCOUNT_APPROVAL_REQUIRED` | 422 | RG-23 | Ventes |
| `SALE_IMMUTABLE` | 409 | RG-27 | Ventes |
| `CREDIT_REQUIRES_CUSTOMER` | 422 | RG-26 | Ventes |
| `SYNC_CONFLICT` | 200 (statut métier) | RG-29, RG-30 | Sync |

## 17.4 Endpoints — vue d'ensemble par module

| Module | Endpoints principaux |
|---|---|
| Auth | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/change-password` |
| Users | `GET/POST /users`, `GET/PUT /users/{id}`, `GET /users/roles`, `GET /users/audit-logs` |
| Products | `GET/POST /products`, `PUT /products/{id}`, `GET/POST /categories`, `GET/POST /brands`, `GET /branches` |
| Suppliers | `GET/POST /suppliers`, `GET/POST /receptions`, `POST /receptions/{id}/validate` |
| Stock | `GET /stock`, `GET /stock/movements` |
| Transfers | `GET/POST /transfers`, `POST /transfers/{id}/receive` |
| Sales | `GET/POST /sales`, `POST /sales/sync`, `GET /sales/{id}/receipt` (PDF), `POST /sales/{id}/refund`, `GET /sales/refunds/pending`, `PATCH /sales/{id}/refund/approve`, `PATCH /sales/{id}/refund/reject`, `GET /sales/credits`, `POST /sales/customers/{id}/settle` |
| Customers | `GET/POST /sales/customers`, `GET/PUT /sales/customers/{id}`, `GET/POST /sales/customers/{id}/payments`, `PUT /sales/customers/{id}/payments/{pid}` |
| Inventories | `POST /inventory`, `GET /inventory/{id}`, `POST /inventory/{id}/validate` |
| Reports | `GET /reports/dashboard`, `GET /reports/dashboard/realtime`, `GET /reports/dashboard/stream` (SSE), `GET /reports/vendeur/dashboard`, `GET /reports/export` (PDF), `GET /reports/export/sales` (Excel), `GET /reports/export/stock` (Excel), `GET /reports/export/credits` (Excel), `GET /reports/credits/pdf` (PDF), `GET /reports/compta/summary`, `GET /reports/branches/compare` |
| Analytics | `GET /analytics/dashboard`, `GET /analytics/sales-trend`, `GET /analytics/forecast`, `GET /analytics/forecast/{product_id}/{branch_id}`, `GET /analytics/credit-scores`, `GET /analytics/credit-scores/{id}/explain` (SHAP), `GET /analytics/anomalies`, `GET /analytics/abc-xyz`, `GET /analytics/rfm-segments`, `GET /analytics/rfm-segments/evaluate-k` (Silhouette/Elbow), `GET /analytics/churn-risk`, `GET /analytics/basket`, `POST /analytics/basket/train`, `GET /analytics/price-elasticity`, `GET /analytics/african-context`, `GET /analytics/cohorts`, `GET /analytics/clv`, `GET /analytics/ml/models`, `POST /analytics/ml/train` (body JSON), `POST /analytics/ml/train/{type}` (URL param) |
| Sync | `POST /sync/sales` — synchronisation ventes offline |
