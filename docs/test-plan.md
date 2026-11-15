# Relay — Test Plan

## 1. Purpose

This document defines the testing approach for Relay, including unit, integration, system/acceptance, and non-functional testing.

The plan follows the API, Socket.IO, security, and testing contracts in [architecture.md](architecture.md).

## 2. Test environment

| Item | Configuration |
|---|---|
| Language | Python 3.11 or later |
| Test framework | pytest 8.3.3 |
| Coverage | pytest-cov 5.0.0 |
| Linter | Ruff 0.6.9 |
| Database for automated tests | SQLite in-memory database |
| Application configuration | `TestConfig` |
| HTTP integration testing | Flask test client |
| Socket integration testing | Flask-SocketIO `socketio.test_client` |
| Browser acceptance testing | Two or more real browser sessions |
| CI | GitHub Actions, Python 3.11 |

Automated tests must use the test configuration and must not depend on a developer's local database or production data.

## 3. Testing levels and ownership

| Level | Tooling | Scope | Owner |
|---|---|---|---|
| Unit | pytest, in-memory SQLite | Service rules, including membership, mute, limits, and permissions | Viswajith |
| Integration | Flask test client and `socketio.test_client` | REST endpoints, socket events, broadcast fan-out, and authentication on connect | Viswajith |
| System / acceptance | `TC-*` cases and two or more real browsers | Acceptance criteria; results recorded in the RTM | Viswajith (execution), Naivadh (acceptance) |
| Non-functional | `scripts/load_test.py` and Socket.IO clients | CHAT-NF-001 latency, CHAT-NF-005 20+ clients, and CHAT-NF-006 ordering | Viswajith (Sprint 2) |

## 4. Test cases

The status column distinguishes the initial automated tests from planned coverage. A planned case is not considered passed until it has been executed and its result recorded.

### 4.1 Application smoke tests

| ID | Scenario | Expected result | Status |
|---|---|---|---|
| TC-SMOKE-001 | Request `GET /` | HTTP 200 and HTML response | Automated |
| TC-SMOKE-002 | Request `GET /api/health` | Public endpoint returns `{"status": "ok"}` | Planned |

### 4.2 Security-header tests

The application must include the documented security headers on every HTTP response.

| ID | Scenario | Expected result | Status |
|---|---|---|---|
| TC-SEC-001 | Inspect Content-Security-Policy | `default-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'` | Automated |
| TC-SEC-002 | Inspect X-Content-Type-Options | Value is `nosniff` | Automated |
| TC-SEC-003 | Inspect Referrer-Policy | Value is `same-origin` | Automated |
| TC-SEC-004 | Access an authenticated route without a session | HTTP 401 JSON response with `AUTH_REQUIRED`, not a redirect | Planned |
| TC-SEC-005 | Submit a request exceeding the configured body-size limit | HTTP 413 with `PAYLOAD_TOO_LARGE` | Planned |

### 4.3 Authentication tests

| ID | Scenario | Expected result |
|---|---|---|
| TC-AUTH-001 | Request `/api/auth/me` without a session | HTTP 200 with `user: null` |
| TC-AUTH-002 | Request `/api/auth/me` with a valid session | HTTP 200 with the current user |
| TC-AUTH-003 | Register with valid credentials | HTTP 201, user is logged in and joins `#general` |
| TC-AUTH-004 | Register with an existing username or invalid input | Appropriate `USERNAME_TAKEN` or `VALIDATION_ERROR` response |
| TC-AUTH-005 | Log in with invalid credentials | `INVALID_CREDENTIALS` response |
| TC-AUTH-006 | Log in with a banned account | `BANNED` response |
| TC-AUTH-007 | Log out | Session version is bumped, `session:terminated` is emitted with reason `logout`, and sockets are disconnected |

### 4.4 Room and direct-message tests

| ID | Scenario | Expected result |
|---|---|---|
| TC-ROOM-001 | Request the user's room list | Only rooms where the user is a member are returned |
| TC-ROOM-002 | Request public rooms | Public rooms are returned; private rooms are excluded |
| TC-ROOM-003 | Create a group room | Creator becomes owner and first member; `room:added` is emitted |
| TC-ROOM-004 | Join a public group room | Membership is created; relevant room events are emitted |
| TC-ROOM-005 | Join the same public room again | Operation is idempotent |
| TC-ROOM-006 | Join a private room with an invite code | Valid code joins the room; invalid code returns `INVALID_INVITE` |
| TC-ROOM-007 | Leave a group room | User receives `room:removed` and the room receives `room:updated` |
| TC-ROOM-008 | Attempt to leave a direct-message room | `VALIDATION_ERROR` |
| TC-DM-001 | Create a direct message with another user | A direct room is created or the existing room is returned |
| TC-DM-002 | Create a direct message with an unknown user or oneself | `NOT_FOUND` or `VALIDATION_ERROR`, respectively |

### 4.5 Messaging and synchronization tests

| ID | Scenario | Expected result |
|---|---|---|
| TC-MSG-001 | Send a message to a room as a member | Message is acknowledged and `message:new` is broadcast to the room |
| TC-MSG-002 | Send a message as a non-member | Operation is rejected |
| TC-MSG-003 | Retry a send with the same `client_id` | Original message is returned; no duplicate is created |
| TC-MSG-004 | Edit one's own message | Message is updated and `message:updated` is emitted |
| TC-MSG-005 | Edit another user's message | `FORBIDDEN` |
| TC-MSG-006 | Delete one's own message | Message is soft-deleted and represented with `deleted: true` and an empty body |
| TC-MSG-007 | Delete another user's message | `FORBIDDEN` |
| TC-SYNC-001 | Synchronize using room message cursors | Messages newer than each cursor are returned in ascending order, subject to the documented limit |
| TC-SYNC-002 | Synchronize a room with a missing or zero cursor | That room's messages are skipped by sync |
| TC-HISTORY-001 | Request room history as a member and non-member | Members can retrieve history; non-members cannot |

### 4.6 Socket.IO and presence tests

| ID | Scenario | Expected result |
|---|---|---|
| TC-SOCK-001 | Connect without a valid session | Connection is refused |
| TC-SOCK-002 | Connect with a valid session | Client receives `presence:snapshot` |
| TC-SOCK-003 | Connect or disconnect another user | Presence events are broadcast appropriately |
| TC-SOCK-004 | Send an event from an unregistered or stale socket | Acknowledgement returns `AUTH_REQUIRED`; no action is performed |
| TC-SOCK-005 | Trigger an unexpected exception in an acknowledged event | Database session is rolled back, `INTERNAL` is acknowledged, and the server remains running |
| TC-SOCK-006 | Send `typing:start` or `typing:stop` | Room members receive the typing event, excluding the sender's socket |
| TC-SOCK-007 | Connect multiple clients to the same room | A message broadcast reaches the intended room clients |
| TC-SOCK-008 | Send a `sync` event | Acknowledgement contains rooms, messages, and unread counts as documented |

### 4.7 Receipts and file tests

| ID | Scenario | Expected result |
|---|---|---|
| TC-RECEIPT-001 | Update delivered and read watermarks | Watermarks move forward only; read also advances delivered |
| TC-RECEIPT-002 | Advance a watermark beyond the newest message | Watermark is capped at the newest message ID |
| TC-FILE-001 | Upload an allowed file with valid content | Attachment is created and returned |
| TC-FILE-002 | Upload an invalid file type or mismatched file content | Upload is rejected |
| TC-FILE-003 | Exceed the upload size limit | Request is rejected |
| TC-FILE-004 | Download as uploader or a member of the room | File is returned with the documented headers |
| TC-FILE-005 | Download as an unauthorized user | Access is denied |

### 4.8 Search and administration tests

| ID | Scenario | Expected result |
|---|---|---|
| TC-SEARCH-001 | Search messages using the documented query parameters | Matching messages are returned according to the search rules |
| TC-ADMIN-001 | Access an admin-only endpoint as a normal user | `FORBIDDEN` |
| TC-ADMIN-002 | Access an admin-only endpoint as an administrator | Authorized response is returned |
| TC-ADMIN-003 | Ban a user | User is banned, sessions are revoked, and `session:terminated` is emitted with reason `banned` |
| TC-ADMIN-004 | Attempt to ban an administrator | `FORBIDDEN` |
| TC-ADMIN-005 | Resolve a report by deleting its message | Message is soft-deleted, report is resolved, and one `message.delete` audit entry is written |
| TC-ADMIN-006 | Perform an effective administrative action | Exactly one corresponding audit entry is written |

## 5. Browser acceptance testing

The following scenarios require two or more real browser sessions with separate test accounts.

| ID | Acceptance scenario | Expected result |
|---|---|---|
| TC-E2E-001 | Register or log in from two browsers and open `#general` | Both users can access the chat |
| TC-E2E-002 | Send messages in both directions | Each browser receives the other user's messages live without refreshing |
| TC-E2E-003 | Observe online users and join/leave notices | Presence changes are reflected in the interface |
| TC-E2E-004 | Start a direct message and exchange messages | Private messages reach the intended participant |
| TC-E2E-005 | Create, join, and leave a room | Room list and membership state update correctly |
| TC-E2E-006 | Scroll back through room history | Older messages load correctly |
| TC-E2E-007 | Generate unread messages and open the room | Unread indicators and receipts update correctly |
| TC-E2E-008 | Edit and delete messages | Changes are reflected live |
| TC-E2E-009 | Restart the Python server during an active chat | Client reconnects and synchronizes without lost or duplicate messages |

## 6. Non-functional testing

Non-functional tests are scheduled for Sprint 2.

| ID | Requirement | Verification |
|---|---|---|
| TC-NF-001 | CHAT-NF-001 — latency | Measure message delivery latency using Socket.IO clients |
| TC-NF-005 | CHAT-NF-005 — 20+ clients | Exercise the system with at least 20 concurrent clients |
| TC-NF-006 | CHAT-NF-006 — message ordering | Verify message ordering under concurrent activity |
| TC-NF-009 | CHAT-NF-009 — service coverage | Track coverage of `relay/services` against the target of at least 70% |

## 7. Test execution and reporting

1. Run automated tests locally before submitting a pull request.
2. Run Ruff and pytest in the CI workflow.
3. Record system and browser acceptance results against their `TC-*` identifiers.
4. Record acceptance results in the Requirements Traceability Matrix (RTM).
5. Report failures with the test ID, steps to reproduce, expected result, actual result, and relevant logs or screenshots.
6. Do not mark a planned test as passed until it has been executed successfully.

### Local commands

Run from the repository root:

```bash
python -m pytest --cov=relay --cov-report=term-missing
ruff check .
```
