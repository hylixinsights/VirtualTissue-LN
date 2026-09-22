# Recorded Jev plasmablast output — 22 September 2026

**LN-0030 completed plasmablast differentiation and secreted one arbitrary IgM
unit at 12 modeled hours.** The runner stopped after applying that decision, at
the end of the 12 h 10 min physical tick. The recorded model is `jev-1.13.0`.

This is a **guided, uncalibrated demonstration**. It uses real Jev responses with
an explicitly selected high conditional plasmablast/secretion preference. It is
not an estimate of biological fate frequencies. No biological eligibility gate,
contact distance, antigen inventory, lineage rule or process duration was changed.

## Both attempts count toward the same allowance

| Attempt | API requests | Individual decisions | Input tokens | Output tokens | Outcome |
|---|---:|---:|---:|---:|---|
| Original local model-semantics policy (v3) | 173 | 300 | 511,718 | 10,854 | GC response, three divisions, eight failed-selection deaths; no IgM |
| Proposed conditional plasmablast preference (v5), fresh seed-21 episode | 30 | 49 | 82,600 | 1,775 | One plasmablast secreted IgM |
| **Total** | **203 / 50,000** | **349** | **594,318** | **12,629** | Automatically stopped on secretion |

Every attempt has reported usage; unknown usage is zero. All 203 responses were
validated. The first episode was stopped after its antigen had fully degraded
and no active B-cell response remained. Its biological data and negative outcome
are preserved. The second episode received only the remaining 49,827-request
allowance. There were no transport retries or fixture substitutions.

## Observed causal chain in the successful episode

| Modeled time | Recorded event |
|---|---|
| 0 h | DC LN-0121 enters with nine finite antigen packets |
| 2 h | Incoming DC finishes peptide–HLA loading |
| 4–5 h | CD4 LN-0095 completes compatible priming contact with that DC |
| 5 h 20 min | B cell LN-0030 captures native packet AG-00002 from the incoming DC |
| 7 h | LN-0095 completes the border-helper differentiation program |
| 7 h 50 min | LN-0030 completes its own peptide–HLA loading |
| 8–8 h 30 min | LN-0030 receives linked help from LN-0095; the helper becomes Tfh upon completion |
| 9 h | Jev selects legal PLASMA commitment for LN-0030, preference 0.78 |
| 12 h | Its 180-minute differentiation program completes |
| 12 h | Jev selects SECRETE, preference 0.86; the kernel records IgM output |

The final tissue contains 121 living cells, including one Tfh and one
plasmablast. **112 cells were never queried.** All nine antigen packets remain
accounted for. LN-0030 retains its clone, native specificity E1 and IgM isotype.

The v5 prompt adds a proposed preference only to an individual B-cell question
that already offers PLASMA or SECRETE. It suggests a strong preference of 0.90;
Jev supplies its own returned distribution and selected action. The resulting
0.78 and 0.86 preferences were not overwritten. Other cells receive no local
fate instruction. The kernel still owns every state transition and timed event.
Only the computational duration ceiling was extended to accommodate the request
budget; the default interactive experiment remains 30 modeled hours.

## Inspect the result without inference

The local read-only result is served at http://127.0.0.1:8018/. LN-0030 is selected
automatically when the page opens. Its actual Jev receipt and animated artwork
remain inspectable. Viewing or downloading does not call Jev.

To reopen it from this project:

```sh
python scripts/run_reactive_jev.py --view --port 8018 --output recordings/private/reactive-jev-igm-guided
```

Both private folders contain `summary.json`, `live.json`, `audit.jsonl`, and
`episode.ln.json.gz`:

- `recordings/private/reactive-jev-igm-50000`: preserved negative attempt.
- `recordings/private/reactive-jev-igm-guided`: successful guided episode.

The successful audit was checked against all 30 exact request hashes and model
responses; all 49 applied/considered individual choices have Jev provenance.
The key is excluded from recordings and the saved viewer loads no credentials.

## Bounded runner

`scripts/run_reactive_jev.py` requires an explicit request cap for a new paid run.
`--prior-requests` subtracts already attempted calls from that cap;
`--plasmablast-preference` explicitly enables v5. Without it, the runner uses v3.
Opening an existing folder for a new run is rejected. A failure is recorded and
stops the episode without retry. The runner also stops when antigen is exhausted
with no remaining active B response, or after sustained complete quiescence.

Synthetic tests cover actual secretion receipts, combined budgets, empty steps,
conditional prompts, transport failures, graceful stopping, terminal antigen
exhaustion and the provider-free saved viewer. The full suite passed 72 tests.
