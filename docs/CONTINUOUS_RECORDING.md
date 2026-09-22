# Continuous Jev recording and portable playback

The continuous recorder preserves real individual Jev decisions after the first
antibody event. It records every physical tick using lossless changes to cell
state, together with complete local observations, legal menus, provider responses,
lineages, antigen accounting and biological events.

## Running it

Python 3.10+ is the only runtime requirement. Start Jev.cmd (Windows) and Start
Jev.command (macOS) both call `scripts/start_jev.py`. The launcher reads a hidden
key or the project's ignored `.env`, asks for a call allowance, and opens the
local recorder. The key is never sent to the browser, stored in browser storage,
or embedded in an exported recording.

```sh
python scripts/start_jev.py --max-requests 5000
python scripts/start_jev.py --max-requests 500 --policy local
```

Each invocation creates a fresh run with its own hard ceiling. Limits are integers
from 1 to 100,000. A call cap is not a dollar or token budget. The default mode
normally asks one individual question per HTTP request and runs up to four
independent questions concurrently. Near the ceiling, remaining questions may be
batched to finish a complete physical round without exceeding the cap. This is
recorded per round. Quiet cells and busy cells receive no redundant questions.

The **Stop & save** browser button, or Ctrl+C in the terminal, waits for in-flight
requests to finish and saves the result. Network or
schema failures stop the run; there is no automatic retry or fixture fallback.
Unknown usage stays explicitly unknown. Existing run folders cannot be overwritten.
The provider journal is flushed before and after every request; completed rounds
are journaled separately. Full compressed checkpoints are written every 100 calls
and on normal completion, handled stopping, or failure.

An explicit continuation is available for a fully checkpointed stopped or failed
run with no incomplete decision round:

```sh
python scripts/start_jev.py --resume --output recordings/private/RUN --max-requests 5000
```

Supply the **original total cap**, seed, population and policy, not a new allowance.
Close the previous local server before reusing its port, or choose a different
`--port` for the continuation.
The recorder validates every saved response and hash, reconstructs the kernel and
random state from those choices, and verifies exact agreement before sending a
new request. Previously spent calls remain counted. It refuses unresolved or
uncheckpointed requests; there is no automatic network retry. Original checkpoints
are retained, and each explicit continuation is logged. Brief Windows file-sharing
conflicts retry only the local replacement of already-written checkpoint bytes.

## Demonstration policy

The default v6 policy illustrates competing fates. For a helped activated B cell,
a toy affinity annotation of at least 0.79 favors eligible early plasmablast
commitment. Lower annotations favor eligible GC founding or local migration.
Licensed GC cells favor division. Already selected GC daughters can favor output.
Plasmablasts favor secretion until three own output units, then maturation;
mature plasma cells favor secretion.

This threshold is a **proposed visual-demonstration prior**, chosen to exercise
competing programs. It is not a measured affinity-to-fate law or calibrated
probability. Jev still returns its own choice and preferences. The kernel does
not force these results. No target cell IDs, global population counts, or future
events are sent to individual questions. `--policy local` uses v3 model semantics;
`--policy plasmablast` selects the earlier v5 high-output preference.

`RecordingSimulation` inherits all reactive biological gates and clocks. It adds
only the cell's own accumulated antibody output to its local observation and a
lossless visual recording format. Numerical biology remains proposed. The live
population limit remains 150 cells.

The full request-budget run can continue long after the initial antigen is gone.
The present model has no calibrated plasma-cell lifespan or antibody decay; late
sustained output must not be interpreted as a prediction of vaccine protection.
The public player separates the initial response highlights from the full saved
time range and keeps both available for inspection.

## Replay

The browser switches to playback when recording stops. Play/pause, one-tick step,
a time slider, speed, event chapters, cell inspection and final-state controls all
read saved data. Native antigen, pMHC, contact programs, migration, daughter
positions and output indicators come from the recorded frames. Artwork pose
animation and positional interpolation do not add biological decisions.

The episode contains a full initial frame followed by lossless cell-field deltas;
seeking reconstructs exact recorded states using cached checkpoints. A daughter's
inspector retains its parent and clone. The stored provider receipts are available
alongside each cell's last choice. No new Jev calls occur during replay.

Use **Zoom** (1×–6×), the **− / +** buttons, or scroll over the tissue to look
closer. Drag the tissue or use the four arrow buttons to move the view; on touch
screens, drag with one finger or pinch with two. **Reset view** returns to the
whole tissue. **Focus response** follows the selected cell, and event chapters
recenter on their recorded participant. Panning takes over from automatic follow;
your view stays in place while playing, pausing, or seeking through the timeline.
With the tissue focused, arrow keys pan, plus/minus zoom, and Home resets;
Shift + left/right inspects the next or previous cell.

These camera controls work with the existing saved episode. They do not alter
cell positions, decisions, or the recording, and require no new run or Jev calls.
They are available in both the live viewer and the static website player.

## Build for GitHub and the website

Select the completed episode explicitly:

```sh
python scripts/build_reactive_site.py --recording recordings/private/RUN/episode.ln.json.gz
python -m http.server 8020 --bind 127.0.0.1 --directory site
```

`site/` is a static package with relative URLs, supplied cell art, compressed
recording, SHA-256 integrity manifest and provenance page. It works at the domain
root or under `/lymph-node/`. Only same-origin files are fetched during replay;
no Python server or API key is needed on the public website.

For a checked-in example, copy only the reviewed episode to `recordings/examples/`
and add its file/hash to `reactive-index.json`. `scripts/build_site.py` selects
that reviewed reactive example when present. `.env`, all unselected private runs,
logs and the machine's configuration remain excluded from source packages.
`--preview-running` is for a labeled local review snapshot while a run is still active.

The source release includes the launchers, recorder, kernel, tests and selected
example. The site release includes only the static player and recording. Publishing
to GitHub or the production website is a separate user-controlled step.

## Export an MP4

The interactive recording is the complete inspectable result. A separate 1080p
MP4 can show a captioned tour of the same saved canvas, followed by the final state.
It does not simulate new events or call Jev. Every caption is tied to a recorded
event; the film explicitly labels its accelerated timeline and illustrative artwork.

With the static site served, developers can use Node, Playwright and current Chrome:

```sh
npm install --no-save playwright
node scripts/export_reactive_video.mjs --url http://127.0.0.1:8020/ --output dist/lymph-node-jev-highlights.mp4
```

The optional video exporter records 150 seconds by default. It also writes a JSON
sidecar containing the episode hash, actual call count, event chapters and capture
dimensions. The MP4 is a separate sharing artifact; the source and static player
do not require it or these developer dependencies to run.
