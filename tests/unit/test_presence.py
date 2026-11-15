from relay.services.presence import PresenceRegistry


def test_add_tracks_first_and_additional_sockets_for_a_user():
    registry = PresenceRegistry()

    assert registry.add("sid-one", 7) is True
    assert registry.add("sid-two", 7) is False
    assert registry.user_for("sid-one") == 7
    assert set(registry.sids_for(7)) == {"sid-one", "sid-two"}
    assert registry.is_online(7) is True
    assert registry.online_user_ids() == [7]
    assert {entry["sid"] for entry in registry.snapshot()} == {"sid-one", "sid-two"}
    assert all(entry["user_id"] == 7 and entry["connected_at"] for entry in registry.snapshot())


def test_remove_only_marks_user_offline_after_last_socket():
    registry = PresenceRegistry()
    registry.add("sid-one", 7)
    registry.add("sid-two", 7)

    assert registry.remove("sid-one") == (7, False)
    assert registry.user_for("sid-one") is None
    assert registry.sids_for(7) == ["sid-two"]
    assert registry.is_online(7) is True
    assert registry.remove("sid-two") == (7, True)
    assert registry.is_online(7) is False
    assert registry.online_user_ids() == []
    assert registry.snapshot() == []


def test_unknown_sid_removal_is_idempotent():
    registry = PresenceRegistry()
    registry.add("sid-one", 7)

    assert registry.remove("missing") == (None, False)
    assert registry.is_online(7) is True
    assert registry.sids_for(7) == ["sid-one"]


def test_clear_removes_all_registry_state():
    registry = PresenceRegistry()
    registry.add("sid-one", 7)
    registry.add("sid-two", 8)

    registry.clear()

    assert registry.user_for("sid-one") is None
    assert registry.sids_for(7) == []
    assert registry.is_online(8) is False
    assert registry.online_user_ids() == []
    assert registry.snapshot() == []
