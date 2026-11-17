# Sprint 2 Retrospective

> These notes were prepared by the Scrum Master from the merge history of `develop`, the acceptance records in `docs/acceptance/` and the team chat. Merge dates are the real dates the PRs landed.

Drafted by the Scrum Master from the sprint evidence. To be confirmed with the team.

## What went well
- All Sprint 2 features landed and are covered by automated tests; CI enforces lint, tests and a 70 percent coverage gate on `relay/services`.
- Test PRs ran in parallel with the frontend once the backend was on `develop`.
- Reviewers read the acceptance record against the evidence and sent it back for fixes instead of accepting it.

## What to improve
- Acceptance evidence should exist before an item is marked accepted. NF-009 was marked accepted before S5 merged, and NF-002 cited manual tests that had not run.
- Manual NFR tests (NF-003, NF-007, NF-008) were left until the end.
- The release flow (R1 and R2) was last-minute: the v0.1.0 changelog was merged into `develop` while `main` still only had the initial commit.
- Demo videos were committed as placeholders first and replaced with real recordings on 17 Nov. Record from the running app the first time.

## Actions
| Action | Owner | Done when |
|---|---|---|
| Mark an item accepted only after its evidence is merged | Naivadh | Final acceptance record has no unmet evidence |
| Run and record the manual NFR tests | Viswajith | T9 log has no "Not run" rows |
| Tag v0.1.0 and v1.0.0 on `main` through release PRs | Medha, Moorty | Both tags exist on `main` |
| Record both demo videos from the running app | Naivadh | Done on 17 Nov: real `sprint-1.mp4` and `sprint-2.mp4` are in `docs/demos/` |
