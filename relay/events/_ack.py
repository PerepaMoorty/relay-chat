"""Uniform ack envelope for client → server events (docs/architecture.md section 5.3)."""

from functools import wraps

from flask import current_app, request
from flask_login import current_user

from relay.errors import RelayError, fail, ok
from relay.extensions import db
from relay.services import activity
from relay.services.presence import registry


def acked(handler):
    """Run an event handler and turn its result or error into {ok, data | error}.

    Events from a socket that is no longer registered, or whose session was revoked, are refused
    (CHAT-SR-005). Unexpected exceptions are logged and never reach the client or stop the server
    (CHAT-F-013, F-017).
    """

    @wraps(handler)
    def wrapper(payload=None, *_args):
        uid = registry.user_for(request.sid)
        if uid is None or not current_user.is_authenticated or current_user.id != uid:
            return fail(RelayError("AUTH_REQUIRED", "Your session is no longer active"))
        try:
            return ok(handler(payload if isinstance(payload, dict) else {}))
        except RelayError as err:
            db.session.rollback()
            return fail(err)
        except Exception as exc:
            db.session.rollback()
            current_app.logger.exception("Unhandled error in socket event %s", handler.__name__)
            try:
                activity.log("error", uid, f"{handler.__name__}: {type(exc).__name__}")
            except Exception:
                db.session.rollback()
            return fail(RelayError("INTERNAL", "Something went wrong"))

    return wrapper
