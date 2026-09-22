# Continuous LN recording: 5,000 actual Jev calls

Recorded on 22 September 2026 with `jev-1.13.0`, seed 21, 120 resident cells and one incoming antigen-bearing dendritic cell. The run stopped at the exact 5,000-request ceiling; all 5,000 responses were validated and applied. Playback requires no key and sends no inference requests.

## Observed result

- One germinal center formed and later resolved.
- One physical B-cell division produced two daughters: LN-0030 -> LN-0122 and LN-0123. Four other division attempts were blocked by crowding.
- A separate B-cell lineage, LN-0080, became a plasmablast, secreted IgM, and matured into a plasma cell.
- Total IgM output: **4,922 arbitrary model units**. No class switching is modeled.
- Three GC cells underwent apoptosis after failed selection. No memory B cell appeared.
- Living population: 121 after DC entry, a peak of 122, and 119 at the endpoint. Of the final living cells, 116 were never queried; only five distinct cells were queried during the entire run.
- All nine antigen packets are accounted for and ultimately degraded.

## Recorded milestones

| Event | Modeled time |
| --- | ---: |
| DC entry | 0.00 h |
| Border helper | 7.00 h |
| Linked help completed; helper becomes Tfh | 18.83 h |
| GC | 29.17 h |
| Plasmablast | 29.50 h |
| First IgM | 29.50 h |
| Division | 33.17 h |
| Plasma cell | 35.50 h |
| First failed GC selection | 57.17 h |
| GC resolution | 69.33 h |

## Interpretation and policy

This is an **uncalibrated visual demonstration**. The declared v6 policy uses a proposed local affinity-annotation threshold of 0.79 to favor competing early-output and GC routes. The threshold and returned action preferences are not measured biological fate probabilities. Every applied decision is a real Jev response; physical eligibility, contact, finite antigen, ancestry and timed programs are enforced by the kernel.

The initial response highlights cover 72.33 modeled hours. Continuing to the requested call allowance extends the full record to **4,953.67 modeled hours** (about 206 days). Most later requests select sustained secretion by the same plasma cell. Plasma-cell lifespan and antibody decay are not modeled, so this late phase is not a prediction of vaccine protection or antibody persistence.

## Audit and recovery

A Windows checkpoint-file replacement was denied after 3,406 calls. Every response and the completed state had been saved. An explicit continuation reconstructed all 20,163 completed biological steps and verified exact state, observations, decisions, events and random-state continuity before any new request. The remaining 1,594 calls stayed within the original 5,000-call total. No previous paid request was repeated and no fixture response was substituted. The interruption and continuation remain in the record.

The public episode translates that operating-system diagnostic into English; all biological data and provider receipts are unchanged. Its publication metadata identifies the original private checkpoint by hash.

The completed record contains **29,724 visual frames**, **5,000 decisions**, **10,393,684 input tokens**, **199,808 output tokens**, and **zero unknown-usage requests**. All request hashes, returned choices, visual population accounting and daughter lineages passed the [complete audit](continuous-recording-review.json).

Validation: 80 synthetic automated tests, five control scenarios, and browser checks for local simulation, replay, cell inspection, seeking, mobile layout and absence of inference calls during playback. The MP4 capture is separately documented in [video metadata](recording-review/video-capture.json).

## Open or reproduce

Build the default static player with `python scripts/build_site.py`, then serve `site/` using `python -m http.server 8020 --bind 127.0.0.1 --directory site`. Open `http://127.0.0.1:8020/`.

To make a new experiment, open `Start Jev.cmd` or `Start Jev.command`, enter your own hidden key, and choose the per-run call cap. New Jev outcomes can differ. See [the recording and video guide](CONTINUOUS_RECORDING.md).
