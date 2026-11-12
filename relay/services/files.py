"""Uploads and members-only downloads (CHAT-F-037, F-038, F-039; CHAT-SR-010)."""

import secrets
from pathlib import Path

from flask import current_app

from relay.errors import RelayError
from relay.extensions import db
from relay.models import Attachment, Message, RoomMember

TEXT_SAMPLE = 4096


def _is_text(data: bytes) -> bool:
    head = data[:TEXT_SAMPLE]
    if b"\x00" in head:
        return False
    try:
        head.decode("utf-8")
        return True
    except UnicodeDecodeError as err:
        # A multi-byte character may be cut at the end of the sample; that is still text
        return len(data) > TEXT_SAMPLE and err.start >= len(head) - 3


def _zip(data: bytes) -> bool:
    return data.startswith(b"PK\x03\x04")


# extension -> (MIME type, signature check on the file's bytes). The content must match the extension.
ALLOWED = {
    "png": ("image/png", lambda b: b.startswith(b"\x89PNG\r\n\x1a\n")),
    "jpg": ("image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
    "jpeg": ("image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
    "gif": ("image/gif", lambda b: b[:6] in (b"GIF87a", b"GIF89a")),
    "webp": ("image/webp", lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
    "pdf": ("application/pdf", lambda b: b.startswith(b"%PDF")),
    "txt": ("text/plain", _is_text),
    "md": ("text/markdown", _is_text),
    "csv": ("text/csv", _is_text),
    "zip": ("application/zip", _zip),
    "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", _zip),
    "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", _zip),
    "pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", _zip),
}


def upload_dir() -> Path:
    """instance/uploads/, outside static/, so stored files are never served directly."""
    path = Path(current_app.instance_path) / current_app.config["UPLOAD_DIR"]
    path.mkdir(parents=True, exist_ok=True)
    return path


def _display_name(filename: str) -> str:
    # Keep only the last path part, whichever separator the browser used
    name = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    return (name or "file")[:255]


def save(uploader_id: int, storage) -> Attachment:
    if storage is None or not storage.filename:
        raise RelayError("VALIDATION_ERROR", "No file was sent")
    name = _display_name(storage.filename)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED:
        raise RelayError("UNSUPPORTED_TYPE", "That file type is not allowed")
    limit = current_app.config["MAX_UPLOAD_BYTES"]
    data = storage.read(limit + 1)
    if len(data) > limit:
        raise RelayError("PAYLOAD_TOO_LARGE", "Files can be at most 10 MB")
    if not data:
        raise RelayError("VALIDATION_ERROR", "The file is empty")
    mime, matches = ALLOWED[ext]
    if not matches(data):
        raise RelayError("UNSUPPORTED_TYPE", "The file content does not match its type")
    stored = secrets.token_hex(16)  # random name, no extension
    (upload_dir() / stored).write_bytes(data)
    att = Attachment(uploader_id=uploader_id, original_name=name, stored_name=stored,
                     mime_type=mime, size_bytes=len(data))
    db.session.add(att)
    db.session.commit()
    return att


def open_for(user_id: int, attachment_id) -> tuple[Attachment, Path]:
    """The uploader, or a member of the room where the (not deleted) message carrying it was sent."""
    att = db.session.get(Attachment, attachment_id) if type(attachment_id) is int else None
    if not att:
        raise RelayError("NOT_FOUND", "File not found")
    if att.uploader_id != user_id:
        msg = Message.query.filter_by(attachment_id=att.id).first()
        if not msg or msg.deleted_at or not db.session.get(RoomMember, (msg.room_id, user_id)):
            raise RelayError("FORBIDDEN", "You do not have access to this file")
    path = upload_dir() / att.stored_name
    if not path.is_file():
        raise RelayError("NOT_FOUND", "File not found")
    return att, path
