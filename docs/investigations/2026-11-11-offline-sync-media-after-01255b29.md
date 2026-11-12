# Local media and continuous traffic verification

Status: **pass**

- Run: `01255b29`; label: `after`.
- Image: `sha256:4e8d5a8d290166443669c6ec71514140f093f25cdb6105344473b8a288685940`.
- Harness commit: `11bb6e4514e0a40b9b0445941e1164acef29f830`.
- Started: 2026-11-12T07:13:04.489800Z.
- Requested duration: 0 seconds; interval: 300 seconds.
- Only synthetic content, between two exclusive test accounts; no forced outages.
- PNG solid color; WAV 1-second tone sent through normal local audio conversion.
- Delivery requires matching hashed ID, incoming Message and correct media kind.
- Authentication sampled every 2 seconds between batches and before each send.

| Batch | Text delivered | Image delivered | Audio delivered |
|---|---|---|---|
| 1 | 2/2 | 2/2 | 2/2 |

- recovery_seconds: 0

- interrupted_send_attempts: 0

- finished_utc: "2026-11-12T07:13:13.148886Z"

- elapsed_seconds: 8.659

- authentication_samples: 19

- target_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}

- sender_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}
