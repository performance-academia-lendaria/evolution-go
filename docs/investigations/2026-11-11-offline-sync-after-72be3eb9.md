# Local WhatsApp reconnect experiment

> Intermediate candidate, not final validation. All deliveries passed. The automatic
> restart field includes canceled-generation callback attempts in this image; it does
> not count actual new sockets. Subsequent lifecycle fixes require repeated cycles.

Status: **not_reproduced**

- Run: `72be3eb9`; label: `after`.
- Started: 2026-11-11T20:59:54.699346Z.
- Image ID: `sha256:db384371e4b0186174798c5442dcc76665c1c3b4aacc7fcdfc6a4f6ad06d41c7`.
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
