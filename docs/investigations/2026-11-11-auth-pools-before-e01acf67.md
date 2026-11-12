# Local PostgreSQL auth connection experiment

Status: **stopped**

- Run: `e01acf67`; label: `before`.
- Image: `sha256:30cfa84be63f28f17a9e7e78e49a323fc59d33a68a029cab5dea4c1577321c0e`.
- Harness commit: `b5d01aa36605341f1e4d2bc12668876c72b9a59b`.
- Started: 2026-11-12T01:31:45.432726Z.
- Method: target-only `/instance/reconnect`; sender stays online.
- Observer: maintenance database `postgres`; measured database `offline_sync_auth`.
- Settling: 10s initially, 3s after each cycle, 30s finally.

| Sample | Total | Active | Idle | Sync complete | Probe delivered |
|---|---:|---:|---:|---|---|

Stop reason: STOP: warm-up delivery failed; no valid baseline.

No production database was consulted. Session query text, message content,
phone numbers and credentials were neither recorded nor printed.
