from http import HTTPStatus

from flask import jsonify


def json_response(status_code, message, response=None):
    try:
        status_text = HTTPStatus(status_code).phrase
    except ValueError:
        status_text = "Unknown"
    payload = {"status": status_text, "message": message, "response": response}
    return jsonify(payload), status_code
