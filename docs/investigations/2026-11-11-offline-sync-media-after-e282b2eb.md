# Local media and continuous traffic verification

Status: **stopped**

- Run: `e282b2eb`; label: `after`.
- Image: `sha256:4dc949670b264032b9a7aad44c2c1233fdcc75ebfc83391cf3d47cd4603322dd`.
- Started: 2026-11-11T22:15:21.142212Z.
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

- finished_utc: "2026-11-11T22:56:30.022120Z"

- elapsed_seconds: 2468.498

- authentication_samples: 1258

- stop_reason: "STOP: authentication lost; preserve sessions and ask Tuan before recovery."
