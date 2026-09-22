# Scripted vaccination story

The English player at `/web/vaccine-demo.html` visualizes a complete, deliberately
favorable DC–CD4–B pathway in the existing 100-cell LN. It runs for 76 seconds,
representing 600 proposed model minutes, and stops with one plasmablast and
three arbitrary IgM secretion units. It is a local visual demonstration, not
an unbiased estimate of fate probabilities or vaccine efficacy.

## Biological execution

`scripts/build_vaccine_story.py` initializes the existing seed-21 patch without
antigen, then introduces a local two-packet protein/adjuvant challenge. The
selected cells already occupy neighboring sites: DC LN-0018, CD4 LN-0083 and
B LN-0054. Their centers, receptors and identities are unchanged. Two independent
native packets of the same antigen are initially within capture range of the DC
and B cell; this favorable placement is an explicit proposed initial condition.

Every living, non-busy cell receives a legal decision in all 20 full rounds.
Nonparticipants choose WAIT. The DC captures and processes antigen. CD4 chooses
PRIME only when compatible DC pMHC, costimulation and physical proximity permit
it, then enters HELPER. The B cell independently captures and processes native
antigen, obtains local linked HELP, and chooses PLASMA only after its help license
exists. The existing 180-minute differentiation clock completes before SECRETE.
The B cell retains its identity, clone, specificity and IgM isotype. No germinal
center, class switching, cell division or mature plasma state is forced.

The distinction between initial DC priming and subsequent B-cell interaction
is supported by [Goenka et al., 2011](https://pubmed.ncbi.nlm.nih.gov/21715693/).
The precise times and the simplified helper states remain proposed kernel
assumptions, not measured rates from that paper.

The trace records 1,986 scripted choices, with zero inference requests.
All choices use the existing eligibility menus and action handlers. The kernel,
its default policies and its model contract are unchanged. Full cell snapshots
and the two-packet antigen ledger are captured per frame in `web/vaccine-story.json`.
The ordinary episode, full decision receipts and events are included for audit.

## Visual interpretation

The close-up uses the actual recorded cell positions and highlights the same
three agents. Whole tissue shows all 100 cells. Presentation markers appear
only while a cell has pMHC. Contact connectors are derived from recorded PRIME
and HELP start/deadline events and require permitted physical distance.
Antigen ownership and processing stages come from the saved finite ledger.

The short arrival trail is schematic between the supplied local input positions
and the surrounding tissue. Membrane pose changes, transition crossfades,
presentation markers and IgM pentamer icons are illustrations, not extra
biological events. The green plasmablast sheet was copied unchanged from the
user's supplied LN assets. Multiple antibody icons depict an arbitrary output
unit; they do not count individual molecules. Pausing freezes the visual clock.
Reduced-motion preferences disable autoplay; an explicit Play remains available.

## Relationship to Jev

The generator imports only the existing kernel, not Jev or server credentials.
The browser reads local static files and has no inference endpoint. No Jev
probabilities or prompts were changed. A future separately authorized policy
may favor eligible actions along this route, but must still obey antigen,
recognition, contact, help and timing gates. The displayed scripted route must
not be relabeled as a Jev result or a measured transition probability.

## Verification

Unit tests check identity, antigen conservation, ordered events and clocks,
complete rounds, legal menus, reproducibility, and loss of plasmablast/antibody
output when CD40 help or HLA matching is disabled. Browser checks cover actual
autoplay and completion, pause, restart, seeking all eight stages, cell
selection, whole-tissue mode, reduced motion, English text, narrow layouts and
absence of API or external requests. Screenshots are in `docs/vaccine-review/`.
