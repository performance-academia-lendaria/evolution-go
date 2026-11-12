# Local WhatsApp reconnect experiment

> Intermediate candidate 5b0e96e: local delivery checks passed, but later lifecycle
> review fixes require a new image and repeated final validation. Not the final
> before/after result or a two-hour stability test.

Status: **not_reproduced**

- Run: `af051f2f`; label: `after`.
- Started: 2026-11-11T21:11:38.083222Z.
- Image ID: `sha256:8d7165a354a9e03bb48b61d1d2db1a0af120fdf8463a080f19ab91f71901096f`.
- Method: real TCP closure through target-only CONNECT proxy; application's Disconnected handler reconnects.
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

Socket outage: 10 seconds; independent gate restore within 20 seconds.

| Cycle | Tunnels closed | Disconnected-triggered restarts | Sender remained authenticated | Gate restored |
|---|---|---|---|---|
| 1 | 1 | 1 | True | True |
| 2 | 1 | 1 | True | True |
| 3 | 1 | 1 | True | True |
| 4 | 1 | 1 | True | True |
| 5 | 1 | 1 | True | True |
| 6 | 1 | 1 | True | True |
| 7 | 1 | 1 | True | True |
| 8 | 1 | 1 | True | True |
| 9 | 1 | 1 | True | True |
| 10 | 1 | 1 | True | True |
