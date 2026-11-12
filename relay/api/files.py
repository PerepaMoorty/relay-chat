"""Attachment upload and members-only download (CHAT-F-037, F-038, F-039; CHAT-SR-010)."""

from flask import jsonify, request, send_file
from flask_login import current_user, login_required

from relay.api import api_bp
from relay.errors import ok
from relay.services import files


@api_bp.post("/files")
@login_required
def upload():
    att = files.save(current_user.id, request.files.get("file"))
    return jsonify(ok({"attachment": att.to_dict()})), 201


@api_bp.get("/files/<int:attachment_id>")
@login_required
def download(attachment_id: int):
    att, path = files.open_for(current_user.id, attachment_id)
    # Images may render inline (preview); everything else is always downloaded, never rendered.
    resp = send_file(path, mimetype=att.mime_type, as_attachment=not att.is_image,
                     download_name=att.original_name, max_age=0)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Cache-Control"] = "private, no-store"
    return resp
