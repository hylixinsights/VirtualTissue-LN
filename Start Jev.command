#!/bin/zsh
cd -- "${0:A:h}"
export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/lymph-node-python-cache"
if [[ -z "$TYPESAFE_API_KEY" && ! -f .env ]]; then
  read -rs 'TYPESAFE_API_KEY?TypeSafe API key (hidden): '
  print
  export TYPESAFE_API_KEY
fi
read 'ln_request_budget?Maximum paid HTTP requests for this server session (e.g. 100): '
if [[ "$ln_request_budget" != <1-100000> ]]; then
  print 'A positive explicit request budget is required.'
  exit 1
fi
print 'Open http://127.0.0.1:8010, select Jev, then Create new experiment.'
python3 server.py --port 8010 --open-browser --enable-jev --max-requests "$ln_request_budget"
