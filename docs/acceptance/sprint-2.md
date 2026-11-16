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

| Card | Description | Acceptance Criteria | Evidence | Verdict | Notes |
|---|---|---|---|:---:|---|
| **F-012** | Concurrent clients | Handles >= 20 concurrent active socket connections | TC-12, TC-N05, T6 tests | **A** | Scalability verified |
| **F-026** | Typing indicators | Displays live typing state with 3s auto-expire | TC-26, T7 test suite, live test | **A** | Debounce & expire working |
| **F-037** | Share files | Upload attachments up to 10 MB with MIME check | TC-37, T7 test suite | **A** | Magic bytes validated |
| **F-038** | Image preview | Inline image rendering for PNG, JPEG, GIF, WebP | TC-38, live check | **A** | Responsive previews |
| **F-039** | Members-only download | Files downloadable only by room members | TC-39, T7 test suite | **A** | Non-members get 404 |
| **F-041** | Search messages | Case-insensitive text search scoped to joined rooms | TC-41, T7 test suite | **A** | Room scoping verified |
| **F-046** | Report message | Members can flag messages with reason | TC-46, T8 test suite | **A** | Stored in moderation queue |
| **F-047** | Review reports | Admin can review, dismiss, or delete messages | TC-47, T8 test suite | **A** | Live deletion confirmed |
| **F-048** | Ban/unban users | Admin ban revokes session and disconnects socket | TC-48, T8 test suite | **A** | Instant socket termination |
| **F-049** | Mute/unmute users | Admin mute restricts sending while allowing read | TC-49, T8 test suite | **A** | Sender block verified |
| **F-051** | Audit log | Append-only record of all administrative actions | TC-51, T8 test suite | **A** | Immutable trail confirmed |
| **F-052** | Monitor clients & activity | Admin dashboard shows active sockets & server events | TC-52, T8 test suite | **A** | Real-time diagnostics |

---

## 2. Non-Functional & Security Requirements Verification

| ID | Title | Criteria & Target | Evidence | Verdict | Notes |
|---|---|---|---|:---:|---|
| **NF-001** | Latency | Message delivery under 20 clients; measured per T9 script | TC-N01, T9 load test script report (delivery p95 measured; no numeric target in test plan) | **A** | Measurement reported in T9 log |
| **NF-002** | Cross-browser | Works on Chrome, Edge, Firefox, Safari | TC-N02, manual test template in T9 | **P** | Manual scenarios pending execution |
| **NF-003** | Network resilience | Automatic reconnect with exponential backoff | TC-N03, socket.js + sync verification | **A** | Reconnect & cursor sync verified |
| **NF-004** | Minimal footprint | Zero external runtime broker dependencies | TC-N04, pure Python + SQLite inspection | **A** | No external Redis/brokers |
| **NF-005** | Scalability | Supports >= 20 concurrent sockets on modest hardware | TC-N05, T6 multi-client & T9 load test | **A** | 20 active sockets sustained |
| **NF-006** | Message ordering | Monotonic message order preserved via autoincrement ID | TC-N06, T6 tests & T9 run log | **A** | Verified in T6 & T9 repeat |
| **NF-007** | Zero-config deployment | Launches directly with SQLite defaults | TC-N07, run.py automated setup | **A** | Zero manual DB migration needed |
| **NF-008** | Storage integrity | Enforces 10 MB cap; isolates files outside web root | TC-N08, files.py & T7 test suite | **A** | MIME & size cap enforced |
| **NF-009** | Test coverage | Automated test coverage >= 70% on `relay/services` | TC-N09, pytest test suite; S5 coverage gate PR pending | **P** | Pending S5 merge |
| **NF-010** | Ease of evaluation | One-click startup via `run-demo.bat` and `run-demo.sh` | TC-N10, P3 deliverables merged | **A** | Verified on Windows & Unix |
| **NF-011** | Audit immutability | Append-only audit log with no edit/delete paths | TC-N11, audit.py & T8 test suite | **A** | Immutable schema verified |
| **SR-001** | Dead socket rejection | Stale/unauthenticated socket requests rejected | TC-S01, T6 test suite | **A** | Auth check in ack decorator |
| **SR-002** | Username namespace | Case-insensitive uniqueness prevents spoofing | TC-S02, T3 auth suite | **A** | Unique constraint enforced |
| **SR-003** | Channel isolation | DMs accessible exclusively to the 2 participants | TC-S03, T6 multi-client suite | **A** | Channel membership isolated |
| **SR-004** | Input sanitization | Payload length and control character validation | TC-S04, T4 unit tests | **A** | 4,000 char cap + trim |
| **SR-005** | Token revocation | Revoked session immediately disconnects socket | TC-S05, T6 & T8 test suites | **A** | Disconnect on revocation |
| **SR-006** | Credential security | Passwords stored with salted scrypt hashing | TC-S06, T3 auth suite | **A** | Werkzeug scrypt hashing |
| **SR-007** | Handshake auth | Handshake verifies active session cookie | TC-S07, T6 multi-client suite | **A** | Rejected if unauthenticated |
| **SR-008** | Server authorization | Service layer enforces permissions for all actions | TC-S08, T5/T8 test suites | **A** | Non-members get NOT_FOUND |
| **SR-009** | XSS prevention | `textContent` rendering + Content Security Policy | TC-S09, dom.js + headers check | **A** | No innerHTML, strict CSP |
| **SR-010** | Upload safety | Extension allow-list + magic-byte verification | TC-S10, T7 test suite | **A** | Extension & magic-byte check |
| **SR-011** | SQL injection immunity | Parameterized queries via SQLAlchemy ORM | TC-S11, T4/T7 test suites | **A** | Bound parameters only |
| **SR-012** | Admin accountability | Tamper-resistant audit log records all actions | TC-S12, T8 test suite | **A** | Logged on every admin action |
| **SR-013** | Instant revocation | Session version bump forces immediate logout | TC-S13, T3/T8 test suites | **A** | Bump on ban/logout |
| **SR-014** | CSWSH defense | Same-origin socket policy + CORS whitelist | TC-S14, config.py + handshake check | **A** | Origin check + SameSite Lax |

---

## 3. Sprint 2 Review Summary
- All 11 Sprint 2 Functional Requirements (**F-012, F-026, F-037–F-039, F-041, F-046–F-049, F-051, F-052**) are formally **ACCEPTED (A)**.
- 12 of 14 Security Requirements and 9 of 11 NFRs have complete automated evidence and are **ACCEPTED (A)**.
- **NF-002** (manual browser matrix) and **NF-009** (S5 CI coverage gate) remain **In Progress (P)** pending respective manual execution and S5 CI merge.
- Backlog Could-tier requirements remain documented for post-v1.0.
