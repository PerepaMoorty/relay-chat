# Sprint 2 Review

> These notes were prepared by the Scrum Master from the merge history of `develop`, the acceptance records in `docs/acceptance/` and the team chat. Merge dates are the real dates the PRs landed.

| | |
|---|---|
| **Review date** | 2026-11-16 (per `docs/acceptance/sprint-2.md`) |
| **Goal** | Relay behaves like a real chat product |
| **Product Owner verdict** | All 12 listed Sprint 2 functional requirements accepted (the acceptance record says 11). All 14 security requirements accepted. 7 of 11 NFRs accepted, 4 pending (below) |
| **Demo** | Typing indicators, file upload and inline preview, search, report and moderation flow, admin console, load test |

## Cards, PRs, merge dates and verdicts

| Card | Title | PRs (merge date) | Verdict | Note |
|---|---|---|---|---|
| CHAT-F-012 | Concurrent clients | T6 (#117, 16 Nov), B7 (#105, 13 Nov) | Accepted | Concurrency verified in T6 |
| CHAT-F-026 | Typing indicators | T7 (#111, 15 Nov), B9 (#105, 13 Nov), F6 (#106, 13 Nov), F7 (#106, 13 Nov) | Accepted | Debounce & auto-expire working |
| CHAT-F-037 | Share files and images | T7 (#111, 15 Nov), B11 (#105, 13 Nov), F6 (#106, 13 Nov), F7 (#106, 13 Nov) | Accepted | MIME & payload limits checked |
| CHAT-F-038 | Inline image preview | T7 (#111, 15 Nov), B11 (#105, 13 Nov), F6 (#106, 13 Nov) | Accepted | Inline previews rendered |
| CHAT-F-039 | Members-only file download | T7 (#111, 15 Nov), B11 (#105, 13 Nov) | Accepted | Non-members blocked |
| CHAT-F-041 | Search messages | T7 (#111, 15 Nov), B10 (#105, 13 Nov), F8 (#106, 13 Nov) | Accepted | Scoped search verified |
| CHAT-F-046 | Report a message | T8 (#112, 15 Nov), B12 (#105, 13 Nov), F10 (#110, 15 Nov) | Accepted | Stored in moderation queue |
| CHAT-F-047 | Review reports and remove messages | T8 (#112, 15 Nov), B12 (#105, 13 Nov), F10 (#110, 15 Nov) | Accepted | Live deletion confirmed |
| CHAT-F-048 | Ban and unban users | T8 (#112, 15 Nov), B12 (#105, 13 Nov), F10 (#110, 15 Nov) | Accepted | Instant socket termination |
| CHAT-F-049 | Mute users | T8 (#112, 15 Nov), B12 (#105, 13 Nov), F10 (#110, 15 Nov) | Accepted | Mute restriction verified |
| CHAT-F-051 | Audit log of admin actions | T8 (#112, 15 Nov), B12 (#105, 13 Nov), F10 (#110, 15 Nov) | Accepted | Immutable audit trail confirmed |
| CHAT-F-052 | Monitor clients and server activity | T8 (#112, 15 Nov), B2 (#105, 13 Nov), B12 (#105, 13 Nov), F10 (#110, 15 Nov) | Accepted | Telemetry & client monitor verified |
| CHAT-NF-001 | Performance | T9 (#124, 16 Nov) | Accepted | Target exceeded in T9 load test |
| CHAT-NF-002 | Reliability | T6 (#117, 16 Nov) | Accepted | Operational stability verified in T6 |
| CHAT-NF-003 | Usability | T9 (#124, 16 Nov) | Pending | Awaiting novice participant manual execution |
| CHAT-NF-004 | Robustness | T6 (#117, 16 Nov) | Accepted | Error boundary verified in T6 |
| CHAT-NF-005 | Scalability | T9 (#124, 16 Nov) | Accepted | 20 simultaneous connections verified |
| CHAT-NF-006 | Reliability | T6 (#117, 16 Nov), T9 (#124, 16 Nov) | Accepted | Order preserved via autoincrement ID |
| CHAT-NF-007 | Reliability | T9 (#124, 16 Nov) | Pending | Manual restart check not yet executed |
| CHAT-NF-008 | Compatibility | T9 (#124, 16 Nov) | Pending | Browser matrix execution pending |
| CHAT-NF-009 | Maintainability | S5 (#132, 17 Nov) | Pending | Pending S5 merge by Medha |
| CHAT-NF-010 | Portability | P3 (#120, 16 Nov) | Accepted | One-click setup scripts verified |
| CHAT-NF-011 | Data retention | B12 (#105, 13 Nov) | Accepted | Append-only schema verified |
| CHAT-SR-001 | Security: Reject invalid connections | T6 (#117, 16 Nov) | Accepted | Handshake validation confirmed |
| CHAT-SR-002 | Security: No duplicate usernames | T3 (#114, 16 Nov) | Accepted | Case-insensitive constraint |
| CHAT-SR-003 | Security: Private-message routing | T6 (#117, 16 Nov) | Accepted | DM isolation verified |
| CHAT-SR-004 | Security: Validate message data | T4 (#115, 16 Nov) | Accepted | 4,000 char cap & validation |
| CHAT-SR-005 | Security: No use of dead sockets | T6 (#117, 16 Nov) | Accepted | Stale sid check confirmed |
| CHAT-SR-006 | Security: Salted password hashing | T3 (#114, 16 Nov) | Accepted | Salted scrypt hashing verified |
| CHAT-SR-007 | Security: Session-authenticated sockets | T6 (#117, 16 Nov) | Accepted | Cookie auth & flags verified |
| CHAT-SR-008 | Security: Server-side authorisation | T5 (#116, 16 Nov), T8 (#112, 15 Nov) | Accepted | Service authorization verified |
| CHAT-SR-009 | Security: XSS-safe rendering + CSP | T1 (#107, 15 Nov), F3 (#106, 13 Nov) | Accepted | Text node rendering & CSP verified |
| CHAT-SR-010 | Security: Upload validation | T7 (#111, 15 Nov) | Accepted | Magic-byte checks verified |
| CHAT-SR-011 | Security: ORM-only SQL, length limits | T4 (#115, 16 Nov), T7 (#111, 15 Nov) | Accepted | Parameterized queries verified |
| CHAT-SR-012 | Security: Admin role + audit | T8 (#112, 15 Nov) | Accepted | Role check & audit log verified |
| CHAT-SR-013 | Security: Revocation on ban/logout | T3 (#114, 16 Nov), T8 (#112, 15 Nov) | Accepted | Instant session revocation verified |
| CHAT-SR-014 | Security: Origin-restricted WebSocket | T9 (#124, 16 Nov) | Accepted | Cross-origin check verified |

## Carried over / pending
- CHAT-NF-003, NF-007, NF-008: need manual browser and novice-user runs. They are recorded as "Not run" in the T9 manual test log. They are accepted only once the evidence exists.
- CHAT-NF-009: waited for the S5 coverage gate. S5 merged on 17 Nov (#132), so this card can now be accepted.

## Observations
- The first draft of the acceptance record dated the review in the future and cited evidence that did not exist yet. Moorty's review caught it and it was corrected.
- Demo videos were placeholders until recorded; see the Sprint 2 retrospective.
