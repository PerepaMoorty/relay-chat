# Sprint 1 Retrospective

> These notes were prepared by the Scrum Master from the merge history of `develop`, the acceptance records in `docs/acceptance/` and the team chat. Merge dates are the real dates the PRs landed.

Drafted by the Scrum Master from the sprint evidence. To be confirmed with the team.

## What went well
- The control file gave four people and four AI agents one contract. There were no endpoint or payload disputes.
- One owner per file and placeholders created up front meant almost no merge conflicts.
- Paired test PRs found real problems early. The suite reached 66 passing tests and CI stayed green after the first fix.
- Moorty reviewed and merged PRs quickly, and review comments on S2 were specific and fixed in minutes.

## What to improve
- Stacked PRs were merged into the branch beneath them, so `develop` was missing most of the code for a day.
- CI failed on the first real test PR because `pytest` could not import `relay`. This was only found when T1 arrived, since the workflow had run with no tests.
- PR descriptions were often left as the blank template.
- Dates in documents were sometimes written before they happened (for example a planned review date).
- Jira was set up but not used, which cost time before the team decided to drop it.
- The demo video was a placeholder at review time.

## Actions
| Action | Owner | Done when |
|---|---|---|
| Every PR targets `develop`; after a merge, update your next branch with `git fetch origin` then `git merge origin/develop` | Everyone | No stacked PRs in Sprint 2 |
| Fill in the PR template (registry ID, what changed, `Closes #NN`) before asking for review | Everyone | Reviewer finds no blank templates |
| Use real dates in documents; write "planned" for future dates | Naivadh, Medha | No future dates in records |
