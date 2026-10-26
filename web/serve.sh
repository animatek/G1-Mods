#!/bin/sh
# The web builder on this computer: packs the modules (make_bundle.py) and serves web/ at
# http://localhost:8090. Pyodide comes from its CDN, so the page needs the internet once.
cd "$(dirname "$0")"
python3 -I make_bundle.py || exit 1
echo "http://localhost:8090"
exec python3 -I -m http.server -b 127.0.0.1 8090
