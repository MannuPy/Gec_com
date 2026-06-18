/**
 * Format d'erreur homogene de l'API.
 * Cf. backend/app/utils/errors.py (ApiError.to_response).
 */
export interface ApiErrorBody {
  error: string;
  message: string;
  details?: unknown;
}

/**
 * Enveloppe de pagination utilisee par l'API (cf. 17-API-REST.md).
 * Exemple : GET /products -> { data: [...], meta: { page, per_page, total } }.
 */
export interface Paginated<T> {
  data: T[];
  meta: {
    page: number;
    per_page: number;
    total: number;
  };
}
