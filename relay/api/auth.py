"""Registration, login, logout and the current user (CHAT-F-002, F-003, F-014, F-018, F-019)."""

from flask import jsonify
from flask_login import current_user, login_required, login_user, logout_user

from relay.api import api_bp, json_body
from relay.errors import ok
from relay.services import auth, notify


@api_bp.post("/auth/register")
def register():
    body = json_body()
    user = auth.register(body.get("username"), body.get("password"))
    login_user(user)
    return jsonify(ok({"user": user.to_public()})), 201


@api_bp.post("/auth/login")
def login():
    body = json_body()
    user = auth.authenticate(body.get("username"), body.get("password"))
    login_user(user)
    return jsonify(ok({"user": user.to_public()}))


@api_bp.post("/auth/logout")
@login_required
def logout():
    user = current_user._get_current_object()
    auth.revoke_sessions(user)  # every tab's cookie stops working
    notify.terminate_sessions(user.id, "logout")
    logout_user()
    return jsonify(ok())


@api_bp.get("/auth/me")
def me():
    # Always 200 (user is null when logged out), so the client can check its session quietly
    return jsonify(ok({"user": current_user.to_public() if current_user.is_authenticated else None}))
