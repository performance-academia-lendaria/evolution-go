# Local media and continuous traffic verification

Status: **pass**

- Run: `4a5f41a2`; label: `after`.
- Image: `sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd`.
- Harness commit: `098d8bd1df6a07db5814927948d5df95042e408a`.
- Started: 2026-11-12T02:03:17.453394Z.
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

- drops: [{"role": "target", "disconnected_epoch": 1794449003.242181, "origin": "Disconnected_log", "recovered": true, "probe": {"kind": "text", "request_utc": "2026-11-12T02:03:27.319248Z", "accepted_utc": "2026-11-12T02:03:27.808901Z", "message_id_sha256": "36e28d27d0d34f1521fcd27341f6864e96ea47005a86f6cab59cb9f1762ed04a", "destination_sha256": "a02a2694ed5ebcf4d57273e1cf6fbce2efb5756998176ea2eff76b68763e9ffe", "delivered": true}, "connected_epoch": 1794449006.870618, "sync_completed_epoch": 1794449006.938445, "recovered_epoch": 1794449007.8153658, "recovery_seconds": 4.573}]

- interrupted_send_attempts: 0

- last_health_utc: "2026-11-12T02:03:49.931376Z"

- drops_per_hour: {"target": 110.841, "sender": 0.0}

- finished_utc: "2026-11-12T02:03:49.932447Z"

- elapsed_seconds: 32.479

- authentication_samples: 31

- target_logs: {"connected": 1, "offline_preview": 1, "offline_completed": 1, "automatic_restart": 1, "process_handler_panics": 0, "process_stream_errors": 0}

- sender_logs: {"connected": 0, "offline_preview": 0, "offline_completed": 0, "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}
