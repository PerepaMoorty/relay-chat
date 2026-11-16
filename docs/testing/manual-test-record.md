# Manual Browser Test Record — Relay

This is an execution record template. The scenarios below are **Not run** until a tester performs them in real browser sessions and fills in the actual result and evidence. Do not mark a case passed from automated tests or from a planned procedure.

## Run details

- Tester:
- Date and time (local):
- Application commit / branch:
- Server URL:
- Browser(s) and version(s):
- Test accounts:
- Evidence folder or links:

## Acceptance scenarios

| Test ID | Scenario | Expected result | Actual result / evidence | Status |
|---|---|---|---|---|
| TC-E2E-001 | Log in from two separate browser sessions and open `#general` | Both users reach the chat | — | Not run |
| TC-E2E-002 | Send messages in both directions | Each other user's message appears live without refresh | — | Not run |
| TC-E2E-003 | Observe online users and join/leave notices | Presence changes appear in the interface | — | Not run |
| TC-E2E-004 | Start a direct message and exchange messages | Messages reach only the intended participant | — | Not run |
| TC-E2E-005 | Create, join, and leave a room | Room list and membership update correctly | — | Not run |
| TC-E2E-006 | Scroll back through room history | Older messages load in the expected order | — | Not run |
| TC-E2E-007 | Generate unread messages, then open the room | Unread indicators and receipts update correctly | — | Not run |
| TC-E2E-008 | Edit and delete messages | Changes appear live and deleted content is removed | — | Not run |
| TC-E2E-009 | Restart the server during an active chat | Client reconnects and synchronizes without lost or duplicate messages | — | Not run |

## Execution notes

For each case, record the steps actually performed, the observed result, pass/fail status, and evidence (screenshots, logs, or a short recording). For a failed case, include the test ID, expected result, actual result, reproduction steps, and relevant logs. Keep a separate copy per execution run rather than overwriting earlier results.
