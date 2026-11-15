import pytest
from flask_socketio import SocketIOTestClient

from relay.extensions import db, socketio
from relay.models import User
from relay.services import notify
from relay.services.presence import registry


@pytest.fixture(autouse=True)
def clear_presence_registry():
    registry.clear()
    yield
    registry.clear()


def _register(client, username="alice"):
    return client.post("/api/auth/register", json={"username": username, "password": "long-password"})


def test_register_logs_user_in_and_me_returns_current_user(client):
    response = _register(client, " Alice ")

    assert response.status_code == 201
    assert response.json["ok"] is True
    assert response.json["data"]["user"]["username"] == "alice"
    assert client.get("/api/auth/me").json["data"]["user"]["username"] == "alice"


def test_login_rejects_invalid_credentials_and_banned_account(app, client):
    _register(client)
    client.post("/api/auth/logout")

    invalid = client.post("/api/auth/login", json={"username": "alice", "password": "wrong-password"})
    assert invalid.status_code == 401
    assert invalid.json["error"]["code"] == "INVALID_CREDENTIALS"

    with app.app_context():
        user = User.query.filter_by(username="alice").one()
        user.banned_at = user.created_at
        db.session.commit()

    banned = client.post("/api/auth/login", json={"username": "alice", "password": "long-password"})
    assert banned.status_code == 403
    assert banned.json["error"]["code"] == "BANNED"


def test_anonymous_logout_requires_authentication(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 401
    assert response.json["error"]["code"] == "AUTH_REQUIRED"


def test_logout_terminates_active_socket_and_revokes_session(app, client, monkeypatch):
    _register(client)
    with app.app_context():
        user = User.query.filter_by(username="alice").one()
        old_session_id = user.get_id()
        user_id = user.id

    socket_client: SocketIOTestClient = socketio.test_client(app, flask_test_client=client)
    assert socket_client.is_connected()
    assert registry.is_online(user_id)

    emitted = []
    original_emit = notify._emit

    def record_emit(event, data, to, skip_sid=None):
        emitted.append((event, data, to))
        return original_emit(event, data, to, skip_sid)

    monkeypatch.setattr(notify, "_emit", record_emit)
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert not socket_client.is_connected()
    assert not registry.is_online(user_id)
    with app.app_context():
        assert User.query.filter_by(username="alice").one().session_version == 2
        assert app.login_manager._user_callback(old_session_id) is None
    assert ("session:terminated", {"reason": "logout"}, notify.user_channel(user_id)) in emitted


def test_me_returns_null_without_a_session(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json["data"]["user"] is None

