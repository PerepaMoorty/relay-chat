# T9 Load-Test Run Log

Target: disposable local Relay server at `http://127.0.0.1:5065`, using an ignored SQLite database seeded with the repository's demo data. Load reports use 20 independent WebSocket connections authenticated as the same demo account and send 100 messages to `#general`.

| Run (UTC) | Mode | Result | Acknowledgements / deliveries | Delivery p95 | Ordering |
|---|---|---|---:|---:|---|
| 2026-11-15 19:08:01 | Concurrent | Fail | 100 / 2,000 | 1,475.030 ms | Ordering check flagged all 20 receivers |
| 2026-11-15 19:10:32 | Concurrent | Pass | 100 / 2,000 | 1,095.136 ms | All receiver message IDs were ordered |
| 2026-11-16 18:17:21 | Concurrent | Fail overall; latency and delivery passed | 100 / 2,000 | 1,144.766 ms (p95); 584.648 ms (p90) | All 20 receivers observed ID 11 before ID 9 |
| 2026-11-16 18:17:42 | Sequential sender, 20 clients | Pass | 100 / 2,000 | 21.234 ms (p95); 19.075 ms (p90) | All receivers observed IDs 108–207 in order |

The 2026-11-16 concurrent run is not a script-timing artifact. Every receiver observed the same inversion (11 then 9), while all 100 messages were acknowledged and all 2,000 deliveries arrived. In `relay/events/chat.py`, each `message:send` handler calls `messages.send` and then `notify.message_created`. `messages.send` commits the new row before the handler broadcasts it. With overlapping handlers, one message can commit first and a later message can broadcast first, so the received event sequence can differ from the assigned message-ID sequence. The client store sorts messages by ID for display, but that does not serialize server broadcasts.

The sequential run used the same 20 connected clients while one sender emitted the 100 messages one at a time. It passed the CHAT-NF-006 test-plan contract, which checks increasing IDs for sequential sends. The concurrent result remains a reproducible server-side interleaving behavior and should be discussed at the demo; it is distinct from the specified sequential acceptance case.

CHAT-NF-001 in `docs/test-plan.md` is at least 90% of messages delivered to all connected recipients within 2 seconds. In the two new runs, 100/100 messages met that target (100%). The concurrent run's delivery p95 was 1,144.766 ms, maximum 1,814.776 ms. The sequential run's delivery p95 was 21.234 ms, maximum 29.849 ms; its per-message maximum p95 was 23.712 ms. A separate acceptance record's 200 ms wording has not been reconciled with the test-plan target; this log reports both the source-of-truth criterion and measured values without claiming agreement from Naivadh.

Generated reports contain exact runtime, acknowledgement, delivery, target, ordering, and connection measurements:

- `docs/testing/reports/t9-load-test-local.json` — 2026-11-15 passing repeat
- `docs/testing/reports/t9-load-test-concurrent-2026-11-16.json` — concurrent run with ordering failure
- `docs/testing/reports/t9-load-test-sequential-2026-11-16.json` — sequential run passing all scripted criteria
