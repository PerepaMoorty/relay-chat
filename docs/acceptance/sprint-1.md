# Sprint 1 Acceptance Record

| | |
|---|---|
| **Project** | Relay — Real-Time Chat Application |
| **Review Date** | 2026-11-14 |
| **Product Owner** | Naivadh Shrivastava (PES2UG24CS297) |
| **Scrum Master** | Medha Singh (PES2UG24CS274) |
| **Developers** | Lakshmi Narasimha Moorty Perepa (PES2UG24CS248), Malepati Viswajith (PES2UG24CS259) |
| **Sprint Goal** | *"The v1.0 chat works end to end"* (Core messaging, rooms, presence, direct messaging, receipts) |

---

## 1. Acceptance Criteria & Verdict Summary

| Card | Description | Acceptance Criteria | Evidence | Verdict | Notes |
|---|---|---|---|:---:|---|
| **SETUP-skeleton** | Repo Skeleton + SAD | App boots, factory registers blueprints, SAD v1.0 matches architecture | B1 merge, SAD v1.0 | **A** | Foundational skeleton |
| **SETUP-CI** | CI & Templates | GitHub Actions pipeline runs lint + tests, issue/PR templates available | S1 merge, CI green | **A** | CI operational |
| **SETUP-harness** | Test Harness | Pytest suite configured with client fixture and test plan | T1 merge, test-plan.md | **A** | Quality harness established |
| **SETUP-docs** | Project Documents | SRS v2.0 with 77-item RTM, MoSCoW features, use-case and architecture diagrams | P1, S2 merges | **A** | Baseline docs approved |
| **F-001** | Connect via IP/port | WebSocket connection establishes over configured IP/port | TC-01, live test | **A** | Sockets upgrade cleanly |
| **F-002** | Username prompt | Unauthenticated visitors prompted to log in/register before chat view | TC-02, live test | **A** | Gated entry view works |
| **F-003** | Unique usernames | Duplicate usernames rejected with 409 USERNAME_TAKEN | TC-03, T3 test suite | **A** | Case-insensitive constraint |
| **F-004** | Send text message | Text sent via composer delivers to active room with client_id ack | TC-04, T6 test suite | **A** | Instant delivery |
| **F-005** | Public broadcast | Messages sent in #general broadcast to all connected members | TC-05, T6 multi-client | **A** | Multicast confirmed |
| **F-006** | Private messages (DMs) | Direct messages isolated strictly to two participants | TC-06, T5 integration | **A** | Privacy preserved |
| **F-007** | Live display | Incoming messages appear in DOM without page refresh | TC-07, live test | **A** | Real-time DOM updates |
| **F-008** | Timestamps | Messages display server UTC timestamp in local browser format | TC-08, dom.js check | **A** | Correct localization |
| **F-009** | Online users list | Sidebar displays live list of active users, updated on presence | TC-09, T6 multi-client | **A** | Presence sync verified |
| **F-010** | Join notice | Ephemeral join notification rendered when user comes online | TC-10, live check | **A** | Visible in #general |
| **F-011** | Leave notice | Ephemeral notice rendered after 3-second grace period on disconnect | TC-11, live check | **A** | Grace period prevents flash |
| **F-013** | Survive disconnects | Server remains stable on abrupt socket drop; registry cleans up | TC-13, T6 multi-client | **A** | No uncaught crashes |
| **F-014** | Graceful termination | Explicit logout disconnects socket, updates presence to offline | TC-14, T3 auth suite | **A** | Complete session cleanup |
| **F-015** | Username ↔ socket | In-memory thread-safe mapping maintains active sids per user | TC-15, T2 unit tests | **A** | Registry verified |
| **F-016** | Reject invalid | Rejects empty, >4000 char, or control-char messages | TC-16, T4 unit tests | **A** | Validation enforced |
| **F-017** | Error handling | Standard error envelope {ok: false, error: {code, message}} | TC-17, T6 test suite | **A** | Uniform error schema |
| **F-018** | User registration | New account creation with salted scrypt hashing | TC-18, T3 auth suite | **A** | Secure onboarding |
| **F-019** | Login + socket session | Session cookie binds to WebSocket handshake | TC-19, T3/T6 tests | **A** | Handshake authenticated |
| **F-020** | History pagination | Paginates room history (50 messages/page) on scroll | TC-20, T5 integration | **A** | Cursor pagination verified |
| **F-021** | Offline delivery | Missed messages delivered upon next connection via sync | TC-21, T5/T6 tests | **A** | Sync recovery works |
| **F-022** | Create room | Users can create public or invite-only group rooms | TC-22, T5 integration | **A** | Custom channels operational |
| **F-023** | Browse/join/leave | Users can browse public channels, join, and exit | TC-23, T5 integration | **A** | Membership flows working |
| **F-027** | Read receipts | Monotonic delivered_up_to and read_up_to watermarks | TC-27, T6 multi-client | **A** | Checkmarks update live |
| **F-028** | Reconnect + sync | Auto-reconnection with last-seen cursor catch-up | TC-28, T6 multi-client | **A** | Zero message duplication |
| **F-029** | Edit message | Author can edit sent message in-place with real-time update | TC-29, T6 multi-client | **A** | Ownership check enforced |
| **F-030** | Delete message | Author can soft-delete message, preserving chronology | TC-30, T6 multi-client | **A** | Body cleared cleanly |
| **F-040** | Unread counts | Sidebar shows unread badges incrementing on incoming messages | TC-40, T5 integration | **A** | Watermarks clear badges |

---

## 2. Verdict Decision
**All 28 Functional Requirements and 4 SETUP deliverables assigned to Sprint 1 are formally ACCEPTED (A).**
No cards were rejected or carried over.
