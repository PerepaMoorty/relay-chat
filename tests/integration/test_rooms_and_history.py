from relay.extensions import db
from relay.models import Room, RoomMember, User
from relay.services import messages


def _register(client, username):
    response = client.post("/api/auth/register", json={"username": username, "password": "long-password"})
    assert response.status_code == 201
    return response.json["data"]["user"]


def _create_group(client, name="project", visibility="public"):
    response = client.post("/api/rooms", json={"name": name, "visibility": visibility})
    assert response.status_code == 201
    return response.json["data"]["room"]


def test_authenticated_room_lists_hide_private_rooms_and_report_join_state(app):
    alice_client = app.test_client()
    _register(alice_client, "alice")
    public = _create_group(alice_client, "public-room")
    private = _create_group(alice_client, "private-room", "private")

    rooms_response = alice_client.get("/api/rooms")
    public_response = alice_client.get("/api/rooms/public")

    assert [room["id"] for room in rooms_response.json["data"]["rooms"]] == [
        rooms_response.json["data"]["rooms"][0]["id"], public["id"], private["id"]
    ]
    listed_public = public_response.json["data"]["rooms"]
    assert {room["name"] for room in listed_public} == {"general", "public-room"}
    assert next(room for room in listed_public if room["id"] == public["id"])["joined"] is True
    assert all(room["id"] != private["id"] for room in listed_public)


def test_join_public_room_is_idempotent_and_leave_updates_membership(app):
    alice_client = app.test_client()
    bob_client = app.test_client()
    _register(alice_client, "alice")
    _register(bob_client, "bob")
    group = _create_group(alice_client)

    first = bob_client.post(f"/api/rooms/{group['id']}/join")
    repeated = bob_client.post(f"/api/rooms/{group['id']}/join")
    joined_rooms = bob_client.get("/api/rooms").json["data"]["rooms"]
    leave = bob_client.post(f"/api/rooms/{group['id']}/leave")
    after_leave = bob_client.get("/api/rooms").json["data"]["rooms"]

    assert first.status_code == repeated.status_code == 200
    assert any(room["id"] == group["id"] for room in joined_rooms)
    assert leave.status_code == 200
    assert all(room["id"] != group["id"] for room in after_leave)


def test_private_room_join_requires_valid_invite_and_owner_sees_code(app):
    alice_client = app.test_client()
    bob_client = app.test_client()
    _register(alice_client, "alice")
    _register(bob_client, "bob")
    private = _create_group(alice_client, "private-room", "private")

    assert private["invite_code"]
    invalid = bob_client.post("/api/rooms/join", json={"invite_code": "invalid"})
    valid = bob_client.post("/api/rooms/join", json={"invite_code": private["invite_code"]})

    assert invalid.status_code == 400
    assert invalid.json["error"]["code"] == "INVALID_INVITE"
    assert valid.status_code == 200
    assert valid.json["data"]["room"]["id"] == private["id"]
    assert "invite_code" not in valid.json["data"]["room"]


def test_direct_message_is_idempotent_and_returns_peer_specific_room(app):
    alice_client = app.test_client()
    bob_client = app.test_client()
    _register(alice_client, "alice")
    bob = _register(bob_client, "bob")

    created = alice_client.post("/api/dms", json={"user_id": bob["id"]})
    existing = alice_client.post("/api/dms", json={"user_id": bob["id"]})

    assert created.status_code == 201
    assert existing.status_code == 200
    assert created.json["data"]["room"]["id"] == existing.json["data"]["room"]["id"]
    assert created.json["data"]["room"]["peer"]["username"] == "bob"
    assert any(room["kind"] == "direct" for room in alice_client.get("/api/rooms").json["data"]["rooms"])


def test_direct_message_rejects_unknown_user_and_self(app):
    alice_client = app.test_client()
    alice = _register(alice_client, "alice")

    self_dm = alice_client.post("/api/dms", json={"user_id": alice["id"]})
    unknown_dm = alice_client.post("/api/dms", json={"user_id": 999})

    assert self_dm.status_code == 400
    assert self_dm.json["error"]["code"] == "VALIDATION_ERROR"
    assert unknown_dm.status_code == 404
    assert unknown_dm.json["error"]["code"] == "NOT_FOUND"


def test_history_and_receipts_are_limited_to_room_members(app):
    alice_client = app.test_client()
    bob_client = app.test_client()
    carol_client = app.test_client()
    _register(alice_client, "alice")
    _register(bob_client, "bob")
    _register(carol_client, "carol")
    group = _create_group(alice_client)
    with app.app_context():
        alice = User.query.filter_by(username="alice").one()
        bob = User.query.filter_by(username="bob").one()
        messages.send(alice.id, group["id"], "first", client_id="history-1")
        messages.send(alice.id, group["id"], "second", client_id="history-2")
        # The history route includes room receipts for members, not a global receipt list.
        db.session.add(RoomMember(room_id=group["id"], user_id=bob.id))
        db.session.commit()

    member_history = alice_client.get(f"/api/rooms/{group['id']}/messages?limit=1")
    nonmember_history = carol_client.get(f"/api/rooms/{group['id']}/messages")

    assert member_history.status_code == 200
    assert [item["body"] for item in member_history.json["data"]["messages"]] == ["second"]
    assert len(member_history.json["data"]["receipts"]) == 2
    assert nonmember_history.status_code == 404
    assert nonmember_history.json["error"]["code"] == "NOT_FOUND"


def test_room_list_unread_counts_ignore_own_messages_and_exclude_nonmembers(app):
    alice_client = app.test_client()
    bob_client = app.test_client()
    _register(alice_client, "alice")
    bob = _register(bob_client, "bob")
    _create_group(alice_client)
    with app.app_context():
        alice = User.query.filter_by(username="alice").one()
        general = Room.query.filter_by(kind="public", name="general").one()
        messages.send(alice.id, general.id, "own")
        messages.send(bob["id"], general.id, "from bob")

    alice_rooms = alice_client.get("/api/rooms").json["data"]["rooms"]
    general = next(room for room in alice_rooms if room["name"] == "general")

    assert general["unread"] == 1
    assert all(room["name"] != "project" for room in bob_client.get("/api/rooms").json["data"]["rooms"])


def test_room_endpoints_require_authentication(client):
    for path in ("/api/rooms", "/api/rooms/public", "/api/dms", "/api/rooms/1/messages"):
        response = client.get(path) if path != "/api/dms" else client.post(path, json={"user_id": 1})
        assert response.status_code == 401
        assert response.json["error"]["code"] == "AUTH_REQUIRED"




