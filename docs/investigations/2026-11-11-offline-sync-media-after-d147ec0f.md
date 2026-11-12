# Local media and continuous traffic verification

Status: **pass**

- Run: `d147ec0f`; label: `after`.
- Image: `sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd`.
- Harness commit: `3abf9554217038648b89e92e22244bf069f4523e`.
- Started: 2026-11-12T02:23:38.873122Z.
- Requested duration: 7200 seconds; interval: 300 seconds.
- Only synthetic content, between two exclusive test accounts; no forced outages.
- PNG solid color; WAV 1-second tone sent through normal local audio conversion.
- Delivery requires matching hashed ID, incoming Message and correct media kind.
- Authentication sampled every 2 seconds between batches and before each send.

| Batch | Text delivered | Image delivered | Audio delivered |
|---|---|---|---|
| 1 | 2/2 | 2/2 | 2/2 |
| 2 | 2/2 | 2/2 | 2/2 |
| 3 | 2/2 | 2/2 | 2/2 |
| 4 | 2/2 | 2/2 | 2/2 |
| 5 | 2/2 | 2/2 | 2/2 |
| 6 | 2/2 | 2/2 | 2/2 |
| 7 | 2/2 | 2/2 | 2/2 |
| 8 | 2/2 | 2/2 | 2/2 |
| 9 | 2/2 | 2/2 | 2/2 |
| 10 | 2/2 | 2/2 | 2/2 |
| 11 | 2/2 | 2/2 | 2/2 |
| 12 | 2/2 | 2/2 | 2/2 |
| 13 | 2/2 | 2/2 | 2/2 |
| 14 | 2/2 | 2/2 | 2/2 |
| 15 | 2/2 | 2/2 | 2/2 |
| 16 | 2/2 | 2/2 | 2/2 |
| 17 | 2/2 | 2/2 | 2/2 |
| 18 | 2/2 | 2/2 | 2/2 |
| 19 | 2/2 | 2/2 | 2/2 |
| 20 | 2/2 | 2/2 | 2/2 |
| 21 | 2/2 | 2/2 | 2/2 |
| 22 | 2/2 | 2/2 | 2/2 |
| 23 | 2/2 | 2/2 | 2/2 |
| 24 | 2/2 | 2/2 | 2/2 |
| 25 | 2/2 | 2/2 | 2/2 |

- recovery_seconds: 60

- drop_counts: {"target": 1, "sender": 0}

- recovered_drops: 1

- drops: [{"role": "target", "disconnected_epoch": 1794456873.568193, "origin": "Disconnected_log", "recovered": true, "probe": {"kind": "text", "request_utc": "2026-11-12T04:14:38.089449Z", "accepted_utc": "2026-11-12T04:14:38.696455Z", "message_id_sha256": "25308fb6be7269ae2a6a6426ccaeba1d785ea4df8886636f902c11bca28f7179", "destination_sha256": "a02a2694ed5ebcf4d57273e1cf6fbce2efb5756998176ea2eff76b68763e9ffe", "delivered": true}, "connected_epoch": 1794456877.333074, "sync_completed_epoch": 1794456877.36868, "recovered_epoch": 1794456878.7490335, "recovery_seconds": 5.181}]

- interrupted_send_attempts: 0

- last_health_utc: "2026-11-12T04:23:45.381353Z"

- drops_per_hour: {"target": 0.5, "sender": 0.0}

- observed_until_utc: "2026-11-12T04:23:45.300971Z"

- finished_utc: "2026-11-12T04:23:45.641773Z"

- elapsed_seconds: 7206.791

- authentication_samples: 3660

- target_logs: {"connected": 1, "offline_preview": 0, "offline_completed": 1, "automatic_restart": 1, "process_handler_panics": 0, "process_stream_errors": 0}

- sender_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}
