# Local WhatsApp reconnect experiment

> Intermediate candidateea877fb passed these checks. A later global proxy fallback
> correction requires another candidate image and final recorded validation.

Status: **not_reproduced**

- Run: `450d363f`; label: `after`.
- Started: 2026-11-11T21:46:13.104205Z.
- Image ID: `sha256:12bfe23376cd574c82b2df45e2ac5206fa8b36766cc9e076fdde7702b67bf170`.
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

Stop reason: Required candidate cycles completed; this establishes local compatibility, not the production incident's cause.
