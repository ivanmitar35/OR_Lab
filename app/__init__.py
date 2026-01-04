from flask import Flask, request
from werkzeug.exceptions import HTTPException, InternalServerError, MethodNotAllowed

from .api_response import json_response

def create_app():
    app = Flask(__name__)

    from .routes import main
    app.register_blueprint(main)

    @app.errorhandler(MethodNotAllowed)
    def handle_method_not_allowed(error):
        if request.path.startswith("/api/"):
            return json_response(
                501,
                "Method not implemented for requested resource.",
                {"detail": "Method not implemented for requested resource."},
            )
        return error

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        if request.path.startswith("/api/"):
            message = error.description or error.name
            return json_response(error.code or 500, message, {"detail": message})
        return error

    @app.errorhandler(Exception)
    def handle_exception(error):
        if request.path.startswith("/api/"):
            return json_response(
                500,
                "Unexpected server error.",
                {"detail": str(error)},
            )
        if isinstance(error, HTTPException):
            return error
        return InternalServerError()

    return app
