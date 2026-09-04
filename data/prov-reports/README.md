# Provincial government work reports · 省级政府工作报告

Source policy: **every report is taken from that province's own official
`gov.cn` domain.** No aggregator, news compilation or commercial database
(北大法宝 / PKULaw and the like) is used anywhere in this pipeline.

`sources.json` records, per province per year, the URL and a `tier`:

| tier | meaning |
|---|---|
| `portal` | the province's own 政府工作报告 column or government gazette |
| `dept` | full text on a department subdomain of the same provincial government |
| `summary` | official 摘要 where the full text is not reachable (Zhejiang) |

`raw/{year}_{CODE}.html` is the page exactly as served. **It is gitignored and
local only** — these are third-party pages carrying other sites' embedded
identifiers, and one of them (a public WeChat JS-SDK appId on the Heilongjiang
portal) tripped GitHub secret scanning. `text/` is the same page with tags
stripped and IS committed; `targets.json` carries the extracted growth target
plus the sentence it came from, so every figure can still be traced back to its
report and its URL without shipping anyone else's markup.

Deleting `raw/` costs nothing but a re-fetch: `scripts/fetch_prov_reports.py`
re-downloads whatever is missing.

## Known gaps

Not every provincial portal is reachable from outside China, and several sit
behind a WAF that rejects any non-browser client. These are recorded with a URL
in `sources.json` but have no downloaded report:

* connection timeout — 江西 广西 海南 四川 陕西
* page served but empty once stripped (JS-rendered) — 甘肃 青海
* WAF 403/412 — 内蒙古 安徽 河南
* no article URL discoverable (JS-rendered index) — 江苏

To fill a gap by hand: open the URL in a browser, save the page as
`raw/2026_<CODE>.html`, and re-run `scripts/fetch_prov_reports.py`. It parses
whatever is already cached and never re-downloads it.
