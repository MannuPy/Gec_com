"""
Gestion centralisée des erreurs API.

Tous les codes d'erreur métier sont référencés dans `17-API-REST.md`
(table "Référence des codes d'erreur"). Le format de réponse d'erreur est
homogène sur toute l'API :

    {
        "error": "INSUFFICIENT_STOCK",
        "message": "Stock insuffisant pour le produit ...",
        "details": { ... }   # optionnel
    }
"""
from flask import jsonify
from marshmallow import ValidationError


class ApiError(Exception):
    """Exception métier porteuse d'un code d'erreur API et d'un statut HTTP."""

    def __init__(self, code: str, message: str, status_code: int = 400, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_response(self):
        body = {"error": self.code, "message": self.message}
        if self.details is not None:
            body["details"] = self.details
        return jsonify(body), self.status_code


# ---- Raccourcis pour les erreurs les plus fréquentes (cf. 17-API-REST.md) ----

def not_found(entity: str, entity_id=None) -> ApiError:
    message = f"{entity} introuvable."
    if entity_id is not None:
        message = f"{entity} '{entity_id}' introuvable."
    return ApiError("NOT_FOUND", message, status_code=404)


def forbidden(message: str = "Accès refusé.") -> ApiError:
    return ApiError("FORBIDDEN", message, status_code=403)


def validation_error(message: str, details=None) -> ApiError:
    return ApiError("VALIDATION_ERROR", message, status_code=400, details=details)


def conflict(code: str, message: str, details=None) -> ApiError:
    return ApiError(code, message, status_code=409, details=details)


def register_error_handlers(app):
    """Enregistre les gestionnaires d'erreurs globaux sur l'application Flask."""

    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return err.to_response()

    @app.errorhandler(ValidationError)
    def handle_marshmallow_error(err: ValidationError):
        return jsonify({
            "error": "VALIDATION_ERROR",
            "message": "Les données fournies sont invalides.",
            "details": err.messages,
        }), 400

    @app.errorhandler(404)
    def handle_404(_err):
        return jsonify({"error": "NOT_FOUND", "message": "Ressource introuvable."}), 404

    @app.errorhandler(405)
    def handle_405(_err):
        return jsonify({"error": "METHOD_NOT_ALLOWED", "message": "Méthode non autorisée."}), 405

    @app.errorhandler(500)
    def handle_500(_err):
        return jsonify({"error": "INTERNAL_ERROR", "message": "Une erreur interne est survenue."}), 500
