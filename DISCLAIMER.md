# Disclaimer · 免责声明

*Last updated: 2026-09-11*

This repository and the site published from it at https://yqcao.github.io/China-Fiscal-Data/
(together, "the Project") are a personal, non-commercial research archive. By using the
Project you accept the terms below.

本仓库及其发布的网站（以下合称"本项目"）是个人的、非商业性的研究资料库。使用本项目即表示您接受以下条款。

---

## 1. Not affiliated with any government or organisation · 与任何政府机构无关

The Project is an independent effort by a private individual. It is **not** affiliated with,
endorsed by, or maintained on behalf of the Ministry of Finance of the People's Republic of
China (财政部), the National Bureau of Statistics (国家统计局), the People's Bank of China
(中国人民银行), the Ministry of Human Resources and Social Security (人力资源和社会保障部),
the National People's Congress (全国人民代表大会), any provincial government, the
International Monetary Fund, China Central Depository & Clearing Co., Ltd. (中央国债登记结算
有限责任公司), NPC Observer, Alibaba Cloud, or any other organisation named in the Project.

本项目由个人独立完成，与财政部、国家统计局、中国人民银行、人力资源和社会保障部、全国人民代表大会、
各省级人民政府、国际货币基金组织、中央国债登记结算有限责任公司、NPC Observer、阿里云或本项目中提及的
任何其他机构均无隶属、授权或代理关系，上述机构亦未对本项目作任何背书。

## 2. Ownership of the underlying data and documents · 数据与文件的权利归属

All figures, reports, tables and attachments archived here originate from the public
websites of the bodies listed in the README and in each page's source line. **The Project
claims no ownership of any of it.** Copyright and all other rights in the original releases
remain with the issuing agency or organisation. In particular:

- **Chinese government releases** (MOF, NBS, PBOC, MOHRSS, NPC, provincial governments)
  are official documents published for public information. Copies are kept here solely as a
  verbatim archival record; the authoritative version is always the one at the source URL
  recorded in the Project's `catalog.json`, `sources.json`, `INDEX.md` and `article_urls.txt`
  files.
- **IMF figures** on the augmented-debt page are transcribed from IMF Country Report
  No. 26/44 (February 2026), Table 2, © International Monetary Fund, and are reproduced for
  non-commercial research with attribution.
- **Bond-holder statistics** are from the monthly statistical releases of China Central
  Depository & Clearing Co., Ltd. (ChinaBond, 中债), which retains all rights in them.
- **Provincial boundary geometry** used for maps is from DataV.GeoAtlas (Alibaba Cloud) and is
  used only to draw choropleths. See section 5.
- **Budget-system explanatory material** draws on NPC Observer (npcobserver.com), which
  retains all rights in its text and analysis.
- The Project's charts are rendered with Apache ECharts (Apache License 2.0).

If you are a rights holder and believe any material here is reproduced beyond what is
permitted, please open a GitHub issue or contact the maintainer, and it will be removed or
replaced with a link promptly.

本项目所收录的全部数据、报告、表格及附件均来自上述机构的公开网站。**本项目不主张对其中任何内容的所有权。**
原始发布物的著作权及其他一切权利均归发布机构所有。本项目仅作原样存档，以来源网址所指向的官方版本为准。
国际货币基金组织的数据、中债登的统计月报、DataV.GeoAtlas 的行政区划边界以及 NPC Observer 的说明性材料，
其权利分别归各自权利人所有，本项目仅在注明出处的前提下用于非商业研究。如您是权利人并认为本项目的转载超出了
许可范围，请通过 GitHub issue 或直接联系维护者，本项目将及时删除或改为链接。

## 3. Derived figures are the maintainer's own calculations · 衍生数据为维护者自行计算

The official releases publish mostly cumulative year-to-date figures. Single-month values,
growth rates, shares, deficits, "fiscal impulse", execution-pace ratios, splices across
definitional breaks, the bridging of bond-market data with MOF debt-balance releases, and
every other derived series are **computed by the Project**, not published by any agency.
They may differ from an agency's own comparable-basis (可比口径) numbers and may contain
parsing or transcription errors. Structural breaks, revisions and gaps are noted where
known but are not guaranteed to be complete. Nothing here should be cited as an official
statistic; cite the original release.

官方发布多为年初至当期的累计值。本项目中的单月值、同比增速、占比、赤字、"财政脉冲"、支出进度、口径衔接、
债券市场报告与财政部债务余额数据的拼接等一切衍生序列，均由本项目自行计算，并非任何机构发布，
可能与机构自身的可比口径数据存在差异，也可能含有解析或转录错误。请勿将本项目的数据作为官方统计引用；
引用时请以原始发布为准。

## 4. No warranty; not advice · 不作担保；不构成建议

The Project is provided **"as is" and "as available", without warranty of any kind**,
express or implied, including accuracy, completeness, timeliness, merchantability, fitness
for a particular purpose, or non-infringement. Nothing in the Project constitutes
investment, financial, legal, tax or policy advice, or a recommendation to buy, sell or hold
any security, including Chinese government or local-government bonds. Any interpretation,
commentary or chart title expresses the maintainer's personal analytical view only. You use
the Project entirely at your own risk, and the maintainer accepts no liability for any loss
or damage arising from its use or from reliance on it.

本项目按"现状"及"可用"状态提供，**不作任何明示或默示的担保**，包括但不限于准确性、完整性、及时性、
适销性、特定用途适用性及不侵权。本项目的任何内容均不构成投资、金融、法律、税务或政策建议，亦不构成买卖
或持有任何证券（包括中国国债及地方政府债券）的建议。任何解读、评论或图表标题仅代表维护者的个人分析观点。
使用本项目的风险由您自行承担，维护者不对因使用或依赖本项目而产生的任何损失承担责任。

## 5. Maps · 地图

Maps in the Project are schematic visualisations of province-level statistics. Boundaries
are third-party geometry used for drawing purposes only; they are not surveyed, not
authoritative, have no map-approval number (审图号), and imply no position by the maintainer
on the status of any territory or boundary.

本项目中的地图仅为省级统计数据的示意性可视化。行政区划边界为第三方绘图用几何数据，未经测绘核实，
不具权威性，无审图号，亦不代表维护者对任何领土或边界问题的立场。

## 6. Scraping and archiving conduct · 数据采集方式

Data is collected from public pages with ordinary HTTP requests at low frequency, without
credentials, and without circumventing any access control. The Project deliberately ships
no bot-detection bypass; where a site requires a browser challenge, files are collected
manually. Large binary attachments that are freely re-downloadable from the source are not
committed to the repository.

本项目仅以低频、无凭证的普通 HTTP 请求从公开页面采集数据，不规避任何访问控制，亦不提供任何反爬虫绕过手段；
对设有浏览器验证的网站，文件由人工下载。可从来源网站自由重新下载的大体积附件不提交至仓库。

## 7. Reuse of the Project · 对本项目的再利用

You may cite, link to and reuse the Project's **code and derived JSON series** for
non-commercial research and educational purposes with attribution to this repository.
Rights in the **original documents** archived here are governed by their issuing bodies'
terms, not by the Project; obtain them from the source URL if you need them for any other
purpose. Anyone reusing Project output does so on the same "as is" basis and must carry
this disclaimer forward.

在注明出处的前提下，您可以出于非商业研究和教育目的引用、链接和再利用本项目的**代码及衍生 JSON 序列**。
本项目所存档的**原始文件**的使用受其发布机构的条款约束，与本项目无关；如需将其用于其他目的，请从来源网址获取。
任何再利用本项目产出的行为同样以"现状"为基础，且须一并载明本声明。

## 8. Changes · 变更

The maintainer may change, correct, or remove any part of the Project at any time without
notice, and may amend this disclaimer.

维护者可随时不经通知更改、更正或删除本项目的任何部分，并可修订本声明。
