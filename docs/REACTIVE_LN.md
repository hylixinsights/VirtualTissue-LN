# Live LN with local responses

The default local launcher serves `web/reactive.html` through `ReactiveStudio` and
`ReactiveSimulation`. The earlier `Simulation`, recorded Jev episodes and scripted
vaccine movie are preserved as explicitly separate legacy tools.

## What changed

The architectural reference was inspected at
[Gut commit cfc795b](https://github.com/hylixinsights/VirtualTissue/tree/cfc795b67eef27d93a835b75131c004f792a6958),
including `src/activation.mjs`, `src/unified-host.mjs`, `src/renderer.mjs` and its
public IBD replay. The useful mechanics are local activation reasons, eligibility
checks, a decision interval, autonomous process clocks, and inspectable individual
choices. No Gut code, runtime imports, configuration or credentials were reused.

The LN starts with 100–149 residents (120 by default). One antigen-bearing DC can
enter at a collision-free afferent boundary site, adding exactly one individual.
The overall safety limit is 150 living cells. Cell centers remain at z=0; a shaded
monolayer is displayed with depth and the supplied animated cell illustrations.
The quiet population does not move or receive fabricated WAIT decisions.

The supported prompt is **“An antigen-bearing dendritic cell enters the lymph
node.”** A small declared parser recognizes that input, rather than pretending to
understand unrestricted biological prose. Fate instructions are rejected. The
prompt is an experimental input and is not passed to individual Jev questions.
The added DC has one native processing packet and eight additional finite native
packets. It can process antigen into pMHC-II; cognate B cells can acquire native
material at physical DC contact. The latter is a proposed coarse compartment
abstraction motivated by [Qi et al., Science (2006)](https://pubmed.ncbi.nlm.nih.gov/16778060/),
not a quantitative model of antigen recycling or measured human kinetics.

## Local decision contract

A cell needs a local cause, at least one executable non-WAIT action, no active
program, and an elapsed decision interval before it is queried. Causes include
own antigen, an acquired cellular program, nearby cognate native antigen,
compatible presentation/helper contact, or nearby apoptotic debris. There is no
global instruction to respond, make antibodies, or build a GC.

Only local observations and prevalidated menus are given to a provider. Every
answer is checked before mutation. Seeded arbitration reserves acting cells and
shared targets; competing actions can be deferred. In particular, migration
cannot silently overwrite a contact started earlier in the same batch.

MOVE starts a timed motility program. Collision-checked motion advances on every
physical tick, without another provider question. Processing, peptide loading,
priming, helper differentiation, linked help and plasmablast commitment likewise
take time. Pausing the UI stops physical ticks; pose animation alone changes no
biology. Amber rings show current local sensing, not a historical decision or
invented secreted cytokine.

Native antigen recognition by a BCR remains distinct from peptide–HLA recognition
by a CD4 TCR. Priming needs costimulation and a maintained compatible DC contact.
Antibody-producing differentiation needs a finite linked-help license. IgM output
retains the B-cell clone and isotype. The visible antibody glyphs represent saved
arbitrary output units, not individual molecules or a measured concentration.

The preview policy chooses among legal options using declared priorities and a
clone-ID-based fate split. It contains no preselected protagonist cells or timed
story steps. It is deterministic and labeled **Local policy preview**, not Jev,
and is not an estimate of biological fate probabilities. Jev can replace this
policy through the same scheduler; no new real inference was run for this change.

## Proposed numerical choices

All numbers are **P: proposed and uncalibrated**. Authoritative values are in the
exported contract, `REACTIVE_RULES`, and the inherited kernel parameters.

| Quantity | Current value |
|---|---:|
| Default resident cells / after entry | 120 / 121 |
| Maximum living cells | 150 |
| Radius at 120 residents | 135 μm |
| Initial site spacing / cell radius | 20 μm / 4.2 μm |
| Physical tick | 10 min |
| Minimum interval between decisions by one cell | 60 min |
| Motility program / speed | 60 min / 0.3 μm per min |
| Native-antigen sensing radius | 28 μm |
| Presentation/helper sensing radius | 36 μm |
| Required physical contact | ≤15 μm |
| Initial DC entry program | 30 min |
| Antigen input | 9 conserved unit-mass packets |
| pMHC lifetime | 720 min |
| Default experiment duration | 1,800 min (180 physical ticks) |

Other process durations, finite help licenses, lineage and antigen accounting
come from the preserved kernel. Stromal support is constitutive maintenance;
stromal agents do not need artificial repeated MAINTAIN decisions. Two qualified
founders must be within 36 μm of the same supporting FDC, followed by the 120-min
organization interval, before a GC event can be recorded. The GC marker uses that
actual supporting cell location. A prompt cannot create it. A particular run may
produce plasmablasts or founders without completing GC organization.

## Jev and verification

The default Jev launchers now use the [continuous recorder](CONTINUOUS_RECORDING.md)
with a user-selected per-run call budget and no ten-decision ceiling. The earlier
ten-decision behavior below remains available with `--preview`.

The subsequent [real Jev IgM demonstration](REACTIVE_JEV_IGM.md) used 203 API
requests across two attempts. A declared conditional plasmablast preference was
selected for the successful second episode; the original policy produced a GC
response without IgM. Both outcomes and their full provenance are preserved.

`Start Jev.cmd` and `Start Jev.command` require an explicit HTTP request cap and
use a default cap of ten individual decisions. A whole local batch that would
exceed the remaining individual allowance is blocked before a request. Empty
steps do not call Jev. Failures pause time, retain honest usage and never fall back
to fixtures. Credentials remain in this project's server process/local ignored
environment file. Resetting an experiment cannot reset the server request limit.

`tests/test_reactive.py` checks quiet baseline, entry and conservation, sparse
causal decisions, physical contacts, cooldowns, no-help/HLA controls, atomic
validation, and provider boundaries. `tests/browser_reactive.mjs` exercises the
live server and real UI: prompt rejection, entry, automatic time progression,
movement, actual plasmablast output, pause, inspection, mobile layout, reduced
motion, zero external requests and zero paid calls. Reviewed screenshots and
observed metrics are in `docs/reactive-review/`.

## Scope

This remains an uncalibrated patch, not a complete lymph node. Existing B/T
territories are a stromal scaffold; de novo formation of an entire T-cell zone is
not implemented. Cytokine secretion/diffusion, HEV entry, egress, Tfr/Treg control,
CSR and sequence-based affinity maturation remain outside this version. Native
antigen availability around the DC is a sensing prior, not a calibrated chemokine
field. Quantitative population composition and contact lifetimes require future
calibration. Export saves the input, kernel contract, decisions, clocks, finite
antigen ledger and lineage for audit; the legacy public replay is unchanged.

## Observed browser run

Seed 21, 120 residents plus one arriving DC, inspected at 24 biological hours:
121 living cells, 112 never queried, 124 local policy decisions, three Tfh cells,
two plasmablasts and 16 arbitrary IgM output units. Two cells were GC founders;
this readout does not establish that a germinal center had formed. All nine
antigen packets remained accounted for. The browser made zero external requests
and zero paid requests, with no script errors or mobile overflow. These are
observations of the declared deterministic preview, not biological predictions.
