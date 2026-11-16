from relay.extensions import db
from relay.models import Activity, User
from relay.services import activity
from relay.services.presence import PresenceRegistry


def test_log_persists_activity_and_truncates_detail(app):
    with app.app_context():
        user = User(username="alice", password_hash="unused")
        db.session.add(user)
        db.session.commit()

        activity.log("connect", user.id, "x" * 250)

        entry = Activity.query.one()
        assert entry.kind == "connect"
        assert entry.user_id == user.id
        assert entry.detail == "x" * 200


def test_log_defaults_to_anonymous_user_and_empty_detail(app):
    with app.app_context():
        activity.log("error")

        entry = Activity.query.one()
        assert entry.kind == "error"
        assert entry.user_id is None
        assert entry.detail == ""
        assert entry.to_dict()["user"] is None


def test_recent_returns_newest_entries_first_and_respects_limit(app):
    with app.app_context():
        activity.log("connect", detail="first")
        activity.log("disconnect", detail="second")
        activity.log("error", detail="third")

        entries = activity.recent(limit=2)

        assert [entry.detail for entry in entries] == ["third", "second"]


def test_connected_clients_returns_public_socket_details(app, monkeypatch):
    registry = PresenceRegistry()
    monkeypatch.setattr(activity, "registry", registry)

    with app.app_context():
        user = User(username="alice", password_hash="unused")
        db.session.add(user)
        db.session.commit()
        registry.add("12345678-extra", user.id)

        assert activity.connected_clients() == [
            {
                "sid": "12345678",
                "username": "alice",
                "connected_at": registry.snapshot()[0]["connected_at"].isoformat(timespec="seconds") + "Z",
            }
        ]


def test_connected_clients_is_empty_when_no_sockets(app, monkeypatch):
    monkeypatch.setattr(activity, "registry", PresenceRegistry())

    with app.app_context():
        assert activity.connected_clients() == []
