# Local WhatsApp reconnect experiment

> Evidence correction: the completion log counter used by this historical run was invalid.
> Ignore the Completed column and conclusions about missing sync completion. Delivery and
> forced-disconnection measurements remain valid. A corrected reference run is required.

Status: **not_reproduced**

- Run: `588b5cb3`; label: `before`.
- Started: 2026-11-11T18:01:00.256200Z.
- Image ID: `sha256:30cfa84be63f28f17a9e7e78e49a323fc59d33a68a029cab5dea4c1577321c0e`.
- Method: local `POST /instance/reconnect` invokes `ReconnectClient` on target only.
- Recovery/observation window: 180 seconds.
- Initial/before marker timeout: 30 seconds. Target API restart delay is the unchanged application default (2 seconds).
- A during marker is confirmed only if target was offline at request and still offline after sender acknowledgement.
- Markers are synthetic; account identifiers, tokens and raw logs are excluded.

| Cycle | During send confirmed offline | Connected after | Preview | Completed | Before/during/after delivered | Target outbound delivered | Result |
|---|---|---|---|---|---|---|---|
| 1 | True | True | 1 | 0 | True/True/True | True | delivery_pass_sync_unobserved |
| 2 | True | True | 1 | 0 | True/True/True | True | delivery_pass_sync_unobserved |
| 3 | True | True | 1 | 0 | True/True/True | True | delivery_pass_sync_unobserved |
| 4 | True | True | 1 | 0 | True/True/True | True | delivery_pass_sync_unobserved |
| 5 | True | True | 1 | 0 | True/True/True | True | delivery_pass_sync_unobserved |
| 6 | True | True | 1 | 0 | True/True/True | True | delivery_pass_sync_unobserved |
| 7 | True | True | 1 | 0 | True/True/True | True | delivery_pass_sync_unobserved |
| 8 | True | True | 1 | 0 | True/True/True | True | delivery_pass_sync_unobserved |
| 9 | True | True | 1 | 0 | True/True/True | True | delivery_pass_sync_unobserved |
| 10 | True | True | 1 | 0 | True/True/True | True | delivery_pass_sync_unobserved |

Stop reason: Required cycles completed without reproducing the full incident. Ask Tuan before any dependency update.
