"""Reports, bans, mutes and content removal (CHAT-F-046…F-049, F-051; CHAT-SR-012, SR-013)."""

from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from relay.errors import RelayError
from relay.extensions import db
from relay.models import Message, Report, User
from relay.models._time import utcnow
from relay.services import audit, auth, messages, notify, rooms

MUTE_MIN_MINUTES = 15
MUTE_MAX_MINUTES = 10080  # 7 days
REPORT_STATUSES = ("open", "resolved", "dismissed")


def require_admin(actor: User) -> None:
    if not actor or not actor.is_admin:
        raise RelayError("FORBIDDEN", "Administrators only")


def _reason(raw, required: bool = True) -> str:
    reason = raw.strip() if isinstance(raw, str) else ""
    if required and not reason:
        raise RelayError("VALIDATION_ERROR", "Please give a reason")
    if len(reason) > 200:
        raise RelayError("VALIDATION_ERROR", "Reason must be at most 200 characters")
    return reason


def _close(rep: Report, status: str, actor: User) -> None:
    rep.status, rep.resolved_by, rep.resolved_at = status, actor.id, utcnow()


# ---------------------------------------------------------------- reports (any member)

def report(user_id: int, message_id, reason) -> Report:
    msg = db.session.get(Message, message_id) if type(message_id) is int else None
    if not msg or msg.deleted_at:
        raise RelayError("NOT_FOUND", "Message not found")
    rooms.require_member(msg.room_id, user_id)  # non-members get NOT_FOUND
    rep = Report(message_id=msg.id, reporter_id=user_id, reason=_reason(reason))
    db.session.add(rep)
    try:
        db.session.commit()
    except IntegrityError:  # unique (message_id, reporter_id)
        db.session.rollback()
        raise RelayError("VALIDATION_ERROR", "You have already reported this message") from None
    return rep


def list_reports(actor: User, status: str = "open") -> list[Report]:
    require_admin(actor)
    q = Report.query
    if status in REPORT_STATUSES:
        q = q.filter_by(status=status)
    return q.order_by(Report.id.desc()).limit(200).all()


def delete_message(actor: User, message_id, reason="") -> Message:
    """Admin soft delete: one audit row, open reports on it resolved, live message:updated."""
    require_admin(actor)
    msg = db.session.get(Message, message_id) if type(message_id) is int else None
    if not msg:
        raise RelayError("NOT_FOUND", "Message not found")
    reason = _reason(reason, required=False)
    if not msg.deleted_at:
        messages.soft_delete(msg)
        audit.record(actor.id, "message.delete", "message", msg.id, reason)
    for rep in Report.query.filter_by(message_id=msg.id, status="open"):
        _close(rep, "resolved", actor)
    db.session.commit()
    notify.message_updated(msg)
    return msg


def resolve_report(actor: User, report_id, action, reason="") -> Report:
    require_admin(actor)
    rep = db.session.get(Report, report_id) if type(report_id) is int else None
    if not rep:
        raise RelayError("NOT_FOUND", "Report not found")
    if rep.status != "open":
        raise RelayError("VALIDATION_ERROR", "This report is already closed")
    if action == "delete":
        default = f"report #{rep.id}: {rep.reason}"[:200]
        delete_message(actor, rep.message_id, reason or default)
    elif action == "dismiss":
        _close(rep, "dismissed", actor)
        audit.record(actor.id, "report.dismiss", "report", rep.id, _reason(reason, required=False))
        db.session.commit()
    else:
        raise RelayError("VALIDATION_ERROR", "Action must be delete or dismiss")
    return rep


# ---------------------------------------------------------------- user sanctions

def _target(actor: User, user_id) -> User:
    require_admin(actor)
    user = db.session.get(User, user_id) if type(user_id) is int else None
    if not user:
        raise RelayError("NOT_FOUND", "User not found")
    if user.id == actor.id or user.is_admin:
        raise RelayError("FORBIDDEN", "Administrators cannot be sanctioned")
    return user


def list_users(actor: User) -> list[User]:
    require_admin(actor)
    return User.query.order_by(User.username).all()


def ban(actor: User, user_id, reason) -> User:
    """Ban, revoke every session and drop the user's sockets at once (CHAT-SR-013). No-op if already banned."""
    user = _target(actor, user_id)
    reason = _reason(reason)
    if not user.banned_at:
        user.banned_at = utcnow()
        audit.record(actor.id, "user.ban", "user", user.id, reason)
        auth.revoke_sessions(user)  # commits the ban, the audit row and the new session version
        notify.terminate_sessions(user.id, "banned")
    return user


def unban(actor: User, user_id, reason="") -> User:
    user = _target(actor, user_id)
    reason = _reason(reason, required=False)
    if user.banned_at:
        user.banned_at = None
        audit.record(actor.id, "user.unban", "user", user.id, reason)
        db.session.commit()
    return user


def mute(actor: User, user_id, minutes, reason) -> User:
    user = _target(actor, user_id)
    if type(minutes) is not int or not MUTE_MIN_MINUTES <= minutes <= MUTE_MAX_MINUTES:
        raise RelayError("VALIDATION_ERROR", "Mute for 15 minutes to 7 days")
    reason = _reason(reason)
    user.muted_until = utcnow() + timedelta(minutes=minutes)
    audit.record(actor.id, "user.mute", "user", user.id, f"{minutes} min: {reason}")
    db.session.commit()
    return user


def unmute(actor: User, user_id, reason="") -> User:
    user = _target(actor, user_id)
    reason = _reason(reason, required=False)
    if user.is_muted:
        user.muted_until = None
        audit.record(actor.id, "user.unmute", "user", user.id, reason)
        db.session.commit()
    return user
