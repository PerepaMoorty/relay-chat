import pytest

from relay.extensions import socketio
from relay.models import Message, Room
from relay.services.presence import registry


@pytest.fixture(autouse=True)
def clear_presence_registry():
    registry.clear()
    yield
    registry.clear()


def _account(app, username):
    client = app.test_client()
    response = client.post("/api/auth/register", json={"username": username, "password": "long-password"})
    assert response.status_code == 201
    return client, response.json["data"]["user"]["id"]


def _connect(app, client, clear_received=True):
    socket_client = socketio.test_client(app, flask_test_client=client)
    assert socket_client.is_connected()
    if clear_received:
        socket_client.get_received()
    return socket_client


def _events(socket_client, name):
    return [event for event in socket_client.get_received() if event["name"] == name]


def test_two_clients_receive_room_message_and_acknowledgement(app):
    alice_http, alice_id = _account(app, "alice")
    bob_http, _bob_id = _account(app, "bob")
    alice = _connect(app, alice_http)
    bob = _connect(app, bob_http)
    with app.app_context():
        general_id = Room.query.filter_by(kind="public", name="general").one().id

    ack = alice.emit(
        "message:send",
        {"room_id": general_id, "body": "hello Bob", "client_id": "live-1"},
        callback=True,
    )
    alice_events = _events(alice, "message:new")
    bob_events = _events(bob, "message:new")

    assert ack["ok"] is True
    assert ack["data"]["message"]["sender"]["id"] == alice_id
    assert len(alice_events) == len(bob_events) == 1
    assert alice_events[0]["args"][0] == bob_events[0]["args"][0]
    assert bob_events[0]["args"][0]["message"]["body"] == "hello Bob"


def test_room_broadcast_does_not_rebroadcast_idempotent_retry(app):
    alice_http, _alice_id = _account(app, "alice")
    bob_http, _bob_id = _account(app, "bob")
    alice = _connect(app, alice_http)
    bob = _connect(app, bob_http)
    with app.app_context():
        general_id = Room.query.filter_by(kind="public", name="general").one().id

    first = alice.emit(
        "message:send", {"room_id": general_id, "body": "once", "client_id": "retry-me"}, callback=True
    )
    _events(alice, "message:new")
    _events(bob, "message:new")
    repeated = alice.emit(
        "message:send", {"room_id": general_id, "body": "once", "client_id": "retry-me"}, callback=True
    )

    assert first["ok"] is True and repeated["ok"] is True
    assert first["data"]["message"]["id"] == repeated["data"]["message"]["id"]
    assert _events(alice, "message:new") == []
    assert _events(bob, "message:new") == []
    with app.app_context():
        assert Message.query.filter_by(client_id="retry-me").count() == 1


def test_direct_message_reaches_only_the_two_dm_members(app):
    alice_http, _alice_id = _account(app, "alice")
    bob_http, bob_id = _account(app, "bob")
    carol_http, _carol_id = _account(app, "carol")
    alice = _connect(app, alice_http)
    bob = _connect(app, bob_http)
    carol = _connect(app, carol_http)

    dm = alice_http.post("/api/dms", json={"user_id": bob_id}).json["data"]["room"]
    for socket_client in (alice, bob, carol):
        socket_client.get_received()

    ack = alice.emit(
        "message:send", {"room_id": dm["id"], "body": "private", "client_id": "dm-1"}, callback=True
    )

    assert ack["ok"] is True
    assert len(_events(alice, "message:new")) == 1
    assert len(_events(bob, "message:new")) == 1
    assert _events(carol, "message:new") == []


def test_presence_snapshot_and_last_socket_transition_are_visible_to_other_clients(app):
    alice_http, alice_id = _account(app, "alice")
    watcher_http, _watcher_id = _account(app, "watcher")
    watcher = _connect(app, watcher_http)
    alice_first = _connect(app, alice_http, clear_received=False)
    snapshot = _events(alice_first, "presence:snapshot")
    assert len(snapshot) == 1
    assert alice_id in {user["id"] for user in snapshot[0]["args"][0]["users"]}

    watcher.get_received()
    alice_second = _connect(app, alice_http)
    assert _events(watcher, "presence") == []

    alice_first.disconnect()
    assert registry.is_online(alice_id)
    assert _events(watcher, "presence") == []

    alice_second.disconnect()
    offline = _events(watcher, "presence")
    assert len(offline) == 1
    assert offline[0]["args"][0]["user"]["id"] == alice_id
    assert offline[0]["args"][0]["online"] is False
    assert not registry.is_online(alice_id)


def test_sync_returns_missed_messages_in_id_order_and_unread_counts(app):
    alice_http, _alice_id = _account(app, "alice")
    bob_http, _bob_id = _account(app, "bob")
    alice = _connect(app, alice_http)
    bob = _connect(app, bob_http)
    with app.app_context():
        general_id = Room.query.filter_by(kind="public", name="general").one().id

    first = alice.emit(
        "message:send", {"room_id": general_id, "body": "first", "client_id": "sync-1"}, callback=True
    )
    second = alice.emit(
        "message:send", {"room_id": general_id, "body": "second", "client_id": "sync-2"}, callback=True
    )
    ack = bob.emit("sync", {"cursors": {str(general_id): first["data"]["message"]["id"]}}, callback=True)

    assert ack["ok"] is True
    assert [item["id"] for item in ack["data"]["messages"]] == [second["data"]["message"]["id"]]
    assert ack["data"]["unread"][str(general_id)] == 2



