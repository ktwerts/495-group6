"""Shared exceptions and error handlers.

Service functions raise these; the handlers turn them into consistent JSON
responses ({"error": "...", ...}) for /api routes.
"""

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException


class ValidationError(ValueError):
    """Bad input from the client -> 400."""


class NotFoundError(LookupError):
    """Requested record does not exist -> 404."""


class ConflictError(Exception):
    """Request breaks a scheduling rule -> 409. Carries a list of violations."""

    def __init__(self, message: str, violations: list[str] | None = None):
        super().__init__(message)
        self.violations = violations or []


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationError)
    def handle_validation(exc):
        return jsonify(error=str(exc)), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found(exc):
        return jsonify(error=str(exc)), 404

    @app.errorhandler(ConflictError)
    def handle_conflict(exc):
        return jsonify(error=str(exc), violations=exc.violations), 409

    @app.errorhandler(NotImplementedError)
    def handle_not_implemented(exc):
        # Scaffold stubs raise NotImplementedError until a teammate builds them.
        return jsonify(error=f"Not implemented yet: {exc}"), 501

    @app.errorhandler(HTTPException)
    def handle_http(exc):
        if request.path.startswith("/api/"):
            return jsonify(error=exc.description), exc.code
        return exc

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        if isinstance(exc, HTTPException):
            return handle_http(exc)
        app.logger.exception("Unhandled error")
        if app.config.get("TESTING"):
            raise exc
        return jsonify(error="Internal server error"), 500
