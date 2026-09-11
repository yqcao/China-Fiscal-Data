"""
Shared page footer: a careful, bilingual source list plus the project disclaimer.

Every build_*.py script imports `footer()` and drops its output where the page's
<footer> used to be. The strings use the same `data-l="EN|中文"` mechanism the
pages already use for their EN/中文 toggle, so the footer follows the language
switch. Links are kept outside the data-l spans because applyL() writes
textContent.

    from page_footer import footer
    ... .replace('__FOOTER__', footer(['mof_monthly', 'debt_center'], page='fiscal-monitor.html'))
"""
import datetime, html

SITE = 'https://yqcao.github.io/China-Fiscal-Data/'
REPO = 'https://github.com/yqcao/China-Fiscal-Data'
DISCLAIMER = REPO + '/blob/main/DISCLAIMER.md'

# key -> (english, chinese, [(label, url), ...])
SOURCES = {
 'mof_monthly': (
   'Ministry of Finance of the PRC, Treasury Department, 全国财政收支情况 (monthly national fiscal revenue and expenditure release)',
   '中华人民共和国财政部国库司《全国财政收支情况》（月度）',
   [('mof.gov.cn', 'https://www.mof.gov.cn/zhengwuxinxi/redianzhuanti/quanguocaizhengshouzhiqingkuang/')]),
 'mof_annual': (
   'Ministry of Finance of the PRC, Treasury Department, 财政数据 (annual final-accounts tables)',
   '中华人民共和国财政部国库司《财政数据》（年度决算表）',
   [('gks.mof.gov.cn', 'https://gks.mof.gov.cn/tongjishuju/')]),
 'debt_center': (
   'China Government Debt Research and Evaluation Center (Ministry of Finance), 地方政府债券市场报告 (monthly local-government bond market report)',
   '财政部政府债务研究和评估中心《地方政府债券市场报告》（月度）',
   [('kjhx.mof.gov.cn', 'https://kjhx.mof.gov.cn/yjbg/')]),
 'mof_balance': (
   'Ministry of Finance of the PRC, 地方政府债券发行和债务余额情况 (monthly local-government bond issuance and debt balance release; Budget Department through 2024, Debt Management Department from December 2024)',
   '中华人民共和国财政部《地方政府债券发行和债务余额情况》（月度；2024年及以前为预算司，2024年12月起为债务管理司）',
   [('yss.mof.gov.cn', 'https://yss.mof.gov.cn/zhuantilanmu/dfzgl/sjtj/'),
    ('zwgls.mof.gov.cn', 'https://zwgls.mof.gov.cn/tjsj/')]),
 'npc_budget': (
   'National People\'s Congress, annual budget reports (关于中央和地方预算执行情况与中央和地方预算草案的报告, March each year) and the NPC Standing Committee decision of 8 November 2024 raising the local special-debt ceiling',
   '全国人民代表大会《关于中央和地方预算执行情况与中央和地方预算草案的报告》（每年三月）及全国人大常委会2024年11月8日关于增加地方政府债务限额置换存量隐性债务的决议',
   [('npc.gov.cn', 'http://www.npc.gov.cn/'), ('mof.gov.cn', 'https://www.mof.gov.cn/zhengwuxinxi/caizhengxinwen/')]),
 'nbs': (
   'National Bureau of Statistics of China, 最新发布 (monthly and quarterly statistical releases)',
   '国家统计局《最新发布》（月度、季度统计公报）',
   [('stats.gov.cn', 'https://www.stats.gov.cn/sj/zxfb/')]),
 'customs': (
   'General Administration of Customs of the PRC, 统计月报 (monthly trade statistics)',
   '中华人民共和国海关总署《统计月报》',
   [('customs.gov.cn', 'http://www.customs.gov.cn/customs/302249/zfxxgk/2799825/302274/302277/302276/index.html')]),
 'pboc': (
   'People\'s Bank of China, Statistics and Analysis Department, 统计数据 (money supply, aggregate financing, loans)',
   '中国人民银行调查统计司《统计数据》（货币供应量、社会融资规模、信贷）',
   [('pbc.gov.cn', 'http://www.pbc.gov.cn/diaochatongjisi/116219/116225/index.html')]),
 'mohrss': (
   'Ministry of Human Resources and Social Security of the PRC, 人力资源和社会保障主要统计快报数据 (monthly statistical bulletin)',
   '中华人民共和国人力资源和社会保障部《人力资源和社会保障主要统计快报数据》（月度）',
   [('mohrss.gov.cn', 'https://www.mohrss.gov.cn/SYrlzyhshbzb/zwgk/szrs/tjsj/')]),
 'chinabond': (
   'China Central Depository & Clearing Co., Ltd. (ChinaBond), 债券托管量统计月报 (bond custody by investor type)',
   '中央国债登记结算有限责任公司（中债登）《债券托管量统计月报》（按投资者类型）',
   [('chinabond.com.cn', 'https://www.chinabond.com.cn/zzsj/zzsj_tjsj/tjsj_tjyb/')]),
 'prov_reports': (
   'Each province\'s own government work report (政府工作报告), taken from that province\'s official portal, government gazette or people\'s congress site; the exact URL for every province is linked on this page',
   '各省级人民政府《政府工作报告》，取自该省官方门户、政府公报或人大网站；每省的具体来源网址已在本页链接',
   []),
 'state_council': (
   'State Council decisions and notices on central–local tax sharing, as listed in the rules table on this page',
   '国务院关于中央与地方税收收入划分的相关决定和通知，见本页规则表',
   [('gov.cn', 'https://www.gov.cn/')]),
 'imf': (
   'International Monetary Fund, People\'s Republic of China: 2025 Article IV Consultation, IMF Country Report No. 26/44 (February 2026), Table 2. © International Monetary Fund',
   '国际货币基金组织《中华人民共和国：2025年第四条款磋商》，国别报告第26/44号（2026年2月），表2。版权归国际货币基金组织所有',
   [('imf.org', 'https://www.imf.org/en/Publications/CR')]),
 'geoatlas': (
   'Province boundary geometry: DataV.GeoAtlas (Alibaba Cloud), used for drawing only',
   '省级行政区划边界几何数据：DataV.GeoAtlas（阿里云），仅用于绘图',
   [('datav.aliyun.com', 'https://datav.aliyun.com/portal/school/atlas/area_selector')]),
 'npc_observer': (
   'NPC Observer (npcobserver.com), explanatory material on the National People\'s Congress and China\'s budget process, used as background; all rights remain with NPC Observer',
   'NPC Observer（npcobserver.com）关于全国人大及预算程序的说明性材料，仅作背景参考；权利归 NPC Observer 所有',
   [('npcobserver.com', 'https://npcobserver.com/about-npc/')]),
 'echarts': (
   'Charts rendered with Apache ECharts 5.5.0 (Apache License 2.0)',
   '图表由 Apache ECharts 5.5.0 绘制（Apache 2.0 许可）',
   [('echarts.apache.org', 'https://echarts.apache.org/')]),
}

CSS = '''<style>
footer.cite{margin-top:1.8rem;padding-top:.9rem;border-top:1px solid var(--bd,#e3e3e6);font-size:.78rem;color:var(--mut,#777);line-height:1.5}
footer.cite b{font-weight:650}
footer.cite ul{margin:.25rem 0 .7rem 1.1rem;padding:0}
footer.cite li{margin:.15rem 0}
footer.cite p{margin:.4rem 0}
footer.cite a{color:var(--mut,#777)}
footer.cite code{font-size:.74rem}
</style>'''

DISC_EN = ('All data on this page remain the property of the issuing bodies listed above and are reproduced for '
           'non-commercial research and educational purposes with attribution; the authoritative figures are those at the '
           'source links. Single-month values, growth rates, shares, deficits and every other derived figure are the '
           'author\'s own calculations from the published levels, not official statistics, and may differ from the agencies\' '
           'own comparable-basis (可比口径) numbers or contain parsing errors. This page is provided as is, without warranty '
           'of any kind, and is not investment, financial or policy advice. It is an independent personal project, not '
           'affiliated with, endorsed by or speaking for any organisation named here.')
DISC_ZH = ('本页所有数据的权利均归上述发布机构所有，仅在注明出处的前提下用于非商业性研究与教育目的；以来源链接处的官方数据为准。'
           '单月值、增速、占比、赤字及其他一切衍生数据均由作者根据公布的水平值自行计算，并非官方统计，可能与机构自身的可比口径数据存在差异，'
           '也可能含有解析错误。本页按现状提供，不作任何担保，不构成投资、金融或政策建议。本项目为个人独立项目，与本页提及的任何机构均无隶属或背书关系，'
           '亦不代表其立场。')
MAP_EN = ('Maps are schematic visualisations of province-level figures. Boundaries are third-party drawing geometry, not '
          'surveyed, without a map-approval number (审图号), and imply no position on the status of any territory or boundary.')
MAP_ZH = '地图仅为省级数据的示意性可视化。边界为第三方绘图用几何数据，未经测绘核实，无审图号，不代表对任何领土或边界问题的立场。'


STATIC = None   # None: data-l toggle; 'en' / 'zh' / 'both': fixed text for pages without applyL()


def _dl(en, zh, tag='span'):
    """A bilingual element for the page's applyL() switch, or fixed text on static pages."""
    if STATIC == 'en':
        return f'<{tag}>{html.escape(en)}</{tag}>'
    if STATIC == 'zh':
        return f'<{tag}>{html.escape(zh)}</{tag}>'
    if STATIC == 'both':
        return f'<{tag}>{html.escape(en)}<br>{html.escape(zh)}</{tag}>'
    return f'<{tag} data-l="{html.escape(en, quote=True)}|{html.escape(zh, quote=True)}"></{tag}>'


def footer(keys, page, notes=None, map_page=False, extra_html='', static=None):
    """
    static    : None (page has an EN/中文 toggle) or 'en' / 'zh' / 'both' for fixed text
    keys      : SOURCES keys, in citation order
    page      : the html file name, for the suggested citation
    notes     : optional list of (en, zh) basis/caveat notes shown above the sources
    map_page  : add the map-boundary sentence
    extra_html: raw html appended after the source list (e.g. a page-specific link)
    """
    global STATIC
    STATIC = static
    today = datetime.date.today().isoformat()
    parts = [CSS, '<footer class="cite">']
    for en, zh in (notes or []):
        parts.append('<p>' + _dl(en, zh) + '</p>')
    parts.append('<p><b>' + _dl('Sources', '数据来源') + '</b></p><ul>')
    for k in keys:
        en, zh, links = SOURCES[k]
        li = _dl(en, zh)
        if links:
            li += ' · ' + ' · '.join(f'<a href="{u}" target="_blank" rel="noopener">{html.escape(l)}</a>' for l, u in links)
        parts.append('<li>' + li + '</li>')
    parts.append('</ul>')
    if extra_html:
        parts.append(extra_html)
    parts.append('<p>' + _dl('Data retrieved from the sources above and page built on ' + today + '.',
                             '数据于 ' + today + ' 自上述来源获取并生成本页。') + '</p>')
    parts.append('<p>' + _dl(DISC_EN, DISC_ZH) + '</p>')
    if map_page:
        parts.append('<p>' + _dl(MAP_EN, MAP_ZH) + '</p>')
    cite_en = (f'Suggested citation: Yongquan Cao, "China Fiscal Data: {page.replace(".html", "")}", {SITE}{page}, '
               f'built {today}; underlying data from the sources listed above.')
    cite_zh = f'建议引用格式：Yongquan Cao，《China Fiscal Data: {page.replace(".html", "")}》，{SITE}{page}，生成于 {today}；数据来源见上。'
    parts.append('<p>' + _dl(cite_en, cite_zh) + '</p>')
    parts.append('<p><a href="' + DISCLAIMER + '" target="_blank" rel="noopener">' + _dl('Full disclaimer · 免责声明', '完整免责声明 · Disclaimer') + '</a>'
                 ' · <a href="' + REPO + '" target="_blank" rel="noopener">github.com/yqcao/China-Fiscal-Data</a></p>')
    parts.append('</footer>')
    return '\n'.join(parts)
