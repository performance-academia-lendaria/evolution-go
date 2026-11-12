# Local media and continuous traffic verification

Status: **pass**

- Run: `7c526e36`; label: `after`.
- Image: `sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd`.
- Started: 2026-11-11T22:13:50.621044Z.
- Requested duration: 0 seconds; interval: 300 seconds.
- Only synthetic content, between two exclusive test accounts; no forced outages.
- PNG solid color; WAV 1-second tone sent through normal local audio conversion.
- Delivery requires matching hashed ID, incoming Message and correct media kind.
- Authentication sampled every 2 seconds between batches and before each send.

| Batch | Text delivered | Image delivered | Audio delivered |
|---|---|---|---|
| 1 | 2/2 | 2/2 | 2/2 |

- finished_utc: "2026-11-11T22:13:56.943010Z"

- elapsed_seconds: 6.322

- authentication_samples: 7

- target_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}

- sender_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}
