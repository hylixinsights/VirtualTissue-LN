# Independent repository, shared website

`hylixinsights/VirtualTissue-LN` owns this simulator, biological manual, tests and reviewed public recording. It does not import the Gut simulator at runtime. The local API key and unselected sessions remain outside Git and release packages.

The existing `hylixinsights/VirtualTissue` repository remains the only publisher for `virtualtissue.org`. It can build this repository at a pinned commit and copy only the resulting `site/` into `/lymph-node/`. It must retain the existing Gut player and links. No extra domain or Python hosting is needed for replay.

## Build the public player

The current reactive recorder and timeline player are documented in
[CONTINUOUS_RECORDING.md](CONTINUOUS_RECORDING.md). When a reviewed
`recordings/examples/reactive-index.json` is present, the default build below uses
that example. `python scripts/build_site.py --legacy` retains the earlier memory
B-cell example described later in this document.

```sh
python3 scripts/build_site.py
python3 -m http.server 8020 --bind 127.0.0.1 --directory site
```

Open http://127.0.0.1:8020/. The same site works under a subdirectory such as `/lymph-node/`. It includes relative assets, a catalog allowlist and a SHA-256 check of the recording. The generated player has no simulation API client, inference endpoint or secret. Same-origin static files are its only network dependencies.

The reviewed example contains actual Jev responses. The local default simulation still uses an explicitly labeled fixture. The browser disclosure identifies the proposed fate-policy revision at 60 hours. All numerical biology remains uncalibrated.

## Verify and package

```sh
python3 -m unittest discover -s tests -q
node tests/browser_reactive_replay.mjs
python3 scripts/package_release.py
```

The browser test requires Playwright/Chrome and the static preview above. `SITE_URL` selects a nested preview; `PLAYWRIGHT_MODULE` can select an existing Playwright runtime. CI installs Chromium and makes no paid requests.

Release packages contain allowlisted source or static replay files. `scripts/release_files.json` controls the source package; `dist/SHA256SUMS.json` identifies the generated archives. GitHub releases and the portal update are separate operations: publishing new LN source does not automatically change the portal's pinned version.
