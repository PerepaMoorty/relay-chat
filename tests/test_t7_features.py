import io

from relay.extensions import socketio


def register_user(app, username):
    client = app.test_client()
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "RelayPass123"},
    )
    assert response.status_code == 201, response.get_json()
    return client


def connect_socket(app, client):
    socket = socketio.test_client(app, flask_test_client=client)
    assert socket.is_connected()
    return socket


def general_room_id(client):
    response = client.get("/api/rooms")
    assert response.status_code == 200
    rooms = response.get_json()["data"]["rooms"]
    return next(room["id"] for room in rooms if room["kind"] == "public")


def test_typing_is_broadcast_to_other_room_members_only(app):
    sender = register_user(app, "typing_sender")
    receiver = register_user(app, "typing_receiver")
    room_id = general_room_id(sender)

    sender_socket = connect_socket(app, sender)
    receiver_socket = connect_socket(app, receiver)

    try:
        sender_socket.get_received()
        receiver_socket.get_received()

        ack = sender_socket.emit(
            "typing:start", {"room_id": room_id}, callback=True
        )
        assert ack["ok"] is True

        received = [
            event for event in receiver_socket.get_received()
            if event["name"] == "typing"
        ]
        assert len(received) == 1
        payload = received[0]["args"][0]
        assert payload["room_id"] == room_id
        assert payload["user"]["username"] == "typing_sender"
        assert payload["is_typing"] is True

        sender_events = sender_socket.get_received()
        assert not any(event["name"] == "typing" for event in sender_events)

        stop_ack = sender_socket.emit(
            "typing:stop", {"room_id": room_id}, callback=True
        )
        assert stop_ack["ok"] is True

        stopped = [
            event for event in receiver_socket.get_received()
            if event["name"] == "typing"
        ]
        assert len(stopped) == 1
        assert stopped[0]["args"][0]["is_typing"] is False
    finally:
        sender_socket.disconnect()
        receiver_socket.disconnect()


def test_search_only_returns_messages_from_member_rooms(app):
    owner = register_user(app, "search_owner")
    outsider = register_user(app, "search_outsider")

    room_response = owner.post(
        "/api/rooms",
        json={"name": "t7-private-search", "visibility": "private"},
    )
    assert room_response.status_code == 201
    room_id = room_response.get_json()["data"]["room"]["id"]

    owner_socket = connect_socket(app, owner)
    try:
        ack = owner_socket.emit(
            "message:send",
            {
                "room_id": room_id,
                "body": "T7DistinctiveSearchPhrase",
                "client_id": "t7-search-message-1",
            },
            callback=True,
        )
        assert ack["ok"] is True

        owner_result = owner.get(
            "/api/search?q=T7DistinctiveSearchPhrase"
        )
        assert owner_result.status_code == 200
        messages = owner_result.get_json()["data"]["messages"]
        assert len(messages) == 1
        assert messages[0]["body"] == "T7DistinctiveSearchPhrase"

        outsider_result = outsider.get(
            "/api/search?q=T7DistinctiveSearchPhrase"
        )
        assert outsider_result.status_code == 200
        assert outsider_result.get_json()["data"]["messages"] == []
    finally:
        owner_socket.disconnect()


def test_file_upload_member_download_and_nonmember_denial(app):
    owner = register_user(app, "file_owner")
    member = register_user(app, "file_member")
    outsider = register_user(app, "file_outsider")

    room_response = owner.post(
        "/api/rooms",
        json={"name": "t7-file-room", "visibility": "public"},
    )
    assert room_response.status_code == 201
    room_id = room_response.get_json()["data"]["room"]["id"]

    join_response = member.post(f"/api/rooms/{room_id}/join")
    assert join_response.status_code == 200

    content = b"T7 file access test"
    upload = owner.post(
        "/api/files",
        data={"file": (io.BytesIO(content), "t7-note.txt")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201
    attachment = upload.get_json()["data"]["attachment"]

    owner_socket = connect_socket(app, owner)
    try:
        ack = owner_socket.emit(
            "message:send",
            {
                "room_id": room_id,
                "body": "",
                "client_id": "t7-file-message-1",
                "attachment_id": attachment["id"],
            },
            callback=True,
        )
        assert ack["ok"] is True

        member_download = member.get(attachment["url"])
        assert member_download.status_code == 200
        assert member_download.data == content
        assert member_download.headers["X-Content-Type-Options"] == "nosniff"

        outsider_download = outsider.get(attachment["url"])
        assert outsider_download.status_code == 403
    finally:
        owner_socket.disconnect()
