# Local media and continuous traffic verification

Status: **pass**

- Run: `5b135557`; label: `after`.
- Image: `sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd`.
- Harness commit: `46fa181fcb5d9fade58d144363bd2581daf5dd54`.
- Started: 2026-11-12T02:15:52.127516Z.
- Requested duration: 0 seconds; interval: 300 seconds.
- Only synthetic content, between two exclusive test accounts; no forced outages.
- PNG solid color; WAV 1-second tone sent through normal local audio conversion.
- Delivery requires matching hashed ID, incoming Message and correct media kind.
- Authentication sampled every 2 seconds between batches and before each send.

| Batch | Text delivered | Image delivered | Audio delivered |
|---|---|---|---|
| 1 | 2/2 | 2/2 | 2/2 |

- recovery_seconds: 60

- drop_counts: {"target": 0, "sender": 0}

- recovered_drops: 0

- drops: []

- interrupted_send_attempts: 0

- last_health_utc: "2026-11-12T02:16:00.090405Z"

- drops_per_hour: {"target": 0.0, "sender": 0.0}

- observed_until_utc: "2026-11-12T02:16:00.046179Z"

- finished_utc: "2026-11-12T02:16:00.159662Z"

- elapsed_seconds: 8.032

- authentication_samples: 16

- target_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}

- sender_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}
