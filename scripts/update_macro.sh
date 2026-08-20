#!/usr/bin/env bash
# Refresh China macro-indicator series and rebuild their pages.
#
# Sources are NBS / PBOC / Customs press releases. Run this from a machine with
# good access to stats.gov.cn & pbc.gov.cn — it is FAR faster there, and the NBS
# full-history data API (data.stats.gov.cn, blocked in some sandboxes) may also be
# reachable for deeper backfill.
#
# Validation status (as of first build):
#   cpi    — validated (YoY + MoM, ~21 months)
#   retail — validated (YTD YoY; monthly YoY parser may need a tweak)
#   pmi / fai / gdp / trade / pboc — fetchers written but NOT yet validated on a
#     full run; check the JSON and adjust the parser regexes if a field is null.
#
# Usage:  bash scripts/update_macro.sh            # fetch + build
#         bash scripts/update_macro.sh --commit   # also git commit & push
set -uo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}

for s in cpi pmi retail fai gdp trade pboc; do
  echo "==> fetch $s"
  $PY "scripts/fetch_$s.py" || echo "   (fetch_$s failed — continuing)"
done

echo "==> build pages"
$PY scripts/build_macro.py
$PY scripts/build_fiscal_drag.py || echo "   (build_fiscal_drag failed — continuing)"

if [[ "${1:-}" == "--commit" ]]; then
  echo "==> committing"
  git add data/macro/*.json *.html scripts/fetch_*.py scripts/build_macro.py scripts/build_fiscal_drag.py 2>/dev/null || true
  git commit -m "Macro data refresh: $(date +%Y-%m-%d)" && git push || echo "nothing to commit"
fi
echo "Done. Open the *.html pages (or push for GitHub Pages)."
