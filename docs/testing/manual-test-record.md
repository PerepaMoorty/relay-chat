# Manual Browser Test Record — Relay

## Run details

- Tester: Viswajith
- Date and time (local): 2026-11-17, approximately 00:03–00:12 IST
- Application commit / branch: `f4d233a` / `test/T9-load-test-manual-records`; no application code was changed for this run
- Server URL: `http://127.0.0.1:5065` (local disposable SQLite database seeded with demo data)
- Browser(s) and version(s): Opera normal window (Alice) and Opera private window (Bob); version not captured
- Test accounts: `alice`, `bob`
- Evidence: generated load reports under `docs/testing/reports/`; no browser screenshots were saved

## E2E acceptance scenarios

| Test ID | Scenario | Expected result | Actual result / evidence | Status |
|---|---|---|---|---|
| TC-E2E-001 | Log in from two separate browser sessions and open `#general` | Both users reach the chat | Alice was signed in from the normal Opera window and Bob from the private Opera window. Both reached the chat; Alice's online list showed Bob. | Pass |
| TC-E2E-002 | Send messages in both directions | Each other user's message appears live without refresh | Alice submitted the same test text during repeated attempts; three entries were visible in Alice's history. Bob's receipt and the reverse direction were not verified because the private window was minimized and could not be brought forward by the UI control. | Not run |
| TC-E2E-003 | Observe online users and join/leave notices | Presence changes appear in the interface | Alice's online list showed Alice and Bob at the same time. No join or leave was induced and verified. | Not run |
| TC-E2E-004 | Start a direct message and exchange messages | Messages reach only the intended participant | No DM exchange or third-user visibility check was performed. | Not run |
| TC-E2E-005 | Create, join, and leave a room | Room list and membership update correctly | No room lifecycle check was performed. | Not run |
| TC-E2E-006 | Scroll back through room history | Older messages load in the expected order | The chat showed the loaded T9 messages in increasing order while moving toward the newest messages. Loading older history was not verified. | Not run |
| TC-E2E-007 | Generate unread messages, then open the room | Unread indicators and receipts update correctly | No unread/read receipt scenario was performed. | Not run |
| TC-E2E-008 | Edit and delete messages | Changes appear live and deleted content is removed | No edit or delete action was performed. | Not run |
| TC-E2E-009 | Restart the server during an active chat | Client reconnects and synchronizes without lost or duplicate messages | No restart/reconnect browser scenario was performed. | Not run |
| TC-E2E-010 | Not defined in the checked-in test plan or record | A defined scenario and expected result are required | `docs/test-plan.md` and this record define TC-E2E-001 through TC-E2E-009 only. No TC-E2E-010 scenario was supplied. | Not run |

## Other T9 checks

| Test ID | Actual result / evidence | Status |
|---|---|---|
| TC-PERF-01 / CHAT-NF-001 | Both 20-client runs delivered all 100 messages to all 20 receivers within 2,000 ms (100%). Concurrent delivery p95: 1,144.766 ms; sequential delivery p95: 21.234 ms. Full reports: `t9-load-test-concurrent-2026-11-16.json` and `t9-load-test-sequential-2026-11-16.json`. | Pass |
| TC-SCALE-01 / CHAT-NF-005 | 20 WebSocket clients connected; 100 acknowledgements and 2,000/2,000 deliveries in each run. | Pass |
| TC-ORD-01 / CHAT-NF-006 | Sequential mode passed increasing message IDs at all receivers. Concurrent mode exposed a consistent event-order inversion at all 20 receivers; see the run log. | Pass for the specified sequential case; concurrent ordering issue recorded |
| TC-SEC-14 | Same-origin Socket.IO polling request returned HTTP 200; `Origin: http://evil.example` returned HTTP 400. | Pass |
| TC-REL-02 | Restart/reconnect-within-10-seconds check not performed. | Not run |
| TC-UX-01 | Novice-user usability check not performed; no novice participant was available. | Not run |
| TC-COMP-01 | Full Chrome/Edge/Firefox and 360/1366/1920 px compatibility matrix not performed. | Not run |
| TC-PORT-01 | Cross-operating-system check not performed; this run used Windows 11 only. | Not run |

## Latency wording

The checked-in test plan defines CHAT-NF-001 as: at least 90% of messages must reach all connected recipients within 2 seconds. This run measured 100% within 2 seconds. A separate acceptance record states a 200 ms target; no agreement with Naivadh was obtained during this run, so that conflicting record still needs reconciliation before final acceptance.

## Execution limitations

The checked-in manual record and test plan contain nine E2E scenarios, not ten. The private Opera window was minimized during follow-up checks and the UI controller could not restore it, so recipient-side live delivery, presence transitions, DMs, room lifecycle, receipts, edit/delete, and reconnect behavior remain unverified. Do not treat these cases as passed based on the load reports.
