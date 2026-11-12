"""Reporting and administration (CHAT-F-046…F-049, F-051, F-052; CHAT-SR-012, SR-013).

Every admin rule (role check, valid targets, reasons) lives in services/moderation.py.
"""

from flask import jsonify, request
from flask_login import current_user, login_required

from relay.api import api_bp, json_body
from relay.errors import RelayError, ok
from relay.services import activity, audit, moderation


def _actor():
    return current_user._get_current_object()


@api_bp.post("/messages/<int:message_id>/report")
@login_required
def report_message(message_id: int):
    rep = moderation.report(current_user.id, message_id, json_body().get("reason"))
    return jsonify(ok({"report": {"id": rep.id, "status": rep.status}})), 201


@api_bp.get("/admin/reports")
@login_required
def list_reports():
    reports = moderation.list_reports(_actor(), request.args.get("status", "open"))
    return jsonify(ok({"reports": [r.to_dict() for r in reports]}))


@api_bp.post("/admin/reports/<int:report_id>/resolve")
@login_required
def resolve_report(report_id: int):
    body = json_body()
    rep = moderation.resolve_report(_actor(), report_id, body.get("action"), body.get("reason"))
    return jsonify(ok({"report": rep.to_dict()}))


@api_bp.delete("/admin/messages/<int:message_id>")
@login_required
def delete_message(message_id: int):
    moderation.delete_message(_actor(), message_id, json_body().get("reason"))
    return jsonify(ok())


@api_bp.get("/admin/users")
@login_required
def list_users():
    return jsonify(ok({"users": [u.to_admin() for u in moderation.list_users(_actor())]}))


@api_bp.post("/admin/users/<int:user_id>/<action>")
@login_required
def sanction(user_id: int, action: str):
    body = json_body()
    actor = _actor()
    if action == "ban":
        user = moderation.ban(actor, user_id, body.get("reason"))
    elif action == "unban":
        user = moderation.unban(actor, user_id, body.get("reason"))
    elif action == "mute":
        user = moderation.mute(actor, user_id, body.get("minutes"), body.get("reason"))
    elif action == "unmute":
        user = moderation.unmute(actor, user_id, body.get("reason"))
    else:
        raise RelayError("NOT_FOUND", "Unknown action")
    return jsonify(ok({"user": user.to_admin()}))


@api_bp.get("/admin/audit")
@login_required
def audit_log():
    moderation.require_admin(_actor())
    return jsonify(ok({"entries": [e.to_dict() for e in audit.recent()]}))


@api_bp.get("/admin/clients")
@login_required
def connected_clients():
    moderation.require_admin(_actor())
    return jsonify(ok({"clients": activity.connected_clients()}))


@api_bp.get("/admin/activity")
@login_required
def activity_log():
    moderation.require_admin(_actor())
    return jsonify(ok({"entries": [e.to_dict() for e in activity.recent()]}))
