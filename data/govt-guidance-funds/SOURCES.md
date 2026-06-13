# 政府投资基金 / 地方政府引导基金 — official data sources

Government guidance funds (政府引导基金) are one class of **政府投资基金** — capital
that governments contribute, alone or alongside private capital, to make equity
investments and steer social capital toward target industries. This is a
**different accounting basis** from the "four-account" budget data tracked
elsewhere in this repo (一般公共预算 / 政府性基金预算 / 国有资本经营预算 / 社保基金预算):
there is no single ready-made MOF monthly table for it, so fund-level data has
to be assembled from registration / disclosure systems plus local announcements.

This file catalogues the **official** channels. Commercial aggregators (清科私募通,
投中 CVSource, 执中 ZERONE, Wind, 烯牛数据) repackage these sources and are far more
convenient, but are **not authoritative** — use them only for cross-checking.

---

## Policy framework (规模 / 政策 / 口径)

The regime was reset in early 2025 and the disclosure / registration sub-rules
are still being issued under it. Read these first to understand what counts as a
政府投资基金 and where official data will surface going forward.

| Document | 文号 | What it sets | Link |
|----------|------|--------------|------|
| 国务院办公厅《关于促进政府投资基金高质量发展的指导意见》 | 国办发〔2025〕1号 | The master framework. Defines 政府投资基金; assigns 财政部 (budget & state-asset management, performance, **information statistics**), 发改委 (布局规划、投向指导、评价), 证监 (登记备案监管) roles; raises 统筹管理 to the **provincial** level. | [gov.cn](https://www.gov.cn/zhengce/zhengceku/202501/content_6996730.htm) |
| 发改委《关于加强政府投资基金布局规划和投向指导的工作办法（试行）》 | 发改财金规〔2025〕1752号 | National layout planning + investment-direction guidance. | [ndrc.gov.cn](https://www.ndrc.gov.cn/xxgk/zcfb/ghxwj/202601/t20260112_1403192.html) |
| 发改委《政府投资基金投向评价管理办法（试行）》 | — | Annual **投向评价**; results to be published. | [解读 (ndrc.gov.cn)](https://www.ndrc.gov.cn/xxgk/jd/jd/202601/t20260112_1403202.html) |

> Implication: after 国办发〔2025〕1号, expect **provincial 财政厅 / 国资委** to become
> the authoritative aggregation points, and **发改委** to publish periodic
>投向评价 results. Watch 财政部 for the promised information-statistics sub-rule.

---

## Tier 1 — fund-level registries (基金明细数据)

### 1. 发改委「政府出资产业投资基金信用信息登记系统」 ⭐ most on-point
- The mandatory registry purpose-built for 政府出资产业投资基金 (includes
  government guidance funds at every level of government).
- Basis: 《政府出资产业投资基金管理暂行办法》(发改财金〔2016〕2800号) and
  《政府出资产业投资基金信用信息登记指引（试行）》— registration mandatory since
  **2017-04-01**; funds must register within 20 working days of signing the
  subscription agreement.
- Records cover: fund info, **manager**, shareholders/partners (i.e. the
  **funding structure**), custodian, and **investment information** — the most
  authoritative way to confirm whether a fund is a government guidance fund and
  what the government's contribution share is.
- Registration guidance (试行): [ndrc.gov.cn PDF](https://www.ndrc.gov.cn/xxgk/zcfb/ghxwj/202006/P020200612621032416702.pdf)
- ⚠️ Public query access is limited; the system is registration-oriented. Use it
  for verification rather than bulk extraction.

### 2. 中国证券投资基金业协会 (AMAC)「信息公示」 ⭐ most extractable
- Entry: <https://gs.amac.org.cn/> (manager query + product/备案 query).
- Most guidance funds and their sub-funds run as **filed private equity / venture
  funds**, so they must file with AMAC. You can pull: manager name, fund name,
  filing number, establish / filing dates, custodian, working state.
- The **only nationwide, structured, programmatically scrapable** source. JSON
  disclosure API lives under `https://gs.amac.org.cn/amac-infodisc/api/pof/`.
  → see [`scripts/fetch_ggf.py`](../../scripts/fetch_ggf.py) in this repo.
- Limitation: AMAC does **not** tag "government guidance fund". Identification is
  by manager/fund-name keywords (引导基金, 政府投资基金, 政府引导, 产业引导, …) and the
  funding party, so results need the NDRC registry / local announcements to confirm.

### 3. 国家企业信用信息公示系统
- Entry: <https://www.gsxt.gov.cn/>
- Guidance funds are usually limited partnerships (有限合伙企业). This shows the
  **partners (LPs), subscribed capital, and registered capital**, which confirm
  which level of finance / SOE is the funding party.

---

## Tier 2 — local first-party disclosure (最细但分散)

Provincial / municipal **财政厅(局)、国资委、地方金融管理局** sites, and the **guidance-fund
management companies' own sites** (e.g. 深圳创新投/深创投, 山东财金集团, 安徽省新兴产业引导基金,
合肥产投, 苏州元禾, 上海国投先导, 广东省半导体及集成电路产业投资基金 …) publish fund-establishment
notices, sub-fund selection results, funding lists, and annual reports. Highest
granularity, but no common format — collect province-by-province.

**Collection recipe — start from the「管理办法」.** For any region, the single richest
first document is its 引导基金 **管理办法**: it lays out the fund's structure, target
size, investment direction, and decision/exit rules. Search the local 财政厅/局 or
government portal with keyword combinations such as:

- `[省/市] 政府引导基金 管理办法` · `[省/市] 政府投资基金 管理办法`
- `[省/市] 新兴产业引导基金` · `[省/市] 产业基金 管理办法`
- `[省/市] 新旧动能转换基金` (and other locally-branded names)

Then follow the **母基金管理公司** site for sub-fund 征集公告 / 合作指南, and extend the
table region by region into a national database. Caveat: a 管理办法 describes the
fund's *design*, not its *actual* holdings or current scale — pair it with the
AMAC filing (Tier 1.2) and the 发改委 registry (Tier 1.1) for the realised picture.

---

## Quick decision guide

| You want… | Go to |
|-----------|-------|
| A scrapable nationwide list of funds/managers | AMAC 信息公示 (Tier 1.2) → `fetch_ggf.py` |
| To confirm a fund *is* a government guidance fund + the gov contribution share | 发改委 登记系统 (Tier 1.1) + 国家企业信用 (Tier 1.3) |
| Total scale / policy / 口径 for macro notes | 国办发〔2025〕1号 + 发改委 投向评价 |
| The finest detail on one province's funds | that province's 财政厅 / 国资委 / fund company site |

---

*Sources are official Chinese government / self-regulatory-body systems. This
file is a research index; always confirm a fund's classification against the
primary registry before relying on it.*
