# Recorded demonstration: division and memory with Jev

[▶ Open the 3D demonstration](http://127.0.0.1:8010/?recording=231bd6719cad444a8d0d)

Use **Play recording** to follow the full trajectory, or **GC formed**, **Memory B** and **First division** to jump to key events. Playback makes no API calls.

## Observed outcome

The example starts with 100 individual cells in a monolayer disk and ends at **64 simulated hours**, after **12,284 actual Jev decisions**. Returned model: `jev-1.13.0`.

| Event | Simulated time | Evidence |
|---|---:|---|
| GC formation | 22.5 h | Biological kernel event |
| Three memory B cells | 63 h | LN-0029, LN-0054 and LN-0062 completed MEMORY |
| One physical division | 64 h | LN-0058 was replaced by LN-0101 and LN-0102, retaining the clone |

The memory cells belong to other clones and appeared before this division. **They are not presented as descendants of the two recorded daughters.** This example produced no plasma cells or antibodies.

Final state: **99 living cells = 100 initial + 1 net gain from division − 2 deaths**; 13 GC B cells, 7 Tfh and 3 memory B cells. One division replaces a parent with two daughters, adding one cell to the population. All 160 antigen packets remain accounted for, including degraded packets.

## How the example was obtained

The original 44.5-hour recording was preserved. Continuing it to 60 hours with the same decision context produced neither division nor memory. A first context revision explained cell states and finite licenses to Jev. That comparison reached four divisions but no memory or plasma output, and was preserved through 86.5 hours.

The final demonstration starts from the same **60-hour checkpoint**. From that point, context v4 states a **qualitative demonstration hypothesis**: local scarcity of cognate antigen can favor memory preservation over another antigen-dependent selection cycle. Accessible antigen and renewed help allow consideration of recycling or secretion. This changes the policy sent to Jev; it is neither a measured rate nor a spontaneous outcome under the previous context.

All applied choices were returned by Jev, including MEMORY and DIVIDE. No synthetic decisions were substituted, no fates were sampled by code, no memory cells were created manually, and no probabilities were adjusted to force a choice. Eligibility, geometry, clocks, division budgets and antigen inventory remained unchanged. No additional antigen pulse was applied.

The run stopped after satisfying the declared criterion of **physical division and memory or mature plasma output**. It is therefore a selected demonstration with a documented context revision, not an unbiased estimate of cell-fate frequencies. Parameters remain proposed and uncalibrated for a human lymph node.

## Usage across all attempts

- 911 cumulative HTTP attempts, including the original example and the comparison without memory.
- 25,859,657 input tokens and 596,008 output tokens reported by the service.
- **US$1.086105594 estimated known cost**, approximately **US$1.09**. The increase from the previous US$0.597968994 was approximately **US$0.49**.
- One earlier HTTP 400 attempt reported no usage. Reserving a conservative maximum context of 65,536 tokens for it adds a US$0.002752512 allowance.
- The global cap of 1,800 attempts was conservatively bounded at US$4.9545216 by the same calculation, below the US$5 authorization for that historical run. No new purchase or recharge change was made.

The calculation uses US$0.042 per million input tokens, free output and a 64k maximum context, checked in the [official Jev documentation](https://docs.typesafe.ai/models) on 21 September 2026. The final account balance was not queried. These historical allowances do not authorize new inference runs.

## Verification and files

The audit replayed all 128 rounds exactly, confirmed that the segment before 60 hours matches the checkpoint, and verified individual-decision coverage, daughter ancestry, antigen conservation and token sums. The 47 synthetic tests available at that review passed. Browser playback checks milestones, counters, policy disclosure and absence of new inference calls.

- Demonstration: `recordings/private/jev-fate-demo-20260921/vaccine.ln.json.gz`.
- Preserved comparison: `recordings/private/jev-extended-demo-20260921/`.
- Preserved original: `recordings/private/jev-20260921-103901-2321f0/`.
- Final audit: `docs/demo-verification.json`.
- Proposed context: `docs/jev-fate-context.json`; full descriptions and version in `jev.py`.

The demonstration's request history includes comparison costs, marked as attempts not applied to this trajectory. The summary and decision file distinguish this provenance. Do not add cumulative totals across directories again: they share the same initial segment.
