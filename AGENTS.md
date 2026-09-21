# Independent Lymph Node Studio

Work only in this project. Never edit, import runtime files from, or reuse credentials from the sibling Gut project. Preserve the original supplied manuals. Read README.md and docs/IMPLEMENTATION.md before changing biology. The reference manual describes a broader scope than implemented handlers.

Keep all numerical assumptions explicitly proposed and uncalibrated. One agent is one cell. Preserve lineages, z=0 monolayer geometry, physical contacts, finite antigen accounting, ancestry and timed events. Jev receives only each cell's local observations and prevalidated menu; the server owns state. Do not add unsupported actions or pretend fixtures are Jev.

Use fixture responses for automated tests. Enable paid inference only with explicit user intent and a bounded request budget. Keep API keys server-side and out of output, recordings and source control. Preserve partial request failures and honest unknown usage. No automatic retry or fixture fallback.

Run the relevant unittest suite after kernel/adapter changes. Run tests/episodes.py for changes to scenario biology and tests/browser.mjs for UI changes. Review screenshots. Update docs/model-contract.json from the actual engine contract and record material scope limitations.
