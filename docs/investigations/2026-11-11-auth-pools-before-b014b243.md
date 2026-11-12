# Local PostgreSQL auth connection experiment

Status: **growth_observed**

- Run: `b014b243`; label: `before`.
- Image: `sha256:30cfa84be63f28f17a9e7e78e49a323fc59d33a68a029cab5dea4c1577321c0e`.
- Harness commit: `86eb808cc5cf75bc855ac97f28e950215467b716`.
- Started: 2026-11-12T01:33:15.846067Z.
- Method: target-only `/instance/reconnect`; sender stays online.
- Observer: maintenance database `postgres`; measured database `offline_sync_auth`.
- Settling: 10s initially, 3s after each cycle, 30s finally.

| Sample | Total | Active | Idle | Sync complete | Probe delivered |
|---|---:|---:|---:|---|---|
| initial | 4 | 0 | 4 | — | — |
| 1 | 6 | 0 | 6 | True | True |
| 2 | 8 | 0 | 8 | True | True |
| 3 | 10 | 0 | 10 | True | True |
| 4 | 12 | 0 | 12 | True | True |
| 5 | 14 | 0 | 14 | True | True |
| 6 | 16 | 0 | 16 | True | True |
| 7 | 18 | 0 | 18 | True | True |
| 8 | 20 | 0 | 20 | True | True |
| 9 | 22 | 0 | 22 | True | True |
| 10 | 24 | 0 | 24 | True | True |
| 11 | 26 | 0 | 26 | True | True |
| 12 | 28 | 0 | 28 | True | True |
| 13 | 30 | 0 | 30 | True | True |
| 14 | 32 | 0 | 32 | True | True |
| 15 | 34 | 0 | 34 | True | True |
| 16 | 36 | 0 | 36 | True | True |
| 17 | 38 | 0 | 38 | True | True |
| 18 | 40 | 0 | 40 | True | True |
| 19 | 42 | 0 | 42 | True | True |
| 20 | 44 | 0 | 44 | True | True |
| final | 44 | 0 | 44 | — | — |

Final minus initial: **+40** connections.
Verdict: `growth_observed` (counts observed over this run only).

No production database was consulted. Session query text, message content,
phone numbers and credentials were neither recorded nor printed.
