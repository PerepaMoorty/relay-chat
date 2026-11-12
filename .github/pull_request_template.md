**Jira:** RLY-<n>

> Only files you own (control §4). Title format: `RLY-<n>: [<registry-id>] <title>`

## Registry ID(s)

<!-- e.g. B8 -->

## Cards contributed / completed

<!-- List EVERY card this PR contributes to. Use `Closes #NN` only for GitHub issues this PR fully completes (control §8.2). -->

- Contributes to: RLY-..., RLY-...
- Closes #NN

## What changed

<!-- 2-4 lines. Files added or replaced. -->

## How it was tested

<!-- Commands run and results, e.g. `ruff check .`, `pytest`, two-browser-window check for real-time behaviour. -->

## Definition of Done (control §10)

- [ ] Built exactly to §6 (or a CCR approved the change, and both the control file and the SAD were updated first)
- [ ] Only owned files touched (§4); no placeholder of someone else's replaced
- [ ] `ruff check .` clean, `pytest` green locally and in CI
- [ ] *Done when* checks of the PR section executed; real-time behaviour checked in **two browser windows** (two different users, e.g. a normal and an incognito window) where relevant
- [ ] PR title, branch and commits carry the Jira key; body lists the cards and `Closes #NN`
- [ ] Raised by the owner; approved; merged by Moorty
- [ ] Hand-off note posted (§13)
