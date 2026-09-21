# Verification · 21 September 2026

**Automated checks use fixtures; the separately authorized real Jev recording is documented in `LIVE_RUN.md`.** Both kinds of evidence are kept distinct.

## Automated kernel and provider checks

45 unit/contract tests passed on Python 3.9. They cover the exact 300-cell initial population, one-layer geometry and collision separation; seed reproducibility; local observations without neighboring private clonotypes; peptide/HLA mismatch; costimulation; linked help; GC prerequisite/support/delay; expired founder handling; finite and timed antigen processing; single-winner antigen ownership; rejection before partial biological mutation; finite probabilities; two-daughter accounting and ancestry; crowding; absorbing apoptosis; noncycling mature plasma cells; nonsecretory memory; complete recording prefixes; individual Jev question construction; response validation; explicit request caps; unknown usage on timeout; no secret in status/audit; and disabled live inference by default.

## Complete fixture episodes

Five scenarios were tested for 90 rounds (45 proposed simulated hours), seed 21. The detailed output is in `episode-verification.json`.

| Scenario | Live cells at 45 h | GC formed during run | Memory B | Plasma / plasmablast |
|---|---:|---|---:|---:|
| Antigen + adjuvant | 301 | Yes | 1 | 1 |
| Quiet baseline | 300 | No | 0 | 0 |
| CD40–CD40L blocked | 300 | No | 0 | 0 |
| Peptide–HLA mismatch | 300 | No | 0 | 0 |
| FDC retention blocked | 300 | No | 0 | 2 |

The example GC forms at 1,110 simulated minutes (18.5 h) under these deliberately proposed clocks; this is **not** a claim about human GC timing. One B-cell division accounts for the increase from 300 to 301 cells at 45 h. The fixture produces both memory and plasma output and positive antibody secretion. These observations verify reachable code paths, not biological calibration or the quality of Jev decisions.

## Browser and access boundaries

Real headless Chrome with WebGL rendered the tissue with no JavaScript or initial console errors. Desktop (1512 × 982) and narrow (390 × 844) layouts were inspected; the narrow layout has no horizontal overflow. Tested controls include a simulation step, 3D/top camera, zone display, cell filtering, model notes, compressed recording import, frame seeking into an active GC, cell inspection and return to the live tissue.

The local server returned 404 for `.env` and Python source, and 403 for a mutation without its session token. Only public web assets are served. Original Gut repository status was unchanged: no tracked diff and the same pre-existing untracked diagnostic images/reports.

Screenshots: `studio.png`, `germinal-center.png`, `mobile.png`.

## Remaining scientific and operational limits

No human calibration, sequence-level SHM, CSR, cytokine fields, cellular influx/efflux or broader optional immune modules have been validated or claimed. Toy affinity annotations do not determine uptake. Real Jev decisions and reported token usage are audited separately. No biological incremental value over the fixture has been established. The in-memory run must be exported before shutting down the server. The first version uses one local shared simulation per server process.


## Compact 100-cell preset

Tests cover exact composition, separation at three seeds, density scaling, finite antigen input, accounting and allowed population sizes. Five 90-round compact fixture episodes passed (see `population-100-verification.json`). The vaccine fixture ended with 103 live cells, 8 GC B cells and 2 plasma/plasmablast cells; negative controls showed no GC. These are fixtures, not real Jev outcomes.

Provider tests also cover bounded probability rounding, explicit resume with exact state reconstruction, paid-response reuse, lossless local observation tables and legacy prompt cache compatibility. All 45 tests passed. Desktop/mobile preset switching, physical diameter, one-round advancement and scaled antigen pulse were verified. The full browser test additionally passed compressed replay, cell inspection and access boundaries.


## Extended demonstration verification

The suite now contains 47 passing synthetic tests, including authorized extension of a completed run without paying for its prefix again and rejection of a decreasing cumulative cap. `demo-verification.json` independently reconstructs the 64-hour demonstration and verifies its unchanged 60-hour prefix, daughter ancestry, antigen conservation and cumulative usage across comparison branches. The real example contains one physical division and three memory B cells under the explicitly proposed v4 fate rubric; this does not establish calibrated biological validity.
