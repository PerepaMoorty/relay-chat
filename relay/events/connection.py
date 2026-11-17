"""connect / disconnect: handshake auth, channels and presence
(CHAT-F-001, F-009…F-015, F-019; CHAT-SR-001, SR-005, SR-007, SR-014)."""

import threading

from flask import current_app, request
from flask_login import current_user
from flask_socketio import join_room

from relay.extensions import db, socketio
from relay.models import User
from relay.models._time import utcnow
from relay.services import activity, notify, rooms
from relay.services.presence import registry

# user_id -> token of a pending "went offline" announcement; a reconnect within the grace period cancels it
_pending_offline: dict[int, object] = {}
_pending_lock = threading.Lock()


@socketio.on("connect")
def on_connect(auth=None):
    # current_user is None-like for no cookie, a stale session version or a banned user (CHAT-SR-007)
    if not current_user.is_authenticated:
        # Return False rather than raising ConnectionRefusedError: with on_error_default registered,
        # Flask-SocketIO would pass the exception to that handler and accept the connection.
        return False
    user = db.session.get(User, current_user.id)
    first = registry.add(request.sid, user.id)
    activity.log("connect", user.id, f"socket {request.sid[:8]} from {request.remote_addr}")

    join_room(notify.user_channel(user.id))
    join_room(notify.PRESENCE)
    for room in rooms.rooms_for(user.id):
        join_room(notify.room_channel(room.id))

    online = User.query.filter(User.id.in_(registry.online_user_ids())).order_by(User.username).all()
    notify.presence_snapshot(request.sid, online)

    with _pending_lock:
        reconnected_in_grace = _pending_offline.pop(user.id, None) is not None
    if first and not reconnected_in_grace:
        notify.presence_changed(user, online=True)


@socketio.on("disconnect")
def on_disconnect(*_reason):
    user_id, was_last = registry.remove(request.sid)
    if user_id is None:
        return
    activity.log("disconnect", user_id, f"socket {request.sid[:8]}")
    if not was_last:
        return
    grace = current_app.config["PRESENCE_GRACE_SECONDS"]
    if not grace:
        _go_offline(user_id)
        return
    # A page refresh reconnects within the grace period, so nobody sees a "left / joined" flash.
    token = object()
    with _pending_lock:
        _pending_offline[user_id] = token
    socketio.start_background_task(_offline_after_grace, current_app._get_current_object(), user_id, token, grace)


def _offline_after_grace(app, user_id: int, token: object, grace: float) -> None:
    socketio.sleep(grace)
    with _pending_lock:
        if _pending_offline.get(user_id) is not token:
            return  # the user came back, or a newer disconnect owns the announcement
        del _pending_offline[user_id]
    if registry.is_online(user_id):
        return
    with app.app_context():
        _go_offline(user_id)


def _go_offline(user_id: int) -> None:
    user = db.session.get(User, user_id)
    if not user:
        return
    user.last_seen_at = utcnow()
    db.session.commit()
    notify.presence_changed(user, online=False)


@socketio.on_error_default
def on_error(err):
    # Last line of defence; handlers wrapped in @acked already turn errors into error acks.
    current_app.logger.exception("Socket.IO handler error: %s", err)
