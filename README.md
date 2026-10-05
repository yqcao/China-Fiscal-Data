# China Fiscal Data · 中国政府预算四本账

Archived data and interactive visualizations of China's government budget system,
sourced from the Ministry of Finance (财政部).

**Live site:** https://yqcao.github.io/China-Fiscal-Data/

GitHub Pages serves the **`docs/`** folder only. For now just two pages are published there —
the Monthly Fiscal Monitor and the FY2025 budget-system page — plus a landing page; the other
pages below are built into the repo root and are not on the live site. `build_monitor.py` writes
the monitor to both places; the FY2025 page is a static copy.

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
- **Coverage:** 185 reports, 2008-08 → 2026-07
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

**Province-level issuance.** The report's own by-province table (表2) and YTD chart (图3) are
images in the PDF with no extractable text, so `scripts/parse_prov_bonds.py` rebuilds the split
from the 发行明细表 appendix instead: every individual bond, classified to one of the 36 issuers
(31 provinces + 5 计划单列市 + the XPCC) and to new/refinancing × general/special from its name.
Writes `prov_bonds_<year>.json` and `lgb_provinces_<year>.csv`. 2024 and 2025 reconcile to the
reports' own published totals to within rounding (2025: 103,101.21 vs 103,101 亿元; refinancing
49,284.12 vs 49,284.07). Needs the gitignored PDFs under `files/` — re-fetch with
`fetch_bonds.py`. Caveat: bonds replacing hidden debt are issued as ordinary 再融资专项债券 and
cannot be told apart by name, so `refi_special` is an upper bound on the swap.

Parsed series for the monitor: `lgb_series.json` (issuance, general/special, new/refinancing,
average rate & maturity, secondary-market turnover, use-of-proceeds) and `new_special_ytd.json`
(YTD new special-bond issuance, RMB bn).

### `data/mof-debt-balance/` — 地方政府债券发行和债务余额情况 (debt balance & repayment)

Monthly local-government-bond issuance, balance, and **principal repayment** reports.

- **Sources:** 预算司 https://yss.mof.gov.cn/zhuantilanmu/dfzgl/sjtj/ (history through 2024) ·
  债务管理司 https://zwgls.mof.gov.cn/tjsj/ (2024-12 onward)
- **Coverage:** repayment series 2021-01 → 2026-07

```
listing*/ raw*/        listing pages and report HTML from both sources
repayment_series.json  YTD principal repaid (亿元), split into refinancing-bond-funded
                       and fiscal-fund-funded; plus each month's issuance (total /
                       general / special / new / refinancing), average rate & maturity,
                       and YTD total and new-special issuance, from the same release;
                       and the month-end debt balance (total / general / special /
                       bond / non-bond), remaining maturity, average coupon, interest
                       paid, and the NPC debt ceiling where the release restates it
INDEX.md               source notes
```

### `data/celma/` — 中国地方政府债券信息公开平台 (province-level debt panel)

The MOF-run local-government bond disclosure platform, mandated by
《地方政府债券信息公开平台管理办法》. It is the only official source that publishes the
**new-debt quota allocated to each province** (新增一般/专项债务限额) next to that province's
actual issuance, which is what makes province-level execution computable — the Debt Center's
market report carries issuance only, and its by-province table is an image.

- **Source:** https://www.celma.org.cn/ (JSON API behind the 年度/季度/月度数据 pages)
- **Coverage:** 37 regions (31 provinces + 5 计划单列市 + XPCC), 2015–2025 annual,
  2025-02→ monthly; 33 indicators

```
annual_by_region.json   region x year x indicator: quota, issuance (new/refi x general/special),
                        repayment, interest, debt limit and balance, plus GDP, budget revenue and
                        expenditure, government-fund revenue and expenditure, retail sales, trade
annual_national.json    the same indicators at national level
monthly_by_region.json  the flow indicators, monthly
prov_panel.json/.csv    tidied panel + per-year completeness flag (build_prov_debt_panel.py)
meta.json               indicator trees, fetch date, any malformed rows skipped
```

`scripts/fetch_celma.py` pulls it; `scripts/build_prov_debt_panel.py` tidies it.

**Validation.** By-region sums reproduce the national totals exactly for 2015–2024, and 2024
new-bond issuance (7,005 general + 40,188 special) matches both the national table and the
independent `parse_prov_bonds.py` appendix parse. Total 2024 local debt outstanding,
475,394 亿元, matches the 47.5 万亿 in 国务院关于2024年度政府债务管理情况的报告.

**Completeness, and how the gap is filled.** The platform carries what each region reports, so
the current year has holes. `build_prov_debt_panel.py` fills missing *issuance* from
`parse_prov_bonds.py` — the bond-by-bond appendix of the Debt Center market report, which covers
every issuer — and tags those rows `issue_source="market-report"`. The fill is a continuation of
the same figures, not a different measure: for 2025 the platform's own ZYZB summary and the
appendix parse agree to the yuan for all 32 regions that have reported. It never overwrites a
reported value.

With that, **2025 issuance is complete for all 37 issuers** and sums to 53,817 亿元 of new bonds,
matching the December 2025 market report exactly. **Quota has no second source** — only the
platform and each province's own budget report publish it, and this repo does not collect the
latter — so 10 issuers have no 2025 quota and no execution rate. The monitor states this, and
computes the aggregate execution rate only across issuers that reported both, so the ratio stays
like-for-like.

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
   principal repayment; debt outstanding (general/special) against the NPC ceiling, with
   remaining maturity, average coupon and interest paid; new special-bond YTD by year; use of new-bond proceeds (month
   selector); average maturity & secondary-market turnover; issuance YoY.

**Bridging the bond-report lag:** the Debt Center's 市场报告 for a month arrives 3–4 weeks after
MOF's own 发行和债务余额情况 release for it. `build_monitor.py` fills any month the market report
has not yet covered with the MOF release's issuance, rate, maturity and YTD figures (tagged
`src: "mof"` and footnoted on the page); secondary-market turnover and use of proceeds stay
blank until the market report lands, at which point its figures take over.

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

`data/debt-limits.json` holds the NPC-approved local-government debt ceilings (一般/专项债务限额)
by year, from the March budget reports plus the 2024-11-08 NPC Standing Committee decision that
added 6tn of special-debt ceiling. The monitor draws the ceiling for the full calendar year and
cross-checks it against the months in which MOF's debt-balance release restates it.
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
  fetch_celma.py         MOF 地方政府债券信息公开平台 → data/celma/ (province quota + issuance)
  build_prov_debt_panel.py  tidy data/celma/ into prov_panel.json/.csv (feeds the monitor's Section 4)
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

*All data and documents archived here remain the property of the issuing agencies (MOF, NBS,
PBOC, MOHRSS, NPC, provincial governments, IMF, ChinaBond) and are reproduced for
non-commercial research and educational purposes only. Derived series are the maintainer's own
calculations, not official statistics, and are provided without warranty. This project is not
affiliated with any of the bodies named. See [DISCLAIMER.md](DISCLAIMER.md) for the full
disclaimer (EN / 中文).*
