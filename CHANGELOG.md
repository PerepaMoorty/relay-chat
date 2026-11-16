# Changelog

All notable changes to Relay are recorded here. Format: Keep a Changelog. Versions: v0.1.0 = Sprint 1, v1.0.0 = Sprint 2.

## [0.1.0] - 2026-11-16

### Added
- Connection and sessions: connect to the server, username prompt, unique usernames, username-to-socket mapping, online user list, join and leave notices, reconnect after disconnects, graceful termination.
- Accounts: register and log in, with the login creating the socket session.
- Messaging: send text messages, broadcast to everyone, private messages, live display with timestamps, edit and delete your own messages, rejection of invalid input, error handling.
- Rooms and direct messages: create a room, browse, join and leave rooms.
- History: message history with pagination, offline delivery, unread counts.
- Receipts: delivered and read receipts.
- Reconnect and sync: automatic reconnect with message sync.
- Test suite (66 tests) and CI with ruff and pytest.

### Known issues
- The Sprint 1 demo video is not recorded yet (the file in the repo is a placeholder).
- `develop` already contained the Sprint 2 code when this release was cut, because the two sprints overlapped in practice.
