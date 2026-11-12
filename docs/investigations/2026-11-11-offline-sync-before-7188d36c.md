# Local WhatsApp reconnect experiment

Status: **not_reproduced**

- Run: `7188d36c`; label: `before`.
- Started: 2026-11-11T20:40:43.924156Z.
- Image ID: `sha256:30cfa84be63f28f17a9e7e78e49a323fc59d33a68a029cab5dea4c1577321c0e`.
- Method: local POST /instance/reconnect invokes ReconnectClient on target only.
- Recovery/observation window: 180 seconds.
- Initial/before marker timeout: 30 seconds. Target API restart delay is the unchanged application default (2 seconds).
- A during marker is confirmed only if target was offline at request and still offline after sender acknowledgement.
- Markers are synthetic; account identifiers, tokens and raw logs are excluded.

| Cycle | During send confirmed offline | Connected after | Preview | Completed | Before/during/after delivered | Target outbound delivered | Result |
|---|---|---|---|---|---|---|---|
| 1 | True | True | 1 | 1 | True/True/True | True | pass |
| 2 | True | True | 1 | 1 | True/True/True | True | pass |
| 3 | True | True | 1 | 1 | True/True/True | True | pass |
| 4 | True | True | 1 | 1 | True/True/True | True | pass |
| 5 | True | True | 1 | 1 | True/True/True | True | pass |
| 6 | True | True | 1 | 1 | True/True/True | True | pass |
| 7 | True | True | 1 | 1 | True/True/True | True | pass |
| 8 | True | True | 1 | 1 | True/True/True | True | pass |
| 9 | True | True | 1 | 1 | True/True/True | True | pass |
| 10 | True | True | 1 | 1 | True/True/True | True | pass |

Stop reason: Required cycles completed without reproducing the full incident. Ask Tuan before any dependency update.
