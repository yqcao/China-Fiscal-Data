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
* **The congress's WeChat account.** Official body, non-gov domain. Worth noting
  the WeChat article has to be found as a *link on the congress's own site* —
  search engines do not index these usefully, and searching mp.weixin.qq.com
  directly returned nothing relevant for any province.
* **A lower-level government in the same province.** Municipal and district
  governments republish the provincial report in full, on their own gov.cn
  domains, and are often reachable when the provincial portal is not.

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

## What actually works when a provincial portal is blocked

Ranked by how often it paid off, from getting 20 of 31 to 30 of 31:

1. **A lower-level government in the same province.** Prefectures, counties,
   districts and departments republish the provincial report in full on their own
   gov.cn domains, and those hosts are usually reachable when the provincial
   portal is not. This alone recovered 内蒙古, 河南, 海南, 陕西, 安徽 and 甘肃.
   **Check whose report it is**: a municipal site publishes its own report too,
   and 芜湖's 5.5–6% is not 安徽's 5–5.5%. Confirm the text says 省人民政府 and
   names the provincial congress.
2. **Try a different URL on the same portal.** 青海's portal had the report all
   along under /zwgk/system/ rather than the 政府信息公开 path.
3. **Plain HTTP.** Several hosts drop TLS but answer on port 80 in two seconds.
4. **The 人大 site, then its 公报 PDF.** 四川 and 江苏 came from these.
5. **The congress's WeChat account.** 广西 only. Findable as a link on the
   congress's own site — searching mp.weixin.qq.com directly finds nothing.

Note for anyone extending this: `hnrd.gov.cn` is **Hunan**, not Henan.

## Known gaps

Not every provincial portal is reachable from outside China, and several sit
behind a WAF that rejects any non-browser client. These are recorded with a URL
in `sources.json` but have no downloaded report:

Only **江西** is missing. Its full text is demonstrably public — it sits on
several county information-disclosure pages — but every gov.cn host carrying it
either times out (`dct.jiangxi.gov.cn`, `xingguo.gov.cn`, `ncx.nc.gov.cn`,
`jiangxi.gov.cn`) or sits behind a cloud WAF that answers "站点不存在"
(`ganxian.gov.cn`). Its congress publishes through `jxnews.com.cn`, a news
domain. Browser-saving one of those pages into `raw/2026_JX.html` closes it.

To fill a gap by hand: open the URL in a browser, save the page as
`raw/2026_<CODE>.html`, and re-run `scripts/fetch_prov_reports.py`. It parses
whatever is already cached and never re-downloads it.
