#!/usr/bin/env bash
# Create .venv in the repo root and install requirements (same as README Step 3).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
echo "Done. Activate: source .venv/bin/activate"
