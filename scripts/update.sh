#!/usr/bin/env bash
# Refresh all data series and rebuild the monitor page.
# Run monthly after MOF publishes (~mid-month for fiscal, ~early month for bonds).
#
# Usage:   bash scripts/update.sh           # fetch + parse + rebuild
#          bash scripts/update.sh --commit   # also git commit & push the result
set -euo pipefail
cd "$(dirname "$0")/.."          # repo root
PY=${PYTHON:-python3}

echo "==> 1/7 General Public Budget + Government Fund"
$PY scripts/fetch_fiscal.py

echo "==> 2/7 Local Government Bond issuance (+ new special YTD)"
$PY scripts/fetch_bonds.py

echo "==> 3/7 Principal repayment"
$PY scripts/fetch_repayment.py

echo "==> 4/7 Rebuild fiscal-monitor.html"
$PY scripts/build_monitor.py

echo "==> 5/7 Rebuild fiscal-drag.html"
$PY scripts/build_fiscal_drag.py

echo "==> 6/7 Four-account annual totals"
$PY scripts/parse_accounts.py

echo "==> 7/7 Rebuild spending.html"
$PY scripts/build_spending.py

if [[ "${1:-}" == "--commit" ]]; then
  echo "==> committing"
  git add fiscal-monitor.html fiscal-drag.html spending.html index.html data/*/*.json data/*/raw* data/*/listing* data/*/text data/*/markdown data/*/*.txt 2>/dev/null || true
  git commit -m "Data refresh: $(date +%Y-%m-%d)" \
    -m "Re-scraped MOF sources and rebuilt the monitor." || { echo "nothing to commit"; exit 0; }
  git push
fi
echo "Done. Open fiscal-monitor.html (or push for GitHub Pages)."
