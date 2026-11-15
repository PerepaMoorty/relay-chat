from relay.extensions import db, socketio
from relay.models import User

PASSWORD = "RelayPass123"


def register_user(app, username):
    client = app.test_client()
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201, response.get_json()
    user_id = response.get_json()["data"]["user"]["id"]
    return client, user_id


def register_admin(app, username="t8_admin"):
    client, user_id = register_user(app, username)
    with app.app_context():
        user = db.session.get(User, user_id)
        user.role = "admin"
        db.session.commit()
    return client, user_id


def connect_socket(app, client):
    socket = socketio.test_client(app, flask_test_client=client)
    assert socket.is_connected()
    return socket


def general_room_id(client):
    response = client.get("/api/rooms")
    assert response.status_code == 200
    rooms = response.get_json()["data"]["rooms"]
    return next(room["id"] for room in rooms if room["kind"] == "public")


def send_message(app, client, room_id, body, client_id):
    socket = connect_socket(app, client)
    try:
        ack = socket.emit(
            "message:send",
            {
                "room_id": room_id,
                "body": body,
                "client_id": client_id,
            },
            callback=True,
        )
        assert ack["ok"] is True, ack
        return ack["data"]["message"]
    finally:
        if socket.is_connected():
            socket.disconnect()


def error_code(response):
    return response.get_json()["error"]["code"]


def test_reporting_rejects_duplicates_and_nonmembers(app):
    poster, _ = register_user(app, "t8_report_poster")
    reporter, _ = register_user(app, "t8_report_user")
    outsider, _ = register_user(app, "t8_report_outsider")

    room_id = general_room_id(poster)
    message = send_message(
        app, poster, room_id, "Message to report", "t8-report-1"
    )

    report = reporter.post(
        f"/api/messages/{message['id']}/report",
        json={"reason": "Inappropriate message"},
    )
    assert report.status_code == 201

    duplicate = reporter.post(
        f"/api/messages/{message['id']}/report",
        json={"reason": "Reporting it again"},
    )
    assert duplicate.status_code == 400
    assert error_code(duplicate) == "VALIDATION_ERROR"

    private_room = poster.post(
        "/api/rooms",
        json={"name": "t8-private-report-room", "visibility": "private"},
    )
    assert private_room.status_code == 201
    private_room_id = private_room.get_json()["data"]["room"]["id"]

    private_message = send_message(
        app, poster, private_room_id, "Private message", "t8-report-2"
    )
    denied = outsider.post(
        f"/api/messages/{private_message['id']}/report",
        json={"reason": "Not a member"},
    )
    assert denied.status_code == 404
    assert error_code(denied) == "NOT_FOUND"


def test_admin_endpoints_reject_regular_users(app):
    user, user_id = register_user(app, "t8_regular_user")

    reports = user.get("/api/admin/reports")
    assert reports.status_code == 403
    assert error_code(reports) == "FORBIDDEN"

    users = user.get("/api/admin/users")
    assert users.status_code == 403
    assert error_code(users) == "FORBIDDEN"

    audit = user.get("/api/admin/audit")
    assert audit.status_code == 403
    assert error_code(audit) == "FORBIDDEN"

    sanction = user.post(
        f"/api/admin/users/{user_id}/ban",
        json={"reason": "Unauthorized attempt"},
    )
    assert sanction.status_code == 403
    assert error_code(sanction) == "FORBIDDEN"


def test_admin_delete_resolves_report_and_records_audit(app):
    poster, _ = register_user(app, "t8_delete_poster")
    reporter, _ = register_user(app, "t8_delete_reporter")
    admin, admin_id = register_admin(app)

    room_id = general_room_id(poster)
    message = send_message(
        app, poster, room_id, "Message awaiting moderation", "t8-delete-1"
    )

    report_response = reporter.post(
        f"/api/messages/{message['id']}/report",
        json={"reason": "Violates chat rules"},
    )
    assert report_response.status_code == 201
    report_id = report_response.get_json()["data"]["report"]["id"]

    open_reports = admin.get("/api/admin/reports?status=open")
    assert open_reports.status_code == 200
    assert any(
        item["id"] == report_id
        for item in open_reports.get_json()["data"]["reports"]
    )

    resolved = admin.post(
        f"/api/admin/reports/{report_id}/resolve",
        json={"action": "delete", "reason": "Confirmed violation"},
    )
    assert resolved.status_code == 200
    assert resolved.get_json()["data"]["report"]["status"] == "resolved"

    history = poster.get(f"/api/rooms/{room_id}/messages")
    messages = history.get_json()["data"]["messages"]
    deleted = next(item for item in messages if item["id"] == message["id"])
    assert deleted["deleted"] is True
    assert deleted["body"] == ""

    audit_response = admin.get("/api/admin/audit")
    assert audit_response.status_code == 200
    entries = audit_response.get_json()["data"]["entries"]
    matching = [
        item for item in entries
        if item["action"] == "message.delete"
        and item["target_id"] == message["id"]
    ]
    assert len(matching) == 1
    assert matching[0]["actor"] == "t8_admin"
    assert matching[0]["reason"] == "Confirmed violation"


def test_mute_blocks_messages_and_unmute_restores_sending(app):
    admin, _ = register_admin(app, "t8_mute_admin")
    user, user_id = register_user(app, "t8_muted_user")
    room_id = general_room_id(user)

    muted = admin.post(
        f"/api/admin/users/{user_id}/mute",
        json={"minutes": 15, "reason": "Temporary moderation"},
    )
    assert muted.status_code == 200
    assert muted.get_json()["data"]["user"]["muted_until"] is not None

    invalid_mute = admin.post(
        f"/api/admin/users/{user_id}/mute",
        json={"minutes": 14, "reason": "Too short"},
    )
    assert invalid_mute.status_code == 400
    assert error_code(invalid_mute) == "VALIDATION_ERROR"

    socket = connect_socket(app, user)
    try:
        blocked = socket.emit(
            "message:send",
            {
                "room_id": room_id,
                "body": "This should be blocked",
                "client_id": "t8-muted-message",
            },
            callback=True,
        )
        assert blocked["ok"] is False
        assert blocked["error"]["code"] == "MUTED"

        unmuted = admin.post(
            f"/api/admin/users/{user_id}/unmute",
            json={"reason": "Restriction lifted"},
        )
        assert unmuted.status_code == 200
        assert unmuted.get_json()["data"]["user"]["muted_until"] is None

        allowed = socket.emit(
            "message:send",
            {
                "room_id": room_id,
                "body": "Sending works again",
                "client_id": "t8-unmuted-message",
            },
            callback=True,
        )
        assert allowed["ok"] is True
    finally:
        if socket.is_connected():
            socket.disconnect()

    audit_response = admin.get("/api/admin/audit")
    actions = [
        item["action"]
        for item in audit_response.get_json()["data"]["entries"]
    ]
    assert "user.mute" in actions
    assert "user.unmute" in actions


def test_ban_revokes_sessions_and_disconnects_active_socket(app):
    admin, _ = register_admin(app, "t8_ban_admin")
    victim, victim_id = register_user(app, "t8_ban_victim")

    second_session = app.test_client()
    login = second_session.post(
        "/api/auth/login",
        json={"username": "t8_ban_victim", "password": PASSWORD},
    )
    assert login.status_code == 200

    socket = connect_socket(app, victim)
    try:
        banned = admin.post(
            f"/api/admin/users/{victim_id}/ban",
            json={"reason": "Repeated rule violations"},
        )
        assert banned.status_code == 200
        assert banned.get_json()["data"]["user"]["banned"] is True

        assert not socket.is_connected()

        assert victim.get("/api/rooms").status_code == 401
        assert second_session.get("/api/rooms").status_code == 401

        me = victim.get("/api/auth/me")
        assert me.status_code == 200
        assert me.get_json()["data"]["user"] is None

        blocked_login = app.test_client().post(
            "/api/auth/login",
            json={"username": "t8_ban_victim", "password": PASSWORD},
        )
        assert blocked_login.status_code == 403
        assert error_code(blocked_login) == "BANNED"

        audit_response = admin.get("/api/admin/audit")
        entries = audit_response.get_json()["data"]["entries"]
        ban_entries = [
            item for item in entries
            if item["action"] == "user.ban"
            and item["target_id"] == victim_id
        ]
        assert len(ban_entries) == 1
    finally:
        if socket.is_connected():
            socket.disconnect()
