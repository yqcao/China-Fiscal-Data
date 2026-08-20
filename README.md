# China Fiscal Data · 中国政府预算四本账

Archived data and interactive visualizations of China's government budget system,
sourced from the Ministry of Finance (财政部).

**Live site:** https://yqcao.github.io/China-Fiscal-Data/

## Pages (GitHub Pages)

| Page | Description |
|------|-------------|
| [`index.html`](index.html) | Landing page linking the visualizations below |
| [`fiscal-monitor.html`](fiscal-monitor.html) | **Monthly Fiscal Monitor** — interactive ECharts dashboard: general public budget, government-managed fund, and local-government bond issuance/repayment, 2021–2026 |
| [`fiscal-drag.html`](fiscal-drag.html) | **Fiscal Drag Monitor** — is budget execution adding to demand or subtracting from it? Execution pace vs. budget, fiscal impulse, and the pass-through to FAI and GDP |
| [`mohrss.html`](mohrss.html) | **Employment & Social Insurance** — every indicator in the MOHRSS monthly release: jobs, unemployment rate, and the social-insurance schemes' participants, fund revenue, expenditure and balance, 2013–2026 |
| [`imf-augmented.html`](imf-augmented.html) | **IMF Augmented Debt & Deficit** — how the IMF builds China's augmented general-government debt and deficit (IMF Table 2) |
| [`budget-system.html`](budget-system.html) | China Budget System — overview of the four-account budget system (四本账) |
| [`budget-system-fy2025.html`](budget-system-fy2025.html) | China Budget System — FY2025 execution figures |

The budget-system pages draw on data from [NPC Observer](https://npcobserver.com/about-npc/).

## Datasets

### `data/mof-reports/` — 全国财政收支情况 (National Fiscal Revenue & Expenditure)

Monthly/annual fiscal reports from the MOF Treasury Department.

- **Source:** https://www.mof.gov.cn/zhengwuxinxi/redianzhuanti/quanguocaizhengshouzhiqingkuang/
- **Coverage:** 183 reports, 2008-08 → 2026-07
- **Contents:** the data is narrative text (no attachments on these pages)

```
raw/                183 original report pages (.htm)
text/               183 cleaned plain-text extractions (.txt)
listing/            9 paginated index pages
article_urls.txt    source URLs
index.json          catalog: file, date, title, url, char count (regenerated each run)
INDEX.md            human-readable, date-sorted table (regenerated each run)
fiscal_series.json  structured series parsed for the monitor page (2021–2026):
                    both budget accounts, central/local splits, 17 tax items,
                    10 expenditure categories, land-sale revenue
```

### `data/mof-research-reports/` — 研究报告 / 地方政府债券市场报告 (Local Government Bond Market Reports)

Monthly, bilingual (Chinese + English) reports from the China Government Debt Center.

- **Source:** https://kjhx.mof.gov.cn/yjbg/
- **Coverage:** 173 reports, 2019-04 → 2026-08
- **Contents:** each report is a downloadable attachment (PDF/docx)

```
listing/            18 paginated index pages
raw/                173 article wrapper pages (.htm)
files/              173 attachments — 170 PDF + 3 docx, ~219 MB (LOCAL ONLY, gitignored)
markdown/           markdown conversions of the attachments (via markitdown)
catalog.json        per-report: date, title, article, local file, size
article_urls.txt    source URLs
INDEX.md            human-readable, date-sorted table
```

> **Note:** The 219 MB of PDF/docx attachments under `files/` are **not committed**
> (see `.gitignore`). `INDEX.md` and `catalog.json` map every report to its source
> URL so the binaries can be re-downloaded. The text-only `markdown/` conversions
> are committed for searchability.

Parsed series for the monitor: `lgb_series.json` (issuance, general/special, new/refinancing,
average rate & maturity, secondary-market turnover, use-of-proceeds) and `new_special_ytd.json`
(YTD new special-bond issuance, RMB bn).

### `data/mof-debt-balance/` — 地方政府债券发行和债务余额情况 (debt balance & repayment)

Monthly local-government-bond issuance, balance, and **principal repayment** reports.

- **Sources:** 预算司 https://yss.mof.gov.cn/zhuantilanmu/dfzgl/sjtj/ (history through 2024) ·
  债务管理司 https://zwgls.mof.gov.cn/tjsj/ (2024-12 onward)
- **Coverage:** repayment series 2021-01 → 2026-06

```
listing*/ raw*/        listing pages and report HTML from both sources
repayment_series.json  YTD principal repaid (亿元), split into refinancing-bond-funded
                       and fiscal-fund-funded
INDEX.md               source notes
```

### `data/mohrss/` — 人力资源和社会保障主要统计快报数据 (employment & social insurance)

Monthly statistical release from the Ministry of Human Resources and Social Security.
This is the **third** of the four budget accounts (社会保险基金预算) — the one MOF's monthly
fiscal report does *not* cover — plus the employment indicators.

- **Source:** https://www.mohrss.gov.cn/SYrlzyhshbzb/zwgk/szrs/tjsj/
- **Coverage:** 160 monthly releases, 2013-01 → 2026-06 (82 `.xls` + 78 `.pdf`, 9.5 MB)

```
files/               160 source attachments, named mohrss_YYYY-MM.{xls,pdf}
catalog.json         per-release: period, title, article URL, attachment URL, local file
INDEX.md             human-readable, date-sorted table
mohrss_series.json   38 parsed fields per month (see below)
```

Parsed fields: employment (`emp_new`, `emp_reemp`, `emp_hard`, `skill_certs`), unemployment
rate (`unemp_survey`, `unemp_registered`), and for each of six schemes — `pension_urban`,
`pension_rural`, `ui`, `injury`, `medical`, `maternity` — the triplet `_insured` / `_rev` /
`_exp` plus a derived `_bal`. Also labour-dispute arbitration (`disp_*`) and labour
inspection (`insp_*`).

**Two eras, two formats.** 2013-01 → 2019-12 are legacy binary `.xls`; 2020-01 onward are
PDFs. `scripts/parse_mohrss.py` reads both — PDFs via `pdftotext -layout` (poppler), xls via
the optional `xlrd` package. Without `xlrd` the script still builds the 2020+ series and says
so. Nothing is keyed off the table's 序号, because the row numbering shifts between editions
(the 技师/职业技能等级证书 row appears only in some), so indicators are matched by label and
the insurance schemes by the fixed order of their triplets.

**Structural breaks**, surfaced on the page rather than papered over:

| Series | Available | Why it stops / starts |
|---|---|---|
| `medical_*` | 2013–2018 | 医疗保险 moved to the new 国家医保局 |
| `maternity_*` | 2013–2018 | 生育保险 merged into medical insurance |
| `unemp_registered` | 2013–2021 | 登记失业率 dropped from the table |
| `unemp_survey` | 2022–2026 | 调查失业率 added to the table (different definition — not spliced) |
| `disp_*`, `insp_*` | sparse | published only in the quarterly and annual editions |

> **Collection is browser-assisted.** The MOHRSS site is behind a JavaScript bot challenge;
> `curl`/`urllib` get a ~1 KB cookie-setting stub instead of the page. This repo deliberately
> ships **no bot-detection bypass**, so unlike the MOF/NBS/PBOC scrapers this dataset cannot be
> refreshed unattended — see *Refreshing the MOHRSS data* below.

## The Monthly Fiscal Monitor

The dashboard (`fiscal-monitor.html`) embeds the four parsed JSON series inline and is
organised in three sections. English-primary with a **EN / 中文** toggle; all monetary
values in **RMB billion / trillion**. Global **口径** (cumulative YTD ↔ derived single-month)
and **分项** (national ↔ central/local) toggles apply to the budget sections.

1. **General Public Budget** — KPI cards; separate Revenue and Expenditure panels (bars =
   level, line = YoY, aligned dual axes); tax & expenditure composition pies + YTD-growth bars.
2. **Government-Managed Fund Budget** — fund revenue (land-sale stacked) + expenditure; YoY.
3. **Local Government Bond Issuance** — issuance by type + rate; refinancing issuance vs
   principal repayment; new special-bond YTD by year; use of new-bond proceeds (month
   selector); average maturity & secondary-market turnover; issuance YoY.

**Caveat on data basis:** the MOF publishes cumulative figures (年初至当期). Single-month
values are derived by differencing consecutive reports within a year; each year's first
report covers 1–2月 combined, so January has no standalone value.

## The Fiscal Drag Monitor

`fiscal-drag.html` answers one question — **is fiscal policy adding to demand, or taking it away?** —
in five steps, one chart each. "Broad" throughout means the two accounts MOF reports monthly
(general public budget + government-managed fund budget); levels are in RMB trillion.

1. **Execution pace** — cumulative broad expenditure as a share of the full-year budget, one line
   per year. Shows directly whether the current year is running ahead of or behind the seasonal norm.
2. **Fiscal impulse** — YoY change in the broad YTD deficit, in RMB trillion. Above zero the budget
   is injecting more demand than a year earlier; below zero it is withdrawing it.
3. **Pass-through** — broad spending growth split into its two accounts, against fixed-asset
   investment. The government-fund account is the infrastructure account and moves with FAI.
4. **The constraint** — land-sale and government-fund revenue against government-fund expenditure,
   i.e. why execution slips when land revenue falls.
5. **Track record** — full-year broad expenditure against the budget approved the previous March.

Inputs: `fiscal_series.json`, `data/budget-targets.json`, and `data/macro/{fai,gdp}_series.json`.
Because it consumes both the fiscal and the macro series, it is rebuilt by **both** `update.sh`
and `update_macro.sh`.

**Caveats** (also stated on the page): growth rates are computed from reported levels and may
differ slightly from MOF's own comparable-basis (可比口径) figures; the budget denominator is the
NPC's March 年初预算 and does not reflect mid-year supplementary budgets; and the page shows
co-movement, not a causal estimate.

## Updating the data (periodic refresh)

The whole pipeline is scripted under `scripts/`. The scrapers are **idempotent and
incremental** — they re-read the live listing pages, download only reports not already on
disk, re-parse everything, and regenerate the JSON series and the page.

```
scripts/
  fetch_fiscal.py      MOF 全国财政收支情况          → data/mof-reports/fiscal_series.json
  fetch_bonds.py       地方政府债券市场报告 (+PDFs)   → lgb_series.json, new_special_ytd.json
  fetch_repayment.py   地方政府债券发行和债务余额情况 → repayment_series.json
  build_monitor.py       rebuild fiscal-monitor.html from the four JSON series
  build_fiscal_drag.py   rebuild fiscal-drag.html (fiscal series + budget targets + FAI/GDP)
  parse_mohrss.py        parse data/mohrss/files/ → mohrss_series.json (browser-collected)
  build_mohrss.py        rebuild mohrss.html from mohrss_series.json
  update.sh              run all of the above in order
```

**To refresh after MOF publishes new monthly data:**

```bash
bash scripts/update.sh            # fetch + parse + rebuild
bash scripts/update.sh --commit   # also git commit & push (triggers the GitHub Pages rebuild)
```

Then hard-refresh the live page (GitHub Pages takes ~1–2 min to redeploy).

The NBS and PBOC listing sites throttle rapid repeated requests, which can stall
`update_macro.sh` for a long time on a deep crawl. For a routine incremental refresh, limit how
many listing pages each fetcher walks:

```bash
MACRO_MAX_PAGES=4 TRADE_MAX_PAGES=4 PBOC_MAX_PAGES=3 bash scripts/update_macro.sh
```

Raise these (or drop them, for the 24/24/12 defaults) only when backfilling deep history.

### Refreshing the MOHRSS data

`scripts/parse_mohrss.py` only *parses* what is already under `data/mohrss/files/`, so it is
safe to re-run any time. Adding a newly published month needs the attachment fetched through a
browser first:

1. Open https://www.mohrss.gov.cn/SYrlzyhshbzb/zwgk/szrs/tjsj/ in a normal browser.
2. Open the newest 《YYYY年1-M月人力资源和社会保障主要统计快报数据》 release and download its
   PDF attachment.
3. Save it as `data/mohrss/files/mohrss_YYYY-MM.pdf` and add the matching entry to
   `data/mohrss/catalog.json`.
4. Run `python3 scripts/parse_mohrss.py && python3 scripts/build_mohrss.py`.

Optional, for the pre-2020 `.xls` half: `pip install xlrd`. `pdftotext` (poppler) is required
for the PDF half — `brew install poppler`.

**Requirements:** Python 3 (standard library only) for the scrapers/parsers; for converting
new bond-report PDFs to markdown, install markitdown once —
`uv tool install 'markitdown[pdf,docx]'` (or `pipx install 'markitdown[pdf,docx]'`).
Individual steps can be run on their own, e.g. `python3 scripts/fetch_bonds.py` then
`python3 scripts/build_monitor.py`.

**Typical cadence:** the fiscal report lands ~mid-month; the bond-market and debt-balance
reports ~early-to-mid month. Running `update.sh` monthly keeps all three sections current.

---

*Data © Ministry of Finance of the People's Republic of China. This repository is an
archive and visualization for research and educational purposes.*
