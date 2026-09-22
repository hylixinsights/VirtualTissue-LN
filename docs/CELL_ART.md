# Cell illustrations in the LN

22 September 2026. Baseline: `1f9dee19ae5f73823af2e44164843d460afaced1`.
Local development on `design/cell-atlas`.

## Watch the vaccination response

Open `/web/vaccine-demo.html` on the local Studio server. The 76-second
scripted playback follows an existing adjacent DC–CD4–B trio through capture,
processing, presentation, cognate help, plasmablast commitment and three IgM
secretion events. It renders full snapshots and finite antigen ownership from
20 complete kernel rounds. Nonparticipating cells choose WAIT. No Jev calls
are made, and no future Jev probabilities have been changed.

All page text, controls, gallery labels and launcher messages are in English.
The user-supplied green plasma-cell sheet is used for the committed plasmablast
in the story; the same B-cell identity and clone are retained. The existing
Studio renderer still uses its original terminal B-cell geometry.

## Open the Studio

On Windows, `Start Jev.cmd` prompts for the project's TypeSafe key using hidden
input if needed, asks for an explicit request cap, and opens
http://127.0.0.1:8012/ with Jev selected. No inference occurs until Run with Jev
or +30 min is selected. `Start Lymph Node.cmd` opens the fixture-only Studio.

The illustrations represent the kernel's actual agents: local observation,
Jev choice, validation and execution, then the same cell's state and position.
Select a cell to inspect its last decision and execution receipt. Active
programs use kernel deadlines; contact lines require reciprocal active programs
and the permitted physical distance. Legacy recordings have no invented contacts.

Illustrated cells switches to the supplied artwork. Original 3D restores the
original meshes. Pause illustration affects only cosmetic motion. The gallery
at `/web/cell-gallery.html` offers all eight poses for each of four source sheets.
Reduced-motion preferences start cosmetic animations paused.

## Scope

Brown lymphocytes represent B cells, yellow lymphocytes represent CD4 T cells,
and dendritic artwork represents cDC2. These are proposed color assignments.
Neutrophils are only previewed in the gallery because the model has no
neutrophil handler. Conventional DCs and FDCs are distinct.

The source PNGs are copied unchanged. The tissue remains a monolayer; planes
with textures are not volumetric cell reconstructions. Eight poses crossfade
with a stable phase per cell identity. Individual dendritic crop bounds retain
processes that cross the nominal grid. Aspect ratios and original edge pixels
are preserved. Filopodia do not increase collision or contact volumes.

GC B states have violet rings; memory B cells have pink rings. Other Studio
cell types and terminal B-cell states retain their original geometry. Legacy
recordings lack per-frame antigen positions; the new scripted story stores its
own complete antigen ledger at every frame.

## Verification

Tests cover 100- and 300-cell views without changing biological state, stable
cell picking, distinct poses, paused animation, reduced motion, narrow layouts,
missing-image fallback, and both fixture and actual saved Jev replay. Browser
checks cover the original Studio, artwork gallery, Jev controls, ten-cell
preview and static player. The vaccination story adds a legal full-round
fixture trace, negative CD40/HLA controls, event-order and conservation checks,
and playback/seek/selection checks without inference calls.

`cell-art-review/checks.json` is a short headless Chrome renderer check, not
Jev latency measurement or a sustained benchmark. Screenshots record visual
reviews. `python scripts/build_site.py` builds the local API-free player.
No deployment was made; the Gut project remains outside these changes.

# Ten-decision visual preview · 22 September 2026

The local preview uses the same 100-cell tissue and supplied artwork. A real
`jev-1.13.0` response provided exactly ten choices in one successful request:
seven MOVE preferences and three WAIT preferences. The kernel accepted all ten;
collision checks allowed only one actual position change. Mandatory clocks and
antigen transport advanced by one partial 30-minute step. The other 90 cells
received no choices or fixture substitutes. This is a design inspection sample,
not a complete scientific round or a biological outcome demonstration.

The successful response reports 13,288 input tokens and 333 output tokens.
A preceding connection failure returned no answers; its usage is unknown and
its receipt is retained separately. Both records remain under ignored
`recordings/private/`. No credentials are included in receipts.

The result at `http://127.0.0.1:8012/` is served by a read-only viewer with no
network-capable decision provider. Selection, artwork animation and the
**Before / After Jev** comparison make no additional inference calls. The usual
experiment controls are disabled. The full-round engine remains unchanged.

Verification: 54 unit tests passed, including exact ten-question request size,
one-attempt enforcement, failure preservation, no fixture fallback, and refusal
to overwrite an existing receipt. Browser tests passed for the ten-cell panel,
selection, before/after, blocked mutation controls and mobile overflow, together
with the existing Studio and static replay checks. Reviewed the actual live
result in the browser with the supplied B, CD4 and cDC2 images.
