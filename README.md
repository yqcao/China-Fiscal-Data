# China Fiscal Data · 中国政府预算四本账

Archived data and interactive visualizations of China's government budget system,
sourced from the Ministry of Finance (财政部).

**Live site:** https://yqcao.github.io/China-Fiscal-Data/

## Pages (GitHub Pages)

| Page | Description |
|------|-------------|
| [`index.html`](index.html) | Landing page linking the visualizations below |
| [`fiscal-monitor.html`](fiscal-monitor.html) | **Monthly Fiscal Monitor** — interactive ECharts dashboard of the general public budget and government fund budget, 2021–2026 |
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

## The Monthly Fiscal Monitor

The dashboard (`fiscal-monitor.html`) reads `fiscal_series.json` (embedded inline) and shows:

- **KPI cards** — latest general-budget revenue/expenditure, balance, and government-fund revenue
- **口径 toggle** — cumulative year-to-date (as published) ↔ derived single-month flows
- **分项 toggle** — national totals (全国) ↔ central/local split (中央/地方)
- **Charts** — general budget revenue vs expenditure; government fund + land-sale revenue;
  cumulative YoY trends; and date-selectable drill-downs of the 17 tax items and
  10 expenditure categories

**Caveat on data basis:** the MOF publishes cumulative figures (年初至当期). Single-month
values are derived by differencing consecutive reports within a year; each year's first
report covers 1–2月 combined, so January has no standalone value.

## Reproducing the archive

Both datasets were scraped from the public MOF pages listed above. The `*/INDEX.md`
and `*/article_urls.txt` files contain the canonical source URLs for every item.

---

*Data © Ministry of Finance of the People's Republic of China. This repository is an
archive and visualization for research and educational purposes.*
