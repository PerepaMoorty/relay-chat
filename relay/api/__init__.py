"""REST API for request/response resources. See docs/architecture.md section 6."""

from flask import Blueprint, jsonify, request

from relay.errors import RelayError, fail
from relay.extensions import db

api_bp = Blueprint("api", __name__)


@api_bp.errorhandler(RelayError)
def handle_relay_error(err: RelayError):
    db.session.rollback()
    return jsonify(fail(err)), err.status


def json_body() -> dict:
    """The request's JSON object, or {} when the body is missing or not an object."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@api_bp.get("/health")
def health():
    return jsonify(status="ok")


# Each module registers its routes on api_bp when imported. The list is complete from B1 on,
# so later PRs only replace module contents and never edit this file.
from relay.api import admin, auth, files, rooms, search, users  # noqa: E402, F401
