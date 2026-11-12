"""Message search, scoped to the user's own conversations (CHAT-F-041; CHAT-SR-008, SR-011)."""

from relay.errors import RelayError
from relay.models import Message, RoomMember

MAX_RESULTS = 50


def _like_escape(text: str) -> str:
    # %, _ and \ are matched literally
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _room_filter(room_id) -> int | None:
    if room_id is None or room_id == "":
        return None
    if type(room_id) is bool:
        raise RelayError("VALIDATION_ERROR", "room_id must be an integer")
    try:
        return int(room_id)
    except (TypeError, ValueError):
        raise RelayError("VALIDATION_ERROR", "room_id must be an integer") from None


def search(user_id: int, q, room_id=None) -> list[Message]:
    """Case-insensitive substring search, newest first, at most 50 results, deleted messages excluded."""
    q = q.strip() if isinstance(q, str) else ""
    if not 2 <= len(q) <= 100:
        raise RelayError("VALIDATION_ERROR", "Search for 2-100 characters")
    room = _room_filter(room_id)
    # The join on (room_id, user_id) limits results to rooms the user is a member of.
    query = (Message.query
             .join(RoomMember, (RoomMember.room_id == Message.room_id) & (RoomMember.user_id == user_id))
             .filter(Message.deleted_at.is_(None), Message.body.ilike(f"%{_like_escape(q)}%", escape="\\")))
    if room is not None:
        query = query.filter(Message.room_id == room)
    return query.order_by(Message.id.desc()).limit(MAX_RESULTS).all()
