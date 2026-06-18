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
        approved_by_user_id: { type: string, format: uuid, nullable: true }
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

  /audit:
    get:
      summary: Consulter les journaux d'audit
      tags: [Audit]
      security: [ { bearerAuth: [] } ]
      parameters:
        - in: query
          name: user_id
          schema: { type: string, format: uuid }
        - in: query
          name: event_type
          schema: { type: string }
        - in: query
          name: from
          schema: { type: string, format: date }
        - in: query
          name: to
          schema: { type: string, format: date }
      responses:
        '200': { description: Liste paginée des logs }
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
| Users | `GET/POST /users`, `PATCH /users/{id}`, `GET /roles` |
| Products | `GET/POST /products`, `PATCH /products/{id}`, `GET/POST /categories`, `GET/POST /brands` |
| Suppliers | `GET/POST /suppliers`, `POST /suppliers/{id}/receptions` |
| Stock | `GET /stock`, `GET /stock/movements` |
| Transfers | `GET/POST /transfers`, `POST /transfers/{id}/receive`, `POST /transfers/{id}/cancel` |
| Sales | `GET/POST /sales`, `GET /sales/{id}/receipt` (PDF) |
| Sync | `POST /sync/sales` |
| Inventories | `POST /inventories`, `PATCH /inventories/{id}/lines`, `POST /inventories/{id}/validate` |
| Reports | `GET /reports/dashboard`, `GET /reports/sales`, `GET /reports/export` (PDF) |
| Analytics | `GET /analytics/abc-xyz`, `GET /analytics/rfm` |
| AI | `GET /ai/stock-predictions`, `GET /ai/credit-score/{id}`, `GET /ai/anomalies` |
| Audit | `GET /audit` |
