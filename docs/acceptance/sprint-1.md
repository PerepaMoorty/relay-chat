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

| ID | Title | Acceptance / Measurement Criteria | Evidence | Test Case | Verdict | Notes |
|---|---|---|---|---|:---:|---|
| **SETUP-skeleton** | Repo Skeleton + SAD | App boots, factory registers blueprints, SAD v1.0 matches architecture | B1 merge, SAD v1.0 | `TC-SETUP-01` | **A** | Foundational skeleton |
| **SETUP-CI** | CI & Templates | GitHub Actions pipeline runs lint + tests, issue/PR templates available | S1 merge, CI green | `TC-SETUP-02` | **A** | CI operational |
| **SETUP-harness** | Test Harness | Pytest suite configured with client fixture and test plan | T1 merge, test-plan.md | `TC-SETUP-03` | **A** | Quality harness established |
| **SETUP-docs** | Project Documents | SRS v2.0 with 77-item RTM, MoSCoW features, use-case and architecture diagrams | P1, S2 merges | `TC-SETUP-04` | **A** | Baseline docs approved |
| **CHAT-F-001** | Connect to the chat server | Valid server address establishes a connection. | B7, F2, T6 merges | `TC-CON-01` | **A** | Sockets upgrade cleanly |
| **CHAT-F-002** | Prompt for username on connect | Username prompt appears before chat access. | F4, T3 merges | `TC-AUTH-01` | **A** | Gated entry view works |
| **CHAT-F-003** | Unique usernames | Duplicate username is rejected. | B4, T3 merges | `TC-AUTH-02` | **A** | Case-insensitive constraint |
| **CHAT-F-004** | Send a text message | Valid message is transmitted to server. | B5, B8, F7, T6 merges | `TC-MSG-01` | **A** | Instant delivery |
| **CHAT-F-005** | Broadcast public messages | Public message appears for all eligible users. | B8, T6 merges | `TC-MSG-02` | **A** | Multicast confirmed |
| **CHAT-F-006** | Private (1:1) messages | Private message is delivered only to sender and recipient. | B5, B6, F5, T5, T6 merges | `TC-PRV-01` | **A** | Privacy preserved |
| **CHAT-F-007** | Live display without refresh | Received message automatically appears. | F6, F9, T6 merges | `TC-MSG-03` | **A** | Real-time DOM updates |
| **CHAT-F-008** | Message timestamps | Displayed message contains timestamp. | F3, F6, T5 merges | `TC-MSG-04` | **A** | Correct localization |
| **CHAT-F-009** | Online users list | List matches active connections. | B7, F5, T6 merges | `TC-USER-01` | **A** | Presence sync verified |
| **CHAT-F-010** | Join notifications | Join notification is displayed. | B7, F6, T6 merges | `TC-USER-02` | **A** | Visible in #general |
| **CHAT-F-011** | Leave notifications | Leave notification is displayed. | B7, F6, T6 merges | `TC-USER-03` | **A** | Grace period prevents flash |
| **CHAT-F-013** | Survive unexpected disconnects | Disconnected client is removed and server continues. | B3, B7, T6 merges | `TC-SRV-02` | **A** | No uncaught crashes |
| **CHAT-F-014** | Graceful session termination | Socket closes and active-user list updates. | B4, B7, F9, T3 merges | `TC-CON-02` | **A** | Complete session cleanup |
| **CHAT-F-015** | Username-to-socket mapping | Username maps to correct socket. | B2, T2 merges | `TC-SRV-03` | **A** | Registry verified |
| **CHAT-F-016** | Reject empty or invalid messages | Invalid message is not transmitted as valid chat. | B5, F7, T4 merges | `TC-VAL-01` | **A** | Validation enforced |
| **CHAT-F-017** | Communication error handling | Communication failure is handled without server crash. | B3, F2, T6 merges | `TC-ERR-01` | **A** | Uniform error schema |
| **CHAT-F-018** | Register an account with a password | Valid username and password create an account and log the user in. Duplicate usernames are rejected with USERNAME_TAKEN; invalid usernames or short passwords with VALIDATION_ERROR. | B4, F4, T3 merges | `TC-ACC-01` | **A** | Secure onboarding |
| **CHAT-F-019** | Log in with a session bound to the socket | Correct credentials open the chat; wrong ones show a generic error. A socket without a valid session is refused; a forged sender field in a payload is ignored. | B4, B7, F4, T3, T6 merges | `TC-ACC-02` | **A** | Handshake authenticated |
| **CHAT-F-020** | Persistent history with pagination | Messages survive a server restart. With 120 messages, the latest 50 show; scrolling up loads the next 50 in order without duplicates. | B6, F6, T5 merges | `TC-HIST-01` | **A** | Cursor pagination verified |
| **CHAT-F-021** | Offline message delivery | B logs out; A sends 3 private messages; on login B sees all 3 and the conversation is marked unread. | B5, B6, T5 merges | `TC-HIST-02` | **A** | Sync recovery works |
| **CHAT-F-022** | Create a group room | A 1-40 character name creates the room with the creator as owner; empty or longer names are rejected. | B6, F8, T5 merges | `TC-ROOM-01` | **A** | Custom channels operational |
| **CHAT-F-023** | Browse, join and leave public rooms | Public rooms are listed with member counts; private rooms never appear. Joining adds the room and posts a join notice; leaving stops further messages from it. | B6, F8, T5 merges | `TC-ROOM-02` | **A** | Membership flows working |
| **CHAT-F-027** | Delivered and read receipts | A private message shows 'delivered' on receipt and 'read' once viewed; room read counts update live. | B5, B8, F6, T6 merges | `TC-PRES-02` | **A** | Checkmarks update live |
| **CHAT-F-028** | Auto-reconnect with missed-message sync | After 30 s offline while 5 messages are sent, reconnecting shows all 5 in order with no duplicates; a 'reconnecting…' banner shows meanwhile. | B8, F2, F9, T6 merges | `TC-PRES-03` | **A** | Zero message duplication |
| **CHAT-F-029** | Edit own message | Edits appear live everywhere with '(edited)'; editing another user's message fails with FORBIDDEN. | B5, B8, F6, T6 merges | `TC-RICH-01` | **A** | Ownership check enforced |
| **CHAT-F-030** | Delete own message | All clients show the placeholder and the history API no longer returns the text. | B5, B8, F6, T6 merges | `TC-RICH-02` | **A** | Body cleared cleanly |
| **CHAT-F-040** | Unread counts | 3 messages in a closed conversation show a badge of 3; opening clears it. | B5, B6, F3, F5, T5 merges | `TC-PRES-04` | **A** | Watermarks clear badges |

---

## 2. Verdict Decision
**All 28 Functional Requirements and 4 SETUP deliverables assigned to Sprint 1 are formally ACCEPTED (A).**
No cards were rejected or carried over.
