# T9 Load-Test Run Log

Target: disposable local Relay server at `http://127.0.0.1:5065`, using an ignored SQLite database seeded with the repository's demo data. Both runs used 20 independent WebSocket connections authenticated as the same demo account, with 100 concurrent messages sent to `#general`.

| Run (UTC) | Result | Acknowledgements / deliveries | Delivery p95 | Ordering |
|---|---|---:|---:|---|
| 2026-11-15 19:08:01 | Fail | 100 / 2,000 | 1,475.030 ms | Ordering check flagged all 20 receivers |
| 2026-11-15 19:10:32 | Pass | 100 / 2,000 | 1,095.136 ms | All receiver message IDs were ordered |

The first run exposed an ordering failure under concurrent sends; the repeat passed. Preserve this as a run-to-run difference, not as a stable performance guarantee. `docs/testing/reports/t9-load-test-local.json` contains the second run's full generated report, including exact runtime, acknowledgement and delivery measurements.

The test plan does not specify a numeric latency limit, so latency is reported as measurement only and is not classified as a pass or failure criterion.
