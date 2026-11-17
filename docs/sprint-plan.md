# Relay: Sprint Plan

Course: UE24CS341A Software Engineering, Section E, Team 8
Owner of this document: Medha Singh (Scrum Master)
Governing document: `00-CONTROL.md` v1.1 (2026-11-13)

## 1. Course timeline and recovery note

| Sprint | Course window |
|---|---|
| Sprint 1 | 19 Oct to 23 Oct 2026 |
| Sprint 2 | 26 Oct to 30 Oct 2026 |

**Recovery note.** The course windows above ended on 30 Oct. The team did not deliver on them. On
**2026-11-07** the team restarted with new roles, discarded the old repository history and began again from an empty
repository under a single control file. The first merge on the fresh repository (B1, project skeleton) landed on
2026-11-12. The windows above remain the official course sprint windows; the real working dates of each item are
recorded in the stand-up notes (`docs/scrum/sprint-N/standups.md`) and in the merge history of `develop`. This
deviation is documented here and in SRS v2.0 Appendix A, and will be explained at the final demo.

## 2. Team and roles

| Member | SRN | Role | Responsibilities |
|---|---|---|---|
| Lakshmi Narasimha Moorty Perepa | PES2UG24CS248 | Developer 1 (Backend), repo owner | All server code under `relay/` except templates and static files; the SAD; reviews and merges every PR; sets branch protection |
| Malepati Viswajith | PES2UG24CS259 | Developer 2 (Frontend) + Testing | Browser code (`relay/templates`, `relay/static`); all automated and manual tests; the test plan |
| Medha Singh | PES2UG24CS274 | Scrum Master | Board, sprints, ceremonies, CI workflow, PR template, this plan, scrum notes, releases, the control file; approves Moorty's PRs |
| Naivadh Shrivastava | PES2UG24CS297 | Product Owner | Backlog order, acceptance criteria and sign-off, SRS v2.0 and RTM, features list, diagrams, README, demo scripts and videos |

## 3. Tracking setup

- **GitHub Issues and a GitHub Project linked to the repository** mirror every FR, NFR and SR card, with assignee,
  Story Points field, Sprint field and labels. This is the copy the examiners check.
- Jira is not used (team decision, control v1.1). The registry ID (B8, F6, T3 and so on) is the key for branches,
  commits and PR titles, and a PR closes its GitHub issue with `Closes #NN` (control section 9).
- The board columns are To Do, In Progress, In Review, Done. A card moves to Done only when all of its PRs
  (control section 8.2) are merged.

## 4. Conventions (control section 9)

| Thing | Rule |
|---|---|
| Base branch | Always `develop` (`git checkout develop; git pull` before branching) |
| Branch | `<type>/<registry-id>-<slug>`; type is `feat`, `test`, `docs`, `ci`, `fix` or `release` |
| Commit | Starts with the registry ID; small, logical commits |
| PR title | `[<registry-id>] <title>` |
| PR body | The PR template, filled in, with `Closes #NN` for each issue the PR completes |
| Merge | Squash and merge by Moorty only, after CI is green and one approval. Medha approves Moorty's own PRs |
| Releases | At each sprint end Medha opens `release/vX.Y.Z` into `main`; Moorty merges with a merge commit and tags |
| Branch protection | `develop` and `main` require a PR, one approval and the `CI / test` check. No direct or force pushes |

## 5. Definition of Ready and Definition of Done (control section 10)

**Definition of Ready** (checked by the Product Owner before an item enters a sprint): requirement text, testable
acceptance criteria, story points, assignee, registry ID(s), and no unmerged dependency at the start of its wave.

**Definition of Done, per PR:**

- Built exactly to the contract in control section 6 (or an approved CCR changed it and the control file and SAD were updated first)
- Only owned files touched (control section 4); no placeholder of someone else's replaced
- `ruff check .` clean, `pytest` green locally and in CI
- *Done when* checks of the PR section executed; real-time behaviour checked in two browser windows where relevant
- PR title, branch and commits carry the registry ID; body lists the cards and `Closes #NN`
- Raised by the owner; approved; merged by Moorty
- Hand-off note posted

**Definition of Done, per card:** all PRs in control section 8.2 merged; its test case executed and recorded by
Viswajith; accepted by Naivadh at the sprint review.

## 6. Sprint goals and scope (control section 7)

| Sprint | Goal | Functional requirements |
|---|---|---|
| Sprint 1 | The v1.0 chat works end to end | F-001 to F-011, F-013 to F-023, F-027 to F-030, F-040 (28 FRs) |
| Sprint 2 | Relay behaves like a real chat product | F-012, F-026, F-037, F-038, F-039, F-041, F-046 to F-049, F-051, F-052 (11 FRs), plus NFR and SR verification |

**Change from the earlier plan.** F-038 (inline image preview) and F-052 (monitor clients and activity) move from
Sprint 1 to Sprint 2, because they depend on file upload (B11) and the admin API (B12). Naivadh records this in the
backlog.

**Out of scope (kept in the backlog, not built):** F-024, F-025, F-031 to F-036, F-042 to F-045, F-050. Also no
reactions, replies, pins, mentions, slash commands, browser notifications, export, profiles or avatars, blocking,
or room deletion. Won't: rate limiting, password reset, TLS, end-to-end encryption, Redis or multi-process.

## 7. Work registry: waves per sprint (control section 8.1)

A PR may start once everything under *Waits for* is merged into `develop`.

### Sprint 1

| Wave | PRs |
|---|---|
| 1 | B1 |
| 2 | S1, S2, P1, B2, B5, F1 |
| 3 | T1, B3, F2, F3, T2, T4 |
| 4 | B4, F4, F5, F6, F7, F8, S3 |
| 5 | B6, B7, T3 |
| 6 | B8, T5 |
| 7 | F9, T6 |
| 8 | S4, P2, R1, P4 |

### Sprint 2

| Wave | PRs |
|---|---|
| 9 | B9, B10, B11, B12, F10, P3 |
| 10 | T7, T8 |
| 11 | T9, S5 |
| 12 | S6, P5, R2, P6 |

| PR | Owner | Title | Waits for |
|---|---|---|---|
| B1 | M | Project skeleton, config, models, app factory, placeholders, SAD | none |
| S1 | S | CI workflow, PR template, issue templates | B1 |
| S2 | S | Sprint plan | B1 |
| P1 | P | SRS v2.0 + RTM + deviations, features list, diagrams | B1 |
| B2 | M | Presence registry + activity log service | B1 |
| B5 | M | Domain services: rooms, messages, receipts | B1 |
| F1 | V | Page shell, styles, vendored Socket.IO client, JS placeholders | B1 |
| T1 | V | Test harness, smoke + header tests, test plan | B1, B2, S1 |
| B3 | M | Broadcast layer (`notify`) + ack envelope and error containment | B2 |
| F2 | V | REST wrapper + socket connection | F1 |
| F3 | V | Client store + safe DOM helpers + time formatting | F1 |
| T2 | V | Unit tests: presence registry, activity | B2, T1 |
| T4 | V | Unit tests: rooms, messages, receipts services | B5, T1 |
| B4 | M | Accounts: auth service + auth REST + session revocation | B3 |
| F4 | V | Login / register view | F2, F3 |
| F5 | V | Sidebar: conversations, unread badges, online list, people search | F2, F3 |
| F6 | V | Conversation view | F2, F3 |
| F7 | V | Composer | F2, F3 |
| F8 | V | Dialogs: create room, browse/join, join by code, search | F2, F3 |
| S3 | S | CI hardening: remove "no tests" tolerance | T1 |
| B6 | M | REST: rooms, DMs, history, user lookup, `seed-demo` CLI | B4, B5 |
| B7 | M | Socket connect/disconnect, auth at handshake, presence, join/leave | B4, B5 |
| T3 | V | Tests: accounts, sessions, logout revocation | B4, T1 |
| B8 | M | Chat socket events + reconnect sync | B7 |
| T5 | V | Integration tests: rooms, DMs, history, unread, authorisation | B6, T1 |
| F9 | V | App controller: routing, wiring, reconnect + sync | F4 to F8, B8 |
| T6 | V | Multi-client real-time tests | B8, T1 |
| S4 | S | Sprint 1 scrum notes | Sprint 1 review |
| P2 | P | Sprint 1 acceptance record + RTM status update | T6, F9 |
| R1 | S | Release v0.1.0 | P2 |
| P4 | P | Sprint 1 demo video + demo script | R1 |
| B9 | M | Typing indicator events | B3, B5 |
| B10 | M | Message search | B5 |
| B11 | M | File upload + members-only download | B5 |
| B12 | M | Moderation: reports, bans, mutes, admin deletes, audit, admin API | B4, B5 |
| F10 | V | Admin console UI + report button + ban/session handling | F9 |
| T7 | V | Tests: typing, search, files | B9, B10, B11, T1 |
| T8 | V | Tests: moderation, admin, audit, revocation on ban | B12, T1 |
| T9 | V | Non-functional: load-test script + manual test records | T6, F10 |
| S5 | S | CI coverage gate of 70 percent on `relay/services` | T7, T8 |
| P3 | P | README + one-click demo scripts | F9, B6 |
| S6 | S | Sprint 2 scrum notes + final retro | Sprint 2 review |
| P5 | P | Sprint 2 acceptance record, final RTM, deviations, `srs.docx` | T9 |
| R2 | S | Release v1.0.0 | P5, S5 |
| P6 | P | Sprint 2 demo video | R2 |

## 8. Load per member

PRs per member per sprint, counted from the registry above (45 PRs in total):

| Member | Sprint 1 PRs | Sprint 2 PRs | Total |
|---|---|---|---|
| Moorty (backend) | 8 | 4 | 12 |
| Viswajith (frontend + testing) | 15 | 4 | 19 |
| Medha (scrum) | 5 | 3 | 8 |
| Naivadh (product) | 3 | 3 | 6 |
| **Total** | **31** | **14** | **45** |

Viswajith carries the largest load in Sprint 1, because he owns both the whole frontend and every test PR. Moorty
is the critical path: B1 to B3 to B4 to B7 to B8 gates the frontend controller (F9) and the real-time tests (T6).
Story points per card are tracked on the GitHub Project.

## 9. Ceremonies

| Ceremony | When | Length | Output (file) |
|---|---|---|---|
| Sprint planning | Day 1 of each sprint | 45 min | Goal, committed cards, wave plan in `docs/scrum/sprint-N/planning.md` |
| Stand-up | Daily, async in the team chat by 10:00 | 5 min each | Scrum Master's summary of the day, appended to `docs/scrum/sprint-N/standups.md` |
| Sprint review | Last day | 30 min | Demo, accept or reject per card by the Product Owner, in `review.md` (plus video by Naivadh) |
| Retrospective | After the review | 20 min | Went well, to improve, one or two actions in `retro.md`; actions become tasks |

Stand-up message format, hand-off notes, hand-off requests and the blocker rules follow control section 13. A PR
waiting for review more than 24 hours, a dependency waiting longer than its wave suggests, a failing CI the author
cannot fix in half a day, a contract dispute, or an agent insisting on editing someone else's file are all treated
as blockers and escalated to the Scrum Master.

## 10. Risks

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| 1 | Backend bottleneck: one developer owns 12 PRs and the critical path | High | High | Waves make the order explicit; paired test PRs start from the contract, not the code; blockers resolved within half a day | Moorty |
| 2 | Frontend and backend contract drift | Medium | High | Contract frozen in control section 6; changes only through an approved CCR and a version bump | Moorty, Viswajith |
| 3 | AI agents inventing APIs | Medium | High | Every agent loads the control file first; "contract is frozen" rule; Viswajith's tests check behaviour against section 6 | Viswajith |
| 4 | Merge conflicts from editing others' files | Medium | Medium | One owner per file (control section 4); placeholders created up front; hand-off requests for any cross-owner change | Medha |
| 5 | Tests lagging behind code | Medium | High | Backend PRs carry no tests; each has a paired test PR; coverage gate of 70 percent on `relay/services` (S5) | Viswajith |
| 6 | Schedule already slipped (course windows ended 30 Oct) | High | High | Fresh start with a single control file; daily stand-up summary; waves and blockers tracked every day; recovery documented honestly | Medha |
| 7 | Demo network (college Wi-Fi) | Medium | Medium | Run the demo on localhost with one-click scripts (P3); record the videos in advance | Naivadh |
