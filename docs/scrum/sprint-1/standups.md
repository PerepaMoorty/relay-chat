# Sprint 1 Stand-up Summaries

> These notes were prepared by the Scrum Master from the merge history of `develop`, the acceptance records in `docs/acceptance/` and the team chat. Merge dates are the real dates the PRs landed.

The summaries use the format from control section 13, built from what merged each day.

```text
[daily] 2026-11-12
Merged:        B1 (#83), F1 (#95), S1 (#101)
Now unblocked: B2, B5 (Moorty); F2, F3 (Viswajith); S2 (Medha); P1 (Naivadh)
In review:     none
At risk:       none
Process:       fresh repository started; branch protection and CI check in place after S1
```
```text
[daily] 2026-11-13
Merged:        S2 (#104), B2 to B12 (#105), F2 to F8 (#106)
Now unblocked: T1 (Viswajith), B3 onward for the test PRs, F9 (Viswajith)
In review:     S2 (#104) had two review comments (real dates, B2 missing from the critical path), fixed the same day
At risk:       B2 to B12 and F2 to F8 had been merged into the branch below them instead of develop, so develop only had B1, F1 and S1
               -> action: Moorty opened #105 to land B2 to B12, Viswajith opened #106 for F2 to F8; rule from now on: every PR targets develop
Decision:      the team dropped Jira. Control v1.1 published: GitHub Issues and the Project are the only board, registry ID replaces the Jira key
```
```text
[daily] 2026-11-15
Merged:        S1 fix (#108), T1 (#107), F9 (#109)
Now unblocked: T2 to T6 (Viswajith), S3 (Medha)
In review:     none
At risk:       T1 failed CI with ModuleNotFoundError: relay
               -> action: Medha changed the CI test command to `python -m pytest` (#108), merged, T1 re-ran green
```
```text
[daily] 2026-11-16
Merged:        T2 (#113), T3 (#114), T4 (#115), T5 (#116), T6 (#117), P1 (#118), P2 (#119), S3 (#126)
Now unblocked: R1 (Medha), P4 (Naivadh)
In review:     none
At risk:       Sprint 1 demo video was still a placeholder
               -> action: Naivadh to record it (see review.md, carried-over items)
Cards to move to Done: every Sprint 1 card whose PR list is now complete
```
