"""Message search endpoint (CHAT-F-041)."""

from flask import jsonify, request
from flask_login import current_user, login_required

from relay.api import api_bp
from relay.errors import ok
from relay.services import search


@api_bp.get("/search")
@login_required
def search_messages():
    results = search.search(current_user.id, request.args.get("q"), request.args.get("room_id"))
    return jsonify(ok({"messages": [m.to_dict() for m in results]}))
