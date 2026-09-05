#!/usr/bin/env bash
# Refresh all data series and rebuild the monitor page.
# Run monthly after MOF publishes (~mid-month for fiscal, ~early month for bonds).
#
# Usage:   bash scripts/update.sh           # fetch + parse + rebuild
#          bash scripts/update.sh --commit   # also git commit & push the result
set -euo pipefail
cd "$(dirname "$0")/.."          # repo root
PY=${PYTHON:-python3}

echo "==> 1/12 General Public Budget + Government Fund"
$PY scripts/fetch_fiscal.py

echo "==> 2/12 Local Government Bond issuance (+ new special YTD)"
$PY scripts/fetch_bonds.py

echo "==> 3/12 Principal repayment"
$PY scripts/fetch_repayment.py

echo "==> 4/12 Government-bond holder structure (CCDC)"
$PY scripts/fetch_holders.py

echo "==> 5/12 Rebuild fiscal-monitor.html"
$PY scripts/build_monitor.py

echo "==> 6/12 Rebuild fiscal-drag.html"
$PY scripts/build_fiscal_drag.py

echo "==> 7/12 Four-account annual totals"
$PY scripts/parse_accounts.py

echo "==> 8/12 Rebuild spending.html"
$PY scripts/build_spending.py

echo "==> 9/12 Rebuild tax-split.html"
$PY scripts/build_tax_split.py

echo "==> 10/12 Provincial government work reports"
$PY scripts/fetch_prov_reports.py

echo "==> 11/12 Rebuild growth-targets.html"
$PY scripts/build_prov_map.py

echo "==> 12/12 Rebuild report-maps.html"
$PY scripts/build_report_maps.py

if [[ "${1:-}" == "--commit" ]]; then
  echo "==> committing"
  # add data/ wholesale and let .gitignore do the excluding: naming an ignored
  # path explicitly (data/prov-reports/raw) aborts the whole add
  git add fiscal-monitor.html fiscal-drag.html spending.html tax-split.html growth-targets.html report-maps.html index.html data 2>/dev/null || true
  git commit -m "Data refresh: $(date +%Y-%m-%d)" \
    -m "Re-scraped MOF sources and rebuilt the monitor." || { echo "nothing to commit"; exit 0; }
  git push
fi
echo "Done. Open fiscal-monitor.html (or push for GitHub Pages)."
