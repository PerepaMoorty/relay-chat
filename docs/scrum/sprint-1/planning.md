# Sprint 1 Planning

> These notes were prepared by the Scrum Master from the merge history of `develop`, the acceptance records in `docs/acceptance/` and the team chat. Merge dates are the real dates the PRs landed.

| | |
|---|---|
| **Sprint** | Sprint 1 (course window 19 to 23 Oct 2026; actual work 12 to 16 Nov 2026, see the recovery note in `docs/sprint-plan.md`) |
| **Goal** | The v1.0 chat works end to end |
| **Scrum Master** | Medha Singh |
| **Product Owner** | Naivadh Shrivastava |

## Committed scope (control section 7)
27 functional requirements: F-001 to F-011, F-013 to F-023, F-027 to F-030, F-040 (control section 7 says 28, but the IDs it lists are 27; Sprint 2 lists 12 and not 11; the total of 39 is correct). Plus the four SETUP cards (repo skeleton and SAD, CI and PR template, client scaffold and test harness, project documents).

## Wave plan (control section 8.1)
| Wave | PRs | Owner |
|---|---|---|
| 1 | B1 | Moorty |
| 2 | S1, S2, P1, B2, B5, F1 | Medha, Naivadh, Moorty, Viswajith |
| 3 | T1, B3, F2, F3, T2, T4 | Viswajith, Moorty |
| 4 | B4, F4 to F8, S3 | Moorty, Viswajith, Medha |
| 5 | B6, B7, T3 | Moorty, Viswajith |
| 6 | B8, T5 | Moorty, Viswajith |
| 7 | F9, T6 | Viswajith |
| 8 | S4, P2, R1, P4 | Medha, Naivadh |

## Decisions at planning
- The control file v1.0 is the single source of truth for the contract, file ownership and the PR registry.
- Each backend PR carries no tests. Viswajith writes a paired test PR against the contract.
- F-038 (inline image preview) and F-052 (monitor clients) move to Sprint 2 because they depend on file upload (B11) and the admin API (B12).
- Could-tier cards stay in the backlog and are not built.

## Risks carried in
Backend bottleneck (one developer, 12 PRs), contract drift, agents inventing APIs, merge conflicts from editing other people's files, tests lagging behind code, schedule already slipped. See `docs/sprint-plan.md` section 10.
