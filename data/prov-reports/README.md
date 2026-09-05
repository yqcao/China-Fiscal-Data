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
| `npc` | the provincial people's congress site (Sichuan) |
| `npc-gazette` | the 人大公报, published as a PDF (Jiangsu) |
| `npc-wechat` | the congress's own WeChat account (Guangxi) — an official body, but hosted by Tencent. Used only where no gov.cn copy of the full text exists, and labelled as such. |

## Routes that work when a provincial portal does not

* **Plain HTTP.** Several provincial hosts drop TLS on port 443 but answer over
  http:// in under two seconds. Try that before concluding a host is blocked.
* **The 人大 site.** Work reports are delivered to the provincial people's
  congress, which often publishes the full text on separate infrastructure.
* **The 人大公报.** Where the congress site has no article, the gazette PDF may
  carry the report. `fetch_prov_reports.py` handles a `.pdf` URL directly,
  converting via markitdown.
* **The congress's WeChat account.** Last resort — official body, non-gov domain.

Note for anyone extending this: `hnrd.gov.cn` is **Hunan**, not Henan.

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

* WAF 403/412 on every host and scheme tried — 内蒙古 安徽 河南
* connection timeout on both the portal and the 人大 site — 海南 陕西
* page served but empty once stripped (script-rendered) — 甘肃
* 人大 site reachable, but no full text and the session documents carry no
  figures — 青海
* 人大 content served from a news domain rather than gov.cn — 江西

To fill a gap by hand: open the URL in a browser, save the page as
`raw/2026_<CODE>.html`, and re-run `scripts/fetch_prov_reports.py`. It parses
whatever is already cached and never re-downloads it.
