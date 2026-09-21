#!/bin/zsh
cd -- "${0:A:h}"
export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/lymph-node-python-cache"
python3 server.py --port 8010 --open-browser
