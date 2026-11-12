# Local media and continuous traffic verification

Status: **pass**

- Run: `f21d35c7`; label: `after`.
- Image: `sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd`.
- Started: 2026-11-12T01:57:29.700508Z.
- Requested duration: 30 seconds; interval: 300 seconds.
- Controlled preflight: one induced target outage, excluded from natural-drop rates.
- PNG solid color; WAV 1-second tone sent through normal local audio conversion.
- Delivery requires matching hashed ID, incoming Message and correct media kind.
- Authentication sampled every 2 seconds between batches and before each send.

| Batch | Text delivered | Image delivered | Audio delivered |
|---|---|---|---|
| 1 | 2/2 | 2/2 | 2/2 |

- recovery_seconds: 60

- drop_counts: {"target": 1, "sender": 0}

- recovered_drops: 1

- drops: [{"role": "target", "disconnected_epoch": 1794448655.9468894, "origin": "Disconnected", "recovered": true, "probe": {"kind": "text", "request_utc": "2026-11-12T01:57:39.384934Z", "accepted_utc": "2026-11-12T01:57:39.878639Z", "message_id_sha256": "2e00fac085036ac0e0638fb6a71977591cd750d3f051a05a15fb677959da0e6c", "destination_sha256": "a02a2694ed5ebcf4d57273e1cf6fbce2efb5756998176ea2eff76b68763e9ffe", "delivered": true}, "connected_epoch": 1794448659.1411076, "sync_completed_epoch": 1794448659.181871, "recovered_epoch": 1794448659.8895752, "recovery_seconds": 3.943}]

- interrupted_send_attempts: 0

- last_health_utc: "2026-11-12T01:58:01.586924Z"

- drops_per_hour: {"target": 112.899, "sender": 0.0}

- finished_utc: "2026-11-12T01:58:01.587351Z"

- elapsed_seconds: 31.887

- authentication_samples: 30

- target_logs: {"connected": 1, "offline_preview": 1, "offline_completed": 1, "automatic_restart": 1, "process_handler_panics": 0, "process_stream_errors": 0}

- sender_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}
