# Local media and continuous traffic verification

Status: **pass**

- Run: `19d178f4`; label: `before`.
- Image: `sha256:30cfa84be63f28f17a9e7e78e49a323fc59d33a68a029cab5dea4c1577321c0e`.
- Started: 2026-11-11T20:32:18.229864Z.
- Requested duration: 0 seconds; interval: 300 seconds.
- Only synthetic content, between two exclusive test accounts; no forced outages.
- PNG solid color; WAV 1-second tone sent through normal local audio conversion.
- Delivery requires matching hashed ID, incoming Message and correct media kind.
- Authentication sampled every 2 seconds between batches and before each send.

| Batch | Text delivered | Image delivered | Audio delivered |
|---|---|---|---|
| 1 | 2/2 | 2/2 | 2/2 |

- finished_utc: "2026-11-11T20:32:26.588448Z"

- elapsed_seconds: 8.359

- authentication_samples: 7

- target_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}

- sender_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}
