#!/usr/bin/env bash
# deploy/bootstrap.sh - feature 017: bring a FRESH clone to a servable state.
# Idempotent; never touches secrets. The two OUT-OF-BAND items (never committed) are
# checked by NAME at the end: ~/.hermes/.env (API keys) and the brands/ asset dir.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== xcela bootstrap =="

# 1. Python 3.11 (the pinned runtime; see requirements.txt header)
PY=python3.11
command -v "$PY" >/dev/null 2>&1 || { echo "ERROR: python3.11 not found (apt install python3.11 python3.11-venv)"; exit 1; }

# 2. venv + pinned deps
if [ ! -x .venv/bin/python ]; then
  "$PY" -m venv .venv
  echo "created .venv"
fi
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt
echo "deps installed from requirements.txt"

# 3. runtime dirs (brands/ fills itself through the /onboard wizard)
mkdir -p output brands
echo "output/ and brands/ ready"

# 4. OUT-OF-BAND item checks (named, non-fatal: the server can boot without them, but no
#    run can spend / no logo can resolve until they exist)
if [ ! -f ".env" ] && [ ! -f "$HOME/.hermes/.env" ]; then
  echo "MISSING (out-of-band item 1): API keys"
  echo "  -> cp .env.example .env and fill in OPENAI_API_KEY / ANTHROPIC_API_KEY"
  echo "     (real environment variables also work and always win; ~/.hermes/.env is the legacy home)"
fi
BRANDS_DIR="${XCELA_BRANDS_DIR:-$(pwd)/brands}"
if [ ! -d "$BRANDS_DIR" ]; then
  echo "MISSING (out-of-band item 2): brands dir $BRANDS_DIR"
  echo "  -> scp the brands/ directory (logos + licensed assets) there"
else
  .venv/bin/python - <<'PYEOF'
import json, sys
from pathlib import Path
sys.path.insert(0, "harness")
from asset_paths import try_resolve_brand_asset
missing = []
for key in sorted(Path("answer_keys").glob("*.json")):
    lp = json.loads(key.read_text(encoding="utf-8")).get("logo_path", "")
    if try_resolve_brand_asset(lp) is None:
        missing.append(f"{key.name}: {lp}")
if missing:
    print("note: these PRE-EXISTING brand keys have no logo asset on this machine; runs for")
    print("them will refuse loudly until the asset is provided. This is fine for a fresh")
    print("deployment: onboard YOUR brands via /onboard (which supplies assets itself).")
    for m in missing:
        print("  ", m)
else:
    print("all committed brand keys resolve their logos")
PYEOF
fi

echo
echo "next steps:"
echo "  test:   .venv/bin/python test_conductor.py"
echo "  serve:  .venv/bin/python frontend/server.py       (or install deploy/xcela.service)"
echo "  proxy:  fill deploy/Caddyfile placeholders (domain + hashed password), then run caddy"
echo "  NOTE:   restart the server after every update (server.py loads once)"
