# Live-recording review · 21 September 2026

- Supplied key configured in the project-local `.env`, owner-readable only (0600). It is not embedded in JavaScript, source, manifest, recordings or command arguments.
- Authenticated against the documented read-only `GET /v1/models` endpoint. No inference request is needed for this check.
- Rechecked current TypeSafe API and Choice documentation, retaining pinned `jev-1.13.0`.
- Added a bounded real-provider recorder with durable request/round journal, periodic compressed recordings, partial-round observations, complete provider audit and separate per-scenario token/request accounting.
- Added four-request concurrency in bounded waves; no later wave starts after failure and no request is retried automatically. A full round's budget is checked before sending any batch.
- Hardened validation of non-object cell answers.
- Added local recording catalogue and playback labels that distinguish real Jev decisions from fixtures; playback displays the recording's own usage rather than the currently open live session's counters.
- Original 29 tests plus six recorder/concurrency tests passed with synthetic transports. The extra tests cover 300 distinct per-cell answers across parallel batches, preflight budget rejection, failure-wave limits, no fixture invocation on the live path, secret exclusion, partial-file preservation and catalogue access.

No biological kernel or calibrated parameter was changed by this review. Real-provider outcomes must be reported as observed, including no GC formation if that is what the decisions produce. Authentication success is not a paid inference test.

Sources checked: https://docs.typesafe.ai/api ; https://docs.typesafe.ai/primitives/choice ; https://docs.typesafe.ai/models
