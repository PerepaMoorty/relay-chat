# Sprint 1 Review

> These notes were prepared by the Scrum Master from the merge history of `develop`, the acceptance records in `docs/acceptance/` and the team chat. Merge dates are the real dates the PRs landed.

| | |
|---|---|
| **Review date** | 2026-11-14 (per `docs/acceptance/sprint-1.md`) |
| **Goal** | The v1.0 chat works end to end |
| **Product Owner verdict** | All 27 listed functional requirements (the acceptance record says 28) and the 4 SETUP deliverables accepted. No card rejected |
| **Demo** | The product was run locally with `seed-demo` data: login, public and private messaging, rooms, receipts, reconnect |

## Cards, PRs, merge dates and verdicts

| Card | Title | PRs (merge date) | Verdict | Note |
|---|---|---|---|---|
| SETUP-skeleton | Repo Skeleton + SAD | B1 (#83, 12 Nov) | Accepted | Foundational skeleton |
| SETUP-CI | CI & Templates | S1 (#101, 12 Nov) | Accepted | CI operational |
| SETUP-harness | Test Harness | T1 (#107, 15 Nov) | Accepted | Quality harness established |
| SETUP-docs | Project Documents | P1 (#118, 16 Nov), S2 (#104, 13 Nov) | Accepted | Baseline docs approved |
| CHAT-F-001 | Connect to the chat server | B7 (#105, 13 Nov), F2 (#106, 13 Nov), T6 (#117, 16 Nov) | Accepted | Sockets upgrade cleanly |
| CHAT-F-002 | Prompt for username on connect | F4 (#106, 13 Nov), T3 (#114, 16 Nov) | Accepted | Gated entry view works |
| CHAT-F-003 | Unique usernames | B4 (#105, 13 Nov), T3 (#114, 16 Nov) | Accepted | Case-insensitive constraint |
| CHAT-F-004 | Send a text message | B5 (#105, 13 Nov), B8 (#105, 13 Nov), F7 (#106, 13 Nov), T6 (#117, 16 Nov) | Accepted | Instant delivery |
| CHAT-F-005 | Broadcast public messages | B8 (#105, 13 Nov), T6 (#117, 16 Nov) | Accepted | Multicast confirmed |
| CHAT-F-006 | Private (1:1) messages | B5 (#105, 13 Nov), B6 (#105, 13 Nov), F5 (#106, 13 Nov), T5 (#116, 16 Nov), T6 (#117, 16 Nov) | Accepted | Privacy preserved |
| CHAT-F-007 | Live display without refresh | F6 (#106, 13 Nov), F9 (#109, 15 Nov), T6 (#117, 16 Nov) | Accepted | Real-time DOM updates |
| CHAT-F-008 | Message timestamps | F3 (#106, 13 Nov), F6 (#106, 13 Nov), T5 (#116, 16 Nov) | Accepted | Correct localization |
| CHAT-F-009 | Online users list | B7 (#105, 13 Nov), F5 (#106, 13 Nov), T6 (#117, 16 Nov) | Accepted | Presence sync verified |
| CHAT-F-010 | Join notifications | B7 (#105, 13 Nov), F6 (#106, 13 Nov), T6 (#117, 16 Nov) | Accepted | Visible in #general |
| CHAT-F-011 | Leave notifications | B7 (#105, 13 Nov), F6 (#106, 13 Nov), T6 (#117, 16 Nov) | Accepted | Grace period prevents flash |
| CHAT-F-013 | Survive unexpected disconnects | B3 (#105, 13 Nov), B7 (#105, 13 Nov), T6 (#117, 16 Nov) | Accepted | No uncaught crashes |
| CHAT-F-014 | Graceful session termination | B4 (#105, 13 Nov), B7 (#105, 13 Nov), F9 (#109, 15 Nov), T3 (#114, 16 Nov) | Accepted | Complete session cleanup |
| CHAT-F-015 | Username-to-socket mapping | B2 (#105, 13 Nov), T2 (#113, 16 Nov) | Accepted | Registry verified |
| CHAT-F-016 | Reject empty or invalid messages | B5 (#105, 13 Nov), F7 (#106, 13 Nov), T4 (#115, 16 Nov) | Accepted | Validation enforced |
| CHAT-F-017 | Communication error handling | B3 (#105, 13 Nov), F2 (#106, 13 Nov), T6 (#117, 16 Nov) | Accepted | Uniform error schema |
| CHAT-F-018 | Register an account with a password | B4 (#105, 13 Nov), F4 (#106, 13 Nov), T3 (#114, 16 Nov) | Accepted | Secure onboarding |
| CHAT-F-019 | Log in with a session bound to the socket | B4 (#105, 13 Nov), B7 (#105, 13 Nov), F4 (#106, 13 Nov), T3 (#114, 16 Nov), T6 (#117, 16 Nov) | Accepted | Handshake authenticated |
| CHAT-F-020 | Persistent history with pagination | B6 (#105, 13 Nov), F6 (#106, 13 Nov), T5 (#116, 16 Nov) | Accepted | Cursor pagination verified |
| CHAT-F-021 | Offline message delivery | B5 (#105, 13 Nov), B6 (#105, 13 Nov), T5 (#116, 16 Nov) | Accepted | Sync recovery works |
| CHAT-F-022 | Create a group room | B6 (#105, 13 Nov), F8 (#106, 13 Nov), T5 (#116, 16 Nov) | Accepted | Custom channels operational |
| CHAT-F-023 | Browse, join and leave public rooms | B6 (#105, 13 Nov), F8 (#106, 13 Nov), T5 (#116, 16 Nov) | Accepted | Membership flows working |
| CHAT-F-027 | Delivered and read receipts | B5 (#105, 13 Nov), B8 (#105, 13 Nov), F6 (#106, 13 Nov), T6 (#117, 16 Nov) | Accepted | Checkmarks update live |
| CHAT-F-028 | Auto-reconnect with missed-message sync | B8 (#105, 13 Nov), F2 (#106, 13 Nov), F9 (#109, 15 Nov), T6 (#117, 16 Nov) | Accepted | Zero message duplication |
| CHAT-F-029 | Edit own message | B5 (#105, 13 Nov), B8 (#105, 13 Nov), F6 (#106, 13 Nov), T6 (#117, 16 Nov) | Accepted | Ownership check enforced |
| CHAT-F-030 | Delete own message | B5 (#105, 13 Nov), B8 (#105, 13 Nov), F6 (#106, 13 Nov), T6 (#117, 16 Nov) | Accepted | Body cleared cleanly |
| CHAT-F-040 | Unread counts | B5 (#105, 13 Nov), B6 (#105, 13 Nov), F3 (#106, 13 Nov), F5 (#106, 13 Nov), T5 (#116, 16 Nov) | Accepted | Watermarks clear badges |

## Carried over to Sprint 2
- F-012 (concurrent clients), F-026 (typing), F-037 to F-039 (files, previews, members-only download), F-041 (search), F-046 to F-049 and F-051 (moderation), F-052 (monitor clients). They were planned for Sprint 2 in control section 7.
- The Sprint 1 demo video was a placeholder at review time and had to be re-recorded (P4).

## Observations
- B2 to B12 and F2 to F8 were first merged into stacked branches instead of `develop`, and landed on `develop` on 13 Nov (#105, #106). From then on every PR targeted `develop`.
- The review took place before the T2 to T6 test PRs merged (16 Nov). The tests were verified when they merged.
