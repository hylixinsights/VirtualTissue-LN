# Actual Jev recording — 100 cells

Run on 21 September 2026, seed 21, protein/adjuvant scenario. Independent of the Gut project. Circular monolayer, 173.2 μm diameter, 3D visualization. Returned model: `jev-1.13.0`.

## Observed outcome

- 89 complete rounds: **44.5 simulated hours** out of a 45-hour target.
- **8,463 actual individual Jev decisions**, with local observations and options recorded.
- Germinal center established at 1,350 minutes (22.5 h), with four founders. Final state: **16 GC B cells**, 6 Tfh and 7 cells displaying pMHC.
- 100 living cells at completion; no division or death. No memory cells, plasma cells or antibody secretion occurred in this run.
- All 160 antigen packets remain accounted for, including degraded packets.

Clocks, proportions and GC criteria are proposed and uncalibrated. This result does not predict the behavior of a human lymph node. Division, memory and plasma routes exist in the code and were reached in synthetic tests, but must not be attributed to this Jev recording.

## Usage and stopping condition

There were **447 HTTP attempts**, under a cap of 450. Another complete round required five calls, so the recording remains honestly marked **partial**. The three remaining calls were not spent on an incomplete round.

The service reported **14,237,357 input tokens** and **294,834 output tokens**. At the US$0.042 per million input tokens and free output shown in the user-supplied price screenshot, estimated known cost was **US$0.597968994**, approximately **US$0.60**. One HTTP 400 request reported no usage; any charge for it is excluded. The current account balance was not queried.

## Protocol reviews

1. Distributions rounded to two decimals: normalization only within the rounding bound, without changing the choice. Ten applied decisions have this adjustment documented and retain their original values.
2. HTTP 400: the original cause was not confirmed because the first version did not preserve the error body. The rejected batch was the largest; lossless local tables reduced its size by 38%. Resuming succeeded, and HTTP error details are now retained.
3. On attempt 369, Jev chose MOVE (0.42) while WAIT had 0.43. The entire response was rejected and preserved in the audit. After explicit review, only that batch was requested again.

There were no automatic retries, synthetic fallback decisions or retroactive decision changes. Already-paid valid responses were reused on resume. Format v1 was used initially; v2 uses lossless tables. This format change is part of the run provenance.

## Open and verify

With the local server running, [open the recording](http://127.0.0.1:8010/?recording=940f891b6407c4a24371), also available under **Saved Jev examples**. Playback and inspection make no paid calls.

File: `recordings/private/jev-20260921-103901-2321f0/vaccine.ln.json.gz`. The same directory contains `summary.json` and the incremental `audit.jsonl` history.

Verification reconstructed all 89 rounds from recorded decisions and obtained an exactly matching final state. It checked coverage of eligible cells, physical invariants, antigen conservation and audit token sums. Results are in `live-verification.json`; the 45 synthetic tests available at that review passed.
