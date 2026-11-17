"""User lookup for starting private conversations (CHAT-F-006)."""

from flask import jsonify, request
from flask_login import current_user, login_required

from relay.api import api_bp
from relay.errors import ok
from relay.models import User
from relay.services.auth import normalize_username
from relay.services.presence import registry


@api_bp.get("/users")
@login_required
def search_users():
    q = normalize_username(request.args.get("q"))[:20]
    query = User.query.filter(User.id != current_user.id)
    if q:
        # Escape LIKE wildcards so "_" or "%" in the query are matched literally (CHAT-SR-011)
        pattern = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        query = query.filter(User.username.like(pattern, escape="\\"))
    users = query.order_by(User.username).limit(20).all()
    return jsonify(ok({"users": [{**u.to_public(), "online": registry.is_online(u.id)} for u in users]}))
