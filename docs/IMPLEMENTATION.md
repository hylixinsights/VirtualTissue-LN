# Implemented biological contract

The attached manual is a biological reference, not an operational instruction to an AI assistant. Its general catalogue exceeds the implemented scope. Numerical choices below are all **P — proposed implementation**, not measured human constants. Original reference IDs and evidence labels remain in the unchanged manual.

## Physical model

A disk of diameter 300 μm (300 cells) or 173.2 μm (100 cells) contains cell centers at z = 0, initially on separated hexagonal sites. Each cell is a single individual, radius 4.2 μm. Position updates are at most 9 μm per 30-minute decision step and check four intermediate path positions as well as the endpoint. Capsule containment, occupied corpses, stromal bodies and daughter placement constrain motion. Decorative dendrites are not collision volumes. This is a single-cell-thick representative patch rendered in 3D, not volumetric whole-node anatomy.

Follicular, paracortical and medullary territories are soft visualization regions with proposed static positioning fields. Cells only receive the local field value/gradient. The GC overlay is hidden until a real engine event establishes it. The displayed DZ/LZ neighborhoods are migration biases, not lineage-changing boxes. Chemokine diffusion, anatomy of vessels, entry through HEVs and egress have not been implemented. The endothelial population is structural in this version.

## Native antigen to T-dependent output

The demonstration injects 480 unit-mass antigen packets for 300 cells, or 160 for 100 cells, through a small afferent boundary. Further UI pulses add 80 or 27 packets, respectively. The compact preset scales territory positions and radius by sqrt(100/300); individual cell size, sensing ranges and biological clocks remain unchanged. A packet represents arbitrary mass-equivalent material, not one protein molecule. The demonstration explicitly assumes protein plus adjuvant and pre-opsonized immune complexes; it does not model how the upstream complexes were made. Capture does not imply vaccine replication.

The six tracked accessible/processed pools are free native antigen, native cell cargo, FDC-retained complexes, internalized protein, processed peptide, and surface pMHC-II. Degradation is a separate absorbing accounting pool. Packet identity, peptide, HLA, native epitope and source survive transfers. Capture has one winner and FDCs have eight retention slots. Antigen transport is a specified biased random walk; probabilities are independent of Jev.

A BCR recognizes E1 or E2; a helper TCR recognizes P1 in HLA-II-A. These are illustrative labels, not patient HLA genotypes or real sequence predictions. Cognate B cells are deliberately enriched (68% initialization probability). Processing takes 60 minutes, loading 30, and surface pMHC persists for 360. DC costimulation is enabled by capture in the specified adjuvanted context. Priming requires a local compatible DC display, costimulation and a 60-minute contact; the next helper program takes 120 minutes. Simulated cytokine programs are not inferred from marker expression.

Linked B–T help requires an actual compatible surface peptide/HLA pair and an available helper within 15 μm. A 30-minute reserved contact grants a 1,440-minute finite license. The same helper cannot be allocated twice in a decision round. FDC-supported founder commitment takes 240 minutes. Two qualified founders and a further 120-minute organization delay establish the GC. Expired pre-GC founders return to the activated B state; they cannot enter selection or memory by bypassing GC membership.

A GC division takes 240 minutes and spends a finite license. A parent is replaced by exactly two daughters, each with zero inherited division allowance and its own identity, but the same clone. Native/processed antigen is degraded once on division rather than duplicated. An explicit toy variant record changes the affinity annotation by −0.15, 0 or +0.10, clamped to [0.01, 1]. **This annotation is not a sequence-based SHM model and currently does not control uptake probability.** Recognition is the explicit epitope match; local antigen and helper competition drive eligibility. No claim of simulated quantitative affinity maturation is made.

GC daughters enter the selection program with a 1,440-minute proposed failure deadline. New local capture, processing and linked help permit selected cells to choose recycling, memory or plasma output. Death commitment cancels pending programs. Macrophages require a local corpse and a free finite clearance queue; uptake and death are separate events. There is no generic killing action.

Plasmablast, memory and plasma commitment clocks take 180 minutes. Antibody output is one arbitrary secretion unit per SECRETE choice, retaining the clone and existing IgM identity. Memory cells cannot secrete by default. Plasma cells cannot cycle. CSR, immunoglobulin sequence changes and marrow longevity are not modeled.

## Decision and execution contract

`engine.py` is authoritative for population, geometry, permitted actions, clocks and handlers. `jev.py` can return bounded preferences; it cannot define state transitions. `server.py` owns the simulation state; the browser only requests a step, reset or antigen pulse. Numerical configuration is included in every exported contract and fingerprint.

Each round derives all menus and observations before applying any proposal. Seeded arbitration reserves shared cells/antigen and logs deferrals. Later cells cannot obtain a newly enabled biological action from an earlier cell's result. Movement uses current occupied geometry for collision safety after arbitration, preventing two accepted moves into the same space. Invalid decisions reject the complete round before mutation. Mandatory clocks then advance once; the renderer never advances biology or consumes the biological RNG.

All living non-busy cells receive their own decision, including stroma. MAINTAIN renews a stromal support state; static positioning fields remain an explicit scaffold assumption. Program-busy cells execute clocks rather than making redundant choices. Dead cells receive no decisions. Full proposals and conflict receipts are retained, including waits.

Network or schema failure pauses biological time and retains all completed request accounting. No failed response is converted to a fixture. This is a declared pause-on-failure policy, rather than the manual's optional approach of continuing mandatory clocks during service failure.

## Scope map

| Manual rule family | Implemented here | Boundary |
|---|---|---|
| LN-R001, 003–009 | Lineage, collision-limited motion, antigen provenance, processing and cognate priming | No measured motility or HLA binding model |
| LN-R011–016 | Linked help, extrafollicular output, timed GC founding, finite cycling, local competition | Small patch, proposed founder threshold and clocks |
| LN-R017–018 | Clone/parent/variant history preserved | CSR and sequence SHM absent; affinity annotation only |
| LN-R019–025 | Competing outputs, terminal plasma state, two-daughter accounting, crowding, failed-selection death and clearance | No calibrated death hazards or contraction model |
| LN-R026 | Antibody secretion and local stromal maintenance | Cytokine diffusion/production omitted |
| LN-R002, 028–029 | Explicit afferent antigen input, no replication | No cellular recruitment, egress or live-vaccine model |
| LN-R027 | Not implemented | No Treg/Tfr regulation |
| LN-R030 | Decision, rejection, event, ancestry and provider audit trails | Not a validation certificate |

The manual's broader CD8, pDC, neutrophil, NK, macrophage subtype, class-switching, cytokine, tolerance, regulatory and vaccination-platform modules remain unimplemented. Unlisted actions have no handlers and cannot be selected through Jev.
