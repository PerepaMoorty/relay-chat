# Sprint 2 Planning

> These notes were prepared by the Scrum Master from the merge history of `develop`, the acceptance records in `docs/acceptance/` and the team chat. Merge dates are the real dates the PRs landed.

| | |
|---|---|
| **Sprint** | Sprint 2 (course window 26 to 30 Oct 2026; actual work 13 to 17 Nov 2026) |
| **Goal** | Relay behaves like a real chat product |

## Committed scope (control section 7)
12 functional requirements: F-012, F-026, F-037, F-038, F-039, F-041, F-046 to F-049, F-051, F-052 (control section 7 says 11, an off-by-one). Plus verification of all NFRs and SRs.

## Wave plan (control section 8.1)
| Wave | PRs | Owner |
|---|---|---|
| 9 | B9, B10, B11, B12, F10, P3 | Moorty, Viswajith, Naivadh |
| 10 | T7, T8 | Viswajith |
| 11 | T9, S5 | Viswajith, Medha |
| 12 | S6, P5, R2, P6 | Medha, Naivadh |

## Decisions at planning
- F-038 and F-052 moved from Sprint 1 to Sprint 2 (they depend on B11 and B12).
- Coverage gate: S5 sets `--cov=relay/services --cov-fail-under=70` and runs pytest as `python -m pytest`. Coverage is Viswajith's job, so S5 was only raised once coverage was at least 70 percent. The threshold is never lowered.
- Jira is dropped (control v1.1). GitHub Issues and the Project are the only board.
- Sprint 2 ends with a release v1.0.0, which freezes development. After that only bug fixes with `fix/` branches.
