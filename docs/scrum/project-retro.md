# Project Retrospective: Relay (Team 8)

> These notes were prepared by the Scrum Master from the merge history of `develop`, the acceptance records in `docs/acceptance/` and the team chat. Merge dates are the real dates the PRs landed.

Drafted by the Scrum Master. To be read and agreed with the team before the final demo.

## What happened
The course sprint windows (19 to 23 Oct and 26 to 30 Oct 2026) passed without a delivered product. On 7 Nov the team restarted with new roles, discarded the old repository and worked from a single control file. All code and documents merged between 12 and 17 Nov 2026. 45 PRs were planned in the registry. `develop` ends with a working chat product, 66 or more automated tests and CI on every PR.

## What worked
- **One control file.** The contract, file ownership and the PR registry were fixed in one document, so four people and four AI agents stayed compatible without seeing each other's work.
- **One owner per file, placeholders up front.** Almost no merge conflicts.
- **Paired testing.** Backend PRs carried no tests, and a separate test PR was written against the contract. That is how the contract was actually verified.
- **CI as a gate.** Ruff, pytest and the coverage gate ran on every PR. The CI import bug was found and fixed the first time real tests ran.
- **Review by the repo owner, approval of his own PRs by the Scrum Master.** It kept the course rules visible in the history.

## What did not
- **The schedule.** The sprint windows were missed. The recovery is documented in `docs/sprint-plan.md` and SRS Appendix A.
- **Stacked PRs.** For a day, most code sat on branches instead of `develop`.
- **Tracking tools.** Jira was set up and then dropped. GitHub Issues and the Project would have been enough from the start.
- **Evidence timing.** Acceptance was written before some evidence existed.
- **Placeholders left in.** Demo videos and some PR descriptions stayed placeholders longer than they should.

## Working with AI agents and the control file
- Agents are only as consistent as the file they are given. When the control file said "this file wins" and froze the contract, agents stopped inventing endpoints.
- Agents cannot see the repository. Handing them a context pack (the real current files) avoided most wrong assumptions.
- Agents reproduce what the guide says, including mistakes: the first CI workflow ran `pytest` and not `python -m pytest`, and an early acceptance record contained future dates. Each human still has to check the output and be able to explain it at the viva.
- Changing the process (dropping Jira) needed a versioned change to the control file and a message to every member, otherwise each agent kept following the old rule.
- A version number on the control file ("Control v1.1 loaded") made it easy to tell whether an agent was working from the current rules.

## Lessons for next time
1. Decide the tracking tool on day one and use only that.
2. Make every PR target `develop` and update your branch after each merge.
3. Run the CI workflow against a real test on day one, not once tests arrive.
4. Record demo videos from the running product and commit the real file.
5. Mark an item accepted only when its evidence is merged and can be opened.
