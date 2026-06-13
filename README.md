# China Fiscal Data · 中国政府预算四本账

Archived data and interactive visualizations of China's government budget system,
sourced from the Ministry of Finance (财政部).

**Live site:** https://yqcao.github.io/China-Fiscal-Data/

## Pages (GitHub Pages)

| Page | Description |
|------|-------------|
| [`index.html`](index.html) | Landing page linking the visualizations below |
| [`fiscal-monitor.html`](fiscal-monitor.html) | **Monthly Fiscal Monitor** — interactive ECharts dashboard: general public budget, government-managed fund, and local-government bond issuance/repayment, 2021–2026 |
| [`imf-augmented.html`](imf-augmented.html) | **IMF Augmented Debt & Deficit** — how the IMF builds China's augmented general-government debt and deficit (IMF Table 2) |
| [`budget-system.html`](budget-system.html) | China Budget System — overview of the four-account budget system (四本账) |
| [`budget-system-fy2025.html`](budget-system-fy2025.html) | China Budget System — FY2025 execution figures |

The budget-system pages draw on data from [NPC Observer](https://npcobserver.com/about-npc/).

## Datasets

### `data/mof-reports/` — 全国财政收支情况 (National Fiscal Revenue & Expenditure)

Monthly/annual fiscal reports from the MOF Treasury Department.

- **Source:** https://www.mof.gov.cn/zhengwuxinxi/redianzhuanti/quanguocaizhengshouzhiqingkuang/
- **Coverage:** 181 reports, 2008-08 → 2026-05
- **Contents:** the data is narrative text (no attachments on these pages)

```
raw/                181 original report pages (.htm)
text/               181 cleaned plain-text extractions (.txt)
listing/            9 paginated index pages
article_urls.txt    source URLs
index.json          catalog: file, date, title, url, char count
INDEX.md            human-readable, date-sorted table
fiscal_series.json  structured series parsed for the monitor page (2021–2026):
                    both budget accounts, central/local splits, 17 tax items,
                    10 expenditure categories, land-sale revenue
```

### `data/mof-research-reports/` — 研究报告 / 地方政府债券市场报告 (Local Government Bond Market Reports)

Monthly, bilingual (Chinese + English) reports from the China Government Debt Center.

- **Source:** https://kjhx.mof.gov.cn/yjbg/
- **Coverage:** 167 reports, 2019-04 → 2026-06
- **Contents:** each report is a downloadable attachment (PDF/docx)

```
listing/            17 paginated index pages
raw/                167 article wrapper pages (.htm)
files/              167 attachments — 164 PDF + 3 docx, ~208 MB (LOCAL ONLY, gitignored)
markdown/           markdown conversions of the attachments (via markitdown)
catalog.json        per-report: date, title, article, local file, size
article_urls.txt    source URLs
INDEX.md            human-readable, date-sorted table
```

> **Note:** The 208 MB of PDF/docx attachments under `files/` are **not committed**
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
- **Coverage:** repayment series 2021-01 → 2026-03

```
listing*/ raw*/        listing pages and report HTML from both sources
repayment_series.json  YTD principal repaid (亿元), split into refinancing-bond-funded
                       and fiscal-fund-funded
INDEX.md               source notes
```

### `data/govt-guidance-funds/` — 政府投资基金 / 地方政府引导基金 (government guidance funds)

A research index of **official** channels for government-guidance-fund data, plus a
scraper for the one nationwide structured source (AMAC). Note this is a different
accounting basis from the four budget accounts above — there is no ready-made MOF
monthly table, so fund-level data is assembled from registration / disclosure systems.

```
SOURCES.md       catalogue of official sources: policy framework (国办发〔2025〕1号,
                 发改委 投向评价), fund registries (发改委 登记系统, AMAC 信息公示,
                 国家企业信用), local 管理办法 search recipe, decision guide
funds.json       AMAC filings matching guidance-fund name keywords (after first run)
managers.json    distinct managers of those funds, with fund counts
INDEX.md         human-readable, date-sorted table (after first run)
major_funds.json curated scale table of the *large* national/provincial funds —
MAJOR_FUNDS.md   AMAC carries no fund size, so per-fund 规模 is hand-assembled from
                 announcements/工商/media (70 funds, every figure sourced). Two
                 columns: paidin_yi (认缴/实缴) vs target_yi (目标/规划), with a
                 scope flag (fund vs 基金群/体系) so the two口径 are never summed together.
province_scale.json  province-level *aggregate* fund scale from official disclosures —
PROVINCE_SCALE.md    all 31 provincial-level units (广东/浙江/安徽 with multi-year
                 timelines), every figure a verbatim official quote + source + 口径 tag
                 (认缴/实缴/撬动/目标/投放/只数). Bases & 母/子 levels are mixed and
                 NOT comparable — never sum or rank provinces on them. Finding: the
                 aggregate is disclosed via 财政厅公告·发布会·官方媒体·评级报告 (四川 has
                 a real 专栏; most don't; 政府工作报告 is mostly qualitative) — a curated
                 per-province recipe, not a clean auto-scrape.
sources.json     per-province recheck recipe: the canonical 财政厅/官方 page + channel
                 type + latest value, so each province's aggregate can be re-checked yearly.
evidence/        pinned evidence — text snapshots of every source page (text/*.txt,
EVIDENCE.md      committed so figures survive URL rot), manifest.json (per-URL sha256,
                 HTTP status, Wayback link, and a NUMBER-VERIFICATION flag = whether the
                 cited figure was actually found in the fetched page). 39/62 verified.
rules/           local 财政厅 「管理办法」 documents — config-driven crawler:
                 sources.json (region source pages, extend province by province),
                 catalog.json, INDEX.md, markdown/ (files/ gitignored)
```

> **Caveat:** AMAC does not tag "government guidance fund"; `fetch_ggf.py` filters by
> fund/manager name only. Confirm each hit against the 发改委 登记系统 / local
> announcements before treating it as official (see `SOURCES.md`).

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

## Updating the data (periodic refresh)

The whole pipeline is scripted under `scripts/`. The scrapers are **idempotent and
incremental** — they re-read the live listing pages, download only reports not already on
disk, re-parse everything, and regenerate the JSON series and the page.

```
scripts/
  fetch_fiscal.py      MOF 全国财政收支情况          → data/mof-reports/fiscal_series.json
  fetch_bonds.py       地方政府债券市场报告 (+PDFs)   → lgb_series.json, new_special_ytd.json
  fetch_repayment.py   地方政府债券发行和债务余额情况 → repayment_series.json
  build_monitor.py     rebuild fiscal-monitor.html from the four JSON series
  update.sh            run all of the above in order
  fetch_ggf.py         政府投资基金/引导基金 (AMAC) → data/govt-guidance-funds/funds.json
  fetch_guidance_rules.py  local 财政厅 管理办法 (config-driven) → .../rules/catalog.json
  build_major_funds.py 重点基金规模 (curated, sourced) → .../major_funds.json + MAJOR_FUNDS.md
  build_province_scale.py 省级汇总规模 (官方披露, 原型3省) → .../province_scale.json + PROVINCE_SCALE.md
```

> `fetch_ggf.py` is **not** part of `update.sh` (different cadence, and it needs
> outbound access to `gs.amac.org.cn`). Run it on its own: `python3 scripts/fetch_ggf.py`
> (incremental) or `--full` for the initial backfill. In Claude Code web sessions the
> egress allowlist blocks `gs.amac.org.cn` by default — add the host or run locally.

**To refresh after MOF publishes new monthly data:**

```bash
bash scripts/update.sh            # fetch + parse + rebuild
bash scripts/update.sh --commit   # also git commit & push (triggers the GitHub Pages rebuild)
```

Then hard-refresh the live page (GitHub Pages takes ~1–2 min to redeploy).

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
