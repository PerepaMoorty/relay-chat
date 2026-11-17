# Changelog

All notable changes to Relay are recorded here. Format: Keep a Changelog. Versions: v0.1.0 = Sprint 1, v1.0.0 = Sprint 2.

## [1.0.0] - 2026-11-17

### Added
- Typing indicators: see when someone in the room is typing.
- File sharing: upload files and images up to 10 MB with type checking, inline image preview, and members-only download.
- Search: search messages in the rooms you belong to.
- Moderation: report a message, review reports, remove messages, ban and unban users, mute users, and an audit log of every admin action.
- Admin console: reports, users, audit log, connected clients and server activity.
- Concurrent clients: verified with a 20-client load test (scripts/load_test.py).
- Non-functional and security verification: load-test evidence, manual test record, test suites for typing, search, files, moderation, admin, audit and session revocation.
- CI coverage gate: at least 70 percent coverage on `relay/services`, enforced on every PR.
- Documentation: SRS v2.0 with requirements traceability matrix and deviations, features list, diagrams, README, one-click demo scripts, sprint plan, scrum notes and project retrospective.

### Changed
- SQLite now starts in WAL mode for safer concurrent use.
- Team process: Jira dropped, GitHub Issues and the Project are the only board (control file v1.1).

### Known issues
- Some manual tests are recorded as "Not run": the browser and device compatibility matrix, the novice-user usability check, the restart-within-10-seconds check and the cross-operating-system check (CHAT-NF-003, NF-007, NF-008). The Product Owner accepts those requirements only once the evidence exists.
- Development is frozen at this release. From here on only bug fixes are allowed, each on a `fix/` branch.

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
