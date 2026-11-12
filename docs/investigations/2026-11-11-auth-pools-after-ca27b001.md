# Local PostgreSQL auth connection experiment

Status: **stable**

- Run: `ca27b001`; label: `after`.
- Image: `sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd`.
- Harness commit: `86eb808cc5cf75bc855ac97f28e950215467b716`.
- Started: 2026-11-12T01:37:58.824576Z.
- Method: target-only `/instance/reconnect`; sender stays online.
- Observer: maintenance database `postgres`; measured database `offline_sync_auth`.
- Settling: 10s initially, 3s after each cycle, 30s finally.

| Sample | Total | Active | Idle | Sync complete | Probe delivered |
|---|---:|---:|---:|---|---|
| initial | 3 | 0 | 3 | — | — |
| 1 | 3 | 0 | 3 | True | True |
| 2 | 3 | 0 | 3 | True | True |
| 3 | 2 | 0 | 2 | True | True |
| 4 | 2 | 0 | 2 | True | True |
| 5 | 2 | 0 | 2 | True | True |
| 6 | 2 | 0 | 2 | True | True |
| 7 | 2 | 0 | 2 | True | True |
| 8 | 2 | 0 | 2 | True | True |
| 9 | 2 | 0 | 2 | True | True |
| 10 | 2 | 0 | 2 | True | True |
| 11 | 2 | 0 | 2 | True | True |
| 12 | 2 | 0 | 2 | True | True |
| 13 | 2 | 0 | 2 | True | True |
| 14 | 2 | 0 | 2 | True | True |
| 15 | 2 | 0 | 2 | True | True |
| 16 | 2 | 0 | 2 | True | True |
| 17 | 2 | 0 | 2 | True | True |
| 18 | 2 | 0 | 2 | True | True |
| 19 | 2 | 0 | 2 | True | True |
| 20 | 2 | 0 | 2 | True | True |
| final | 2 | 0 | 2 | — | — |

Final minus initial: **-1** connections.
Verdict: `stable` (counts observed over this run only).

No production database was consulted. Session query text, message content,
phone numbers and credentials were neither recorded nor printed.
