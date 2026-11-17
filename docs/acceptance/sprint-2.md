# Sprint 2 & Final Acceptance Record

| | |
|---|---|
| **Project** | Relay — Real-Time Chat Application |
| **Review Date** | 2026-11-16 |
| **Product Owner** | Naivadh Shrivastava (PES2UG24CS297) |
| **Scrum Master** | Medha Singh (PES2UG24CS274) |
| **Developers** | Lakshmi Narasimha Moorty Perepa (PES2UG24CS248), Malepati Viswajith (PES2UG24CS259) |
| **Sprint Goal** | *"Relay behaves like a real chat product"* (Typing, file sharing, search, moderation, NFR/SR verification) |

---

## 1. Sprint 2 Functional Acceptance

| ID | Title | Acceptance / Measurement Criteria | Evidence | Test Case | Verdict | Notes |
|---|---|---|---|---|:---:|---|
| **CHAT-F-012** | Concurrent clients | Multiple clients connect and communicate simultaneously. | T6, B7 merges | `TC-SRV-01` | **A** | Concurrency verified in T6 |
| **CHAT-F-026** | Typing indicators | Indicator appears within 1 s of typing and clears within 3 s of stopping or sending. | T7, B9, F6, F7 merges | `TC-PRES-01` | **A** | Debounce & auto-expire working |
| **CHAT-F-037** | Share files and images | Allowed files up to 10 MB arrive as messages with name and size; larger or disallowed files fail with PAYLOAD_TOO_LARGE / UNSUPPORTED_TYPE before storage. | T7, B11, F6, F7 merges | `TC-FILE-01` | **A** | MIME & payload limits checked |
| **CHAT-F-038** | Inline image preview | A PNG shows as a thumbnail at most 320 px wide; clicking opens it full size. | T7, B11, F6 merges | `TC-FILE-02` | **A** | Inline previews rendered |
| **CHAT-F-039** | Members-only file download | Members download; logged-in non-members get 403; anonymous requests get 401. | T7, B11 merges | `TC-FILE-03` | **A** | Non-members blocked |
| **CHAT-F-041** | Search messages | Results come only from the user's conversations and link to the message in context. | T7, B10, F8 merges | `TC-SRCH-01` | **A** | Scoped search verified |
| **CHAT-F-046** | Report a message | A report is created as 'open'; the same user cannot report the same message twice. | T8, B12, F10 merges | `TC-ADM-01` | **A** | Stored in moderation queue |
| **CHAT-F-047** | Review reports and remove messages | Deleting removes the message from all clients and resolves the report; non-admins get 403. | T8, B12, F10 merges | `TC-ADM-02` | **A** | Live deletion confirmed |
| **CHAT-F-048** | Ban and unban users | A banned online user's tabs disconnect within 2 s with a notice; logins are refused until unbanned. | T8, B12, F10 merges | `TC-ADM-03` | **A** | Instant socket termination |
| **CHAT-F-049** | Mute users | A muted user's send fails with MUTED and the remaining time; it works again after expiry. | T8, B12, F10 merges | `TC-ADM-04` | **A** | Mute restriction verified |
| **CHAT-F-051** | Audit log of admin actions | Each admin action creates exactly one entry, listed newest first; entries cannot be edited or deleted through the app. | T8, B12, F10 merges | `TC-ADM-06` | **A** | Immutable audit trail confirmed |
| **CHAT-F-052** | Monitor clients and server activity | The admin view lists connected users with connect time; the activity log records each connect, disconnect and handled error. | T8, B2, B12, F10 merges | `TC-ADM-07` | **A** | Telemetry & client monitor verified |

---

## 2. Non-Functional & Security Requirements Verification

| ID | Title | Requirement / Target | Evidence | Test Case | Verdict | Notes |
|---|---|---|---|---|:---:|---|
| **CHAT-NF-001** | Performance | 90% of test messages delivered within 2 seconds. | T9 load test run log (100% within 2 seconds; concurrent p95: 1,144.766 ms, sequential p95: 21.234 ms) | `TC-PERF-01` | **A** | Target exceeded in T9 load test |
| **CHAT-NF-002** | Reliability | Server continues operating during concurrent-client testing. | T6 multi-client tests merged | `TC-REL-01` | **A** | Operational stability verified in T6 |
| **CHAT-NF-003** | Usability | Test users complete basic chat operations. | T9 manual test record template | `TC-UX-01` | **P** | Awaiting novice participant manual execution |
| **CHAT-NF-004** | Robustness | Failure tests do not crash the application. | T6 error containment tests merged | `TC-ROB-01` | **A** | Error boundary verified in T6 |
| **CHAT-NF-005** | Scalability | 20 clients connect and communicate during load testing. | T9 load test reports (20 clients, 2,000/2,000 deliveries) | `TC-SCALE-01` | **A** | 20 simultaneous connections verified |
| **CHAT-NF-006** | Reliability | Test messages appear in expected processing order. | T6 test suite & T9 sequential load test log | `TC-ORD-01` | **A** | Order preserved via autoincrement ID |
| **CHAT-NF-007** | Reliability | Restart the server mid-conversation: all acknowledged messages persist; clients reconnect ≤ 10 s. | T9 manual test record | `TC-REL-02` | **P** | Manual restart check not yet executed |
| **CHAT-NF-008** | Compatibility | Acceptance suite passes on Chrome, Edge and Firefox at 360/1366/1920 px. | T9 manual test record | `TC-COMP-01` | **P** | Browser matrix execution pending |
| **CHAT-NF-009** | Maintainability | CI shows ruff clean and coverage ≥ 70% on relay/services. | CI workflow; S5 merged (#132) enforcing >= 70% gate on relay/services | `TC-MAINT-01` | **A** | CI coverage gate active and enforced |
| **CHAT-NF-010** | Portability | Fresh clone runs on two OSes in under 10 minutes. | P3 merged (`run-demo.bat`, `run-demo.sh`) | `TC-PORT-01` | **A** | One-click setup scripts verified |
| **CHAT-NF-011** | Data retention | No update/delete path exists for audit_log; retention verified by inspection. | B12 inspection note & schema analysis | `TC-DATA-01` | **A** | Append-only schema verified |
| **CHAT-SR-001** | Security: Reject invalid connections | Invalid connection attempts are rejected. | T6 test suite merged | `TC-SEC-01` | **A** | Handshake validation confirmed |
| **CHAT-SR-002** | Security: No duplicate usernames | Duplicate username attempt is rejected. | T3 test suite merged | `TC-SEC-02` | **A** | Case-insensitive constraint |
| **CHAT-SR-003** | Security: Private-message routing | Third-party client does not receive private message. | T6 multi-client suite merged | `TC-SEC-03` | **A** | DM isolation verified |
| **CHAT-SR-004** | Security: Validate message data | Malformed or invalid message input is rejected safely. | T4 unit tests merged | `TC-SEC-04` | **A** | 4,000 char cap & validation |
| **CHAT-SR-005** | Security: No use of dead sockets | Messages from terminated connection are not processed. | T6 test suite merged | `TC-SEC-05` | **A** | Stale sid check confirmed |
| **CHAT-SR-006** | Security: Salted password hashing | DB shows only hashes; logs captured during login tests contain no password. | T3 auth tests merged | `TC-SEC-06` | **A** | Salted scrypt hashing verified |
| **CHAT-SR-007** | Security: Session-authenticated sockets | Connect without a cookie or with a banned user's cookie is refused; cookie flags verified. | T6 multi-client suite merged | `TC-SEC-07` | **A** | Cookie auth & flags verified |
| **CHAT-SR-008** | Security: Server-side authorisation | Requests for rooms the user is not in return FORBIDDEN; spoofed sender fields are ignored. | T5, T8 test suites merged | `TC-SEC-08` | **A** | Service authorization verified |
| **CHAT-SR-009** | Security: XSS-safe rendering + CSP | `<script>` and `<img onerror>` payloads render literally without executing; CSP header present. | T1, F3 tests merged | `TC-SEC-09` | **A** | Text node rendering & CSP verified |
| **CHAT-SR-010** | Security: Upload validation | Renamed .exe/.html uploads are rejected; stored names are random; headers verified. | T7 test suite merged | `TC-SEC-10` | **A** | Magic-byte checks verified |
| **CHAT-SR-011** | Security: ORM-only SQL, length limits | Over-length input fails with VALIDATION_ERROR; SQL metacharacters in search have no effect. | T4, T7 test suites merged | `TC-SEC-11` | **A** | Parameterized queries verified |
| **CHAT-SR-012** | Security: Admin role + audit | Non-admin calls to /api/admin/* get 403; each admin action yields one audit row. | T8 test suite merged | `TC-SEC-12` | **A** | Role check & audit log verified |
| **CHAT-SR-013** | Security: Revocation on ban/logout | Ban a user with 2 tabs: both disconnect ≤ 2 s; the old cookie is rejected. | T3, T8 test suites merged | `TC-SEC-13` | **A** | Instant session revocation verified |
| **CHAT-SR-014** | Security: Origin-restricted WebSocket | A handshake with a foreign Origin header is refused. | T9 load test & test suite merged | `TC-SEC-14` | **A** | Cross-origin check verified |

---

## 3. Sprint 2 & Final Review Summary
- All 11 Sprint 2 Functional Requirements (**CHAT-F-012, F-026, F-037–F-039, F-041, F-046–F-049, F-051, F-052**) are formally **ACCEPTED (A)**.
- All 14 Security Requirements (**CHAT-SR-001 through SR-014**) are formally **ACCEPTED (A)** based on merged automated test suites T1–T8 and T9.
- 7 of 11 NFRs (**CHAT-NF-001, NF-002, NF-004, NF-005, NF-006, NF-010, NF-011**) are formally **ACCEPTED (A)** based on T6, T9, B12, and P3 evidence.
- 3 NFRs remain pending (**P**):
  - **CHAT-NF-003, CHAT-NF-007, CHAT-NF-008:** Waiting on manual execution of browser and novice-user scenarios (recorded as 'Not run' in T9 manual test log).
- **CHAT-NF-009:** Accepted (**A**) following merge of PR #132 (S5 coverage gate enforcing >= 70% line coverage on relay/services).
- Release v1.0.0 will proceed once final manual test confirmations land.
