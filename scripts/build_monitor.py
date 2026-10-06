import json, os
from page_footer import footer
BASIS_NOTE = [('Basis note: MOF publishes cumulative (year-to-date) figures; "Monthly" values are derived by differencing consecutive reports within a year, and each year\'s first report covers Jan–Feb combined (no standalone January). LGB figures are reported monthly in RMB billion.',
               '口径说明：财政部公布的是年初至当期的累计值；"当月"值由同一年内相邻两期报告相减得出，每年首期报告为1–2月合计（无单独的1月值）。地方政府债券数据按月公布，单位为十亿元。')]
# repo root = parent of this scripts/ directory
base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
DATA = json.dumps(json.load(open(base+'data/mof-reports/fiscal_series.json')), ensure_ascii=False, separators=(',',':'))
lgb  = json.load(open(base+'data/mof-research-reports/lgb_series.json'))
nsb  = json.load(open(base+'data/mof-research-reports/new_special_ytd.json'))
rep  = json.load(open(base+'data/mof-debt-balance/repayment_series.json'))

# The China Government Debt Center's 市场报告 (source of lgb_series) lands 3-4 weeks
# after MOF's own 发行和债务余额情况 release for the same month. Bridge the gap with
# the MOF figures (亿元 -> RMB bn) so the issuance charts and KPIs stay current;
# secondary-market turnover and use-of-proceeds only exist in the market report.
# Rows are tagged src:'mof' and the page footnotes them.
have = {(r['year'], r['month']) for r in lgb}
last = max(have)
for r in rep:
    k = (r['year'], r['month'])
    if k <= last or k in have or 'issue' not in r or 'rate' not in r: continue
    lgb.append({'year': r['year'], 'month': r['month'], 'period': r['period'],
                'issue': r['issue']/10, 'general': r['general']/10, 'special': r['special']/10,
                'new': r['new']/10, 'refi': r['refi']/10, 'rate': r['rate'], 'maturity': r['maturity'],
                'secondary': None, 'cum_issue': r.get('cum_issue', 0)/10 or None, 'use': [], 'src': 'mof'})
    if 'cum_new_special' in r and not any(n['year']==r['year'] and n['month']==r['month'] for n in nsb):
        nsb.append({'year': r['year'], 'month': r['month'], 'ytd': r['cum_new_special']/10, 'src': 'mof'})
lgb.sort(key=lambda r: (r['year'], r['month'])); nsb.sort(key=lambda r: (r['year'], r['month']))
bridged = [r['period'] for r in lgb if r.get('src') == 'mof']
if bridged: print('  bridged from MOF release:', ', '.join(bridged))

LGB  = json.dumps(lgb, ensure_ascii=False, separators=(',',':'))
NSB  = json.dumps(nsb, separators=(',',':'))
REP  = json.dumps(rep, separators=(',',':'))
HOLD = json.dumps(json.load(open(base+'data/chinabond/holders.json')), ensure_ascii=False, separators=(',',':'))
TGT  = json.dumps(json.load(open(base+'data/budget-targets.json'))['targets'], separators=(',',':'))
lim  = json.load(open(base+'data/debt-limits.json'))['limits']
LIM  = json.dumps(lim, ensure_ascii=False, separators=(',',':'))

# ---- Section 4: provincial quota vs issuance (annual) ----------------------
# data/celma/ comes from MOF's 地方政府债券信息公开平台, the only official source
# that publishes the new-debt quota allocated to each region next to that
# region's issuance. Boundaries are the Douglas-Peucker-simplified copy: the full
# DataV geometry is 569 KB and would triple this page.
_pp = json.load(open(base+'data/celma/prov_panel.json', encoding='utf-8'))
_PEN = {'北京市':'Beijing','天津市':'Tianjin','河北省':'Hebei','山西省':'Shanxi','内蒙古自治区':'Inner Mongolia',
 '辽宁省':'Liaoning','吉林省':'Jilin','黑龙江省':'Heilongjiang','上海市':'Shanghai','江苏省':'Jiangsu',
 '浙江省':'Zhejiang','安徽省':'Anhui','福建省':'Fujian','江西省':'Jiangxi','山东省':'Shandong',
 '河南省':'Henan','湖北省':'Hubei','湖南省':'Hunan','广东省':'Guangdong','广西壮族自治区':'Guangxi',
 '海南省':'Hainan','重庆市':'Chongqing','四川省':'Sichuan','贵州省':'Guizhou','云南省':'Yunnan',
 '西藏自治区':'Tibet','陕西省':'Shaanxi','甘肃省':'Gansu','青海省':'Qinghai','宁夏回族自治区':'Ningxia',
 '新疆维吾尔自治区':'Xinjiang','大连市':'Dalian','宁波市':'Ningbo','厦门市':'Xiamen','青岛市':'Qingdao',
 '深圳市':'Shenzhen','新疆生产建设兵团':'Xinjiang Corps'}
_PAR = {'大连市':'辽宁省','宁波市':'浙江省','厦门市':'福建省','青岛市':'山东省','深圳市':'广东省'}
_prow = [{'cn': r['region'], 'en': _PEN.get(r['region'], r['region']),
          'parent': _PAR.get(r['region']), 'year': r['year'],
          'quota': r['quota_total'], 'issue': r['issue_new_total'],
          'exec': r['execution_pct'], 'refi': r['issue_refi_total'],
          'bal': r['bal_total'], 'dgdp': r['debt_to_gdp_pct'], 'gdp': r['gdp'],
          'ns': r['issue_new_special'],
          'rep': ((r['repay_general'] or 0) + (r['repay_special'] or 0)) or None,
          'int': ((r['interest_general'] or 0) + (r['interest_special'] or 0)) or None,
          'src': r.get('issue_source', 'platform'),
          'qsrc': r.get('quota_source'), 'qurl': r.get('quota_url')}
         for r in _pp['rows']
         if any(r.get(k) for k in ('quota_total', 'issue_new_total', 'bal_total'))]
_pyrs = sorted({r['year'] for r in _prow})
PROV = json.dumps({'rows': _prow, 'years': _pyrs,
                   'complete': {str(y): _pp['completeness'][str(y)]['complete'] for y in _pyrs},
                   'report': {str(y): {k: _pp['completeness'][str(y)].get(k)
                                       for k in ('regions','with_issuance','with_quota','filled',
                                                 'quota_sourced','ytd_through','months')}
                              for y in _pyrs},
                   'en': _PEN,
                   'geo': json.load(open(base+'data/geo/china-provinces-min.json', encoding='utf-8'))},
                  ensure_ascii=False, separators=(',',':'))
# cross-check: where a MOF monthly release restates the NPC ceiling it must equal the NPC file
def ceiling(period):
    return max((l for l in lim if l['from'] <= period), key=lambda l: l['from'], default=None)
for r in rep:
    if 'limit' in r:
        c = ceiling(r['period'])
        if c is None or abs(c['total']-r['limit']) > 0.01 or abs(c['gen']-r['limit_gen']) > 0.01 or abs(c['spec']-r['limit_spec']) > 0.01:
            print(f"  WARNING ceiling mismatch {r['period']}: MOF release {r['limit']} vs NPC file {c and c['total']}")

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>China Fiscal Monitor · 中国月度财政运行监测</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{color-scheme:light dark;--bg:#f7f7f8;--fg:#1a1a1a;--card:#fff;--bd:#e3e3e6;--mut:#666;--accent:#c00;--up:#16a34a;--down:#dc2626;}
@media(prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#e6e6e6;--card:#1e1f23;--bd:#2c2e33;--mut:#9aa;--accent:#ff6b6b;}}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",Helvetica,Arial,sans-serif;background:var(--bg);color:var(--fg);line-height:1.5}
body.lang-en .zh{display:none}
.wrap{max-width:1080px;margin:0 auto;padding:2rem 1.1rem 4rem}
h1{font-size:1.7rem;margin:0 0 .15rem}
.zh{color:var(--mut);font-weight:400}
h1 .zh{font-size:1.05rem;display:block;margin-top:.1rem}
.sub{color:var(--mut);margin:.2rem 0 1.4rem;font-size:.9rem}
.sub a{color:var(--accent)}
.controls{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:1.3rem}
.seg{display:inline-flex;border:1px solid var(--bd);border-radius:9px;overflow:hidden;background:var(--card)}
.seg button{border:0;background:transparent;color:var(--fg);padding:.45rem .8rem;font-size:.85rem;cursor:pointer}
.seg button.on{background:var(--accent);color:#fff}
.lbl{font-size:.78rem;color:var(--mut);margin-right:.1rem}
section{margin:2.2rem 0}
.shead{border-top:2px solid var(--accent);padding-top:.7rem;margin-bottom:.8rem}
.shead h2{font-size:1.25rem;margin:0}
.shead .zh{font-size:.95rem}
.shead p{margin:.25rem 0 0;font-size:.82rem;color:var(--mut)}
.period{font-size:.9rem;color:var(--fg);margin:0 0 .7rem;font-weight:600}
.period span{color:var(--mut);font-weight:400}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:.8rem;margin-bottom:1.2rem}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:.85rem .95rem}
.kpi .t{font-size:.78rem;color:var(--mut)} .kpi .t b{color:var(--fg);font-weight:600}
.kpi .v{font-size:1.4rem;font-weight:650;margin:.15rem 0 .05rem}
.kpi .v small{font-size:.8rem;font-weight:400;color:var(--mut)}
.kpi .g{font-size:.82rem;font-weight:600;min-height:1.1em}
.up{color:var(--up)} .down{color:var(--down)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1rem .4rem;margin-bottom:1.1rem}
.card h3{font-size:.98rem;margin:.1rem 0 .15rem;font-weight:600}
.card h3 .zh{font-size:.82rem}
.card .note{font-size:.76rem;color:var(--mut);margin:0 0 .3rem}
.subhead{display:flex;align-items:center;gap:.5rem;margin:.4rem 0 .5rem;font-weight:600}
.chart{width:100%;height:330px}.chart.sm{height:300px}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem}
@media(max-width:760px){.row2{grid-template-columns:1fr}}
select{background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:8px;padding:.35rem .5rem;font-size:.82rem}
.chart.tall{height:620px}
table.ptbl{width:100%;border-collapse:collapse;font-size:.79rem}
table.ptbl th{text-align:right;font-weight:650;padding:.38rem .45rem;border-bottom:1px solid var(--bd);color:var(--mut);cursor:pointer;white-space:nowrap}
table.ptbl th:first-child,table.ptbl td:first-child{text-align:left}
table.ptbl td{padding:.32rem .45rem;border-top:1px solid var(--bd);text-align:right;white-space:nowrap}
table.ptbl tr.sub td:first-child{padding-left:1.3rem;color:var(--mut)}
#prov_partial{color:#e07b00}
footer{margin-top:1.6rem;font-size:.78rem;color:var(--mut)}footer a{color:var(--mut)}
</style>
</head>
<body class="lang-en">
<div class="wrap">
  <h1>China Fiscal Monitor <span class="zh">中国月度财政运行监测</span></h1>
  <p class="sub">Monthly fiscal operations, 2021–<span id="lastyr"></span> ·
    <a href="#sources" data-l="Sources &amp; disclaimer|数据来源与免责声明"></a></p>

  <div class="controls">
    <span class="lbl">Language</span>
    <span class="seg" id="lang"><button data-v="en" class="on">EN</button><button data-v="zh">中文</button></span>
    <span class="lbl" style="margin-left:.5rem">Basis 口径</span>
    <span class="seg" id="basis"><button data-v="cum" class="on">Cumulative YTD 累计</button><button data-v="mom">Monthly 当月</button></span>
    <span class="lbl" style="margin-left:.5rem">Breakdown 分项</span>
    <span class="seg" id="split"><button data-v="total" class="on">National 全国</button><button data-v="cl">Central / Local 中央·地方</button></span>
  </div>

  <!-- SECTION 1 -->
  <section>
    <div class="shead"><h2>1 · General Public Budget <span class="zh">一般公共预算</span></h2>
      <p>The main on-budget account: tax & non-tax revenue and government expenditure.</p></div>
    <p class="period" id="period_gen"></p>
    <div class="kpis" id="kpi_gen"></div>
    <div class="subhead"><span data-l="Budget Execution Progress · YTD by Year|预算执行进度（分年度累计）"></span></div>
    <p class="note" data-l="Cumulative YTD as % of each year's annual budget target — one line per year|各期累计执行占当年全年预算的比重——每年一条线" style="margin-top:-.3rem"></p>
    <div class="row2">
      <div class="card"><h3 data-l="Revenue|收入"></h3><div id="c_exec_gen_rev" class="chart sm"></div></div>
      <div class="card"><h3 data-l="Expenditure|支出"></h3><div id="c_exec_gen_exp" class="chart sm"></div></div>
    </div>
    <div class="subhead"><span data-l="Revenue &amp; Expenditure|收入与支出"></span></div>
    <p class="note" id="note_gen" style="margin-top:-.25rem"></p>
    <div class="row2">
      <div class="card"><h3 data-l="Revenue|收入"></h3><div id="c_gen_rev" class="chart sm"></div></div>
      <div class="card"><h3 data-l="Expenditure|支出"></h3><div id="c_gen_exp" class="chart sm"></div></div>
    </div>

    <div class="subhead"><span data-l="Major Tax Items|主要税收分项"></span> <select id="taxsel"></select></div>
    <div class="row2">
      <div class="card"><h3 data-l="Composition (level)|结构（规模）"></h3>
        <p class="note" data-l="Share of each tax in total, selected period (export rebates excluded)|各税种占比，所选期间（不含出口退税）"></p><div id="c_tax_pie" class="chart sm"></div></div>
      <div class="card"><h3 data-l="YTD Growth|累计同比增速"></h3>
        <p class="note" data-l="Year-on-year %, selected period|累计同比 %，所选期间"></p><div id="c_tax_grow" class="chart sm"></div></div>
    </div>

    <div class="subhead"><span data-l="Major Expenditure Categories|主要支出科目"></span> <select id="expsel"></select></div>
    <div class="row2">
      <div class="card"><h3 data-l="Composition (level)|结构（规模）"></h3>
        <p class="note" data-l="Share of each category in total, selected period|各科目占比，所选期间"></p><div id="c_exp_pie" class="chart sm"></div></div>
      <div class="card"><h3 data-l="YTD Growth|累计同比增速"></h3>
        <p class="note" data-l="Year-on-year %, selected period|累计同比 %，所选期间"></p><div id="c_exp_grow" class="chart sm"></div></div>
    </div>
  </section>

  <!-- SECTION 2 -->
  <section>
    <div class="shead"><h2>2 · Government-Managed Fund Budget <span class="zh">政府性基金预算</span></h2>
      <p>Earmarked fund account, dominated by state land-use-right transfer (土地出让) revenue.</p></div>
    <p class="period" id="period_fund"></p>
    <div class="kpis" id="kpi_fund"></div>
    <div class="subhead"><span data-l="Budget Execution Progress · YTD by Year|预算执行进度（分年度累计）"></span></div>
    <p class="note" data-l="Cumulative YTD as % of each year's annual budget target — one line per year|各期累计执行占当年全年预算的比重——每年一条线" style="margin-top:-.3rem"></p>
    <div class="row2">
      <div class="card"><h3 data-l="Fund Revenue|基金收入"></h3><div id="c_exec_fund_rev" class="chart sm"></div></div>
      <div class="card"><h3 data-l="Fund Expenditure|基金支出"></h3><div id="c_exec_fund_exp" class="chart sm"></div></div>
    </div>
    <div class="card"><h3>Fund Revenue, Expenditure & Land-Sale Revenue <span class="zh">基金收入·支出与土地出让收入</span></h3>
      <p class="note" id="note_fund"></p><div id="c_fund" class="chart"></div></div>
    <div class="card"><h3>Cumulative YoY Growth <span class="zh">累计同比增速</span></h3>
      <p class="note" data-l="Official year-on-year growth, % (cumulative basis)|官方累计同比增速 %"></p><div id="c_fund_yoy" class="chart sm"></div></div>
  </section>

  <!-- SECTION 3 -->
  <section>
    <div class="shead"><h2>3 · Local Government Bond Issuance <span class="zh">地方政府债券发行</span></h2>
      <p id="lgb_sub">LGB issuance from the China Government Debt Center reports, in RMB billion. The reports publish single months; the Cumulative YTD view accumulates them within each calendar year, and re-weights the rate and maturity averages by issuance rather than adding them.</p>
      <p class="note" id="lgb_prelim" hidden></p></div>
    <div class="kpis" id="kpi_lgb"></div>
    <div class="card"><h3><span id="h_lgb"></span></h3>
      <p class="note" id="note_lgb"></p><div id="c_lgb" class="chart"></div></div>
    <div class="subhead"><span data-l="Debt Service: Principal &amp; Interest|还本付息"></span></div>
    <div class="kpis" id="kpi_repay"></div>
    <div class="card"><h3 data-l="Refinancing Issuance vs Principal Repayment|再融资发行 vs 到期偿还本金"></h3>
      <p class="note" id="note_refi"></p><div id="c_lgb_refi" class="chart"></div></div>
    <div class="subhead"><span data-l="Debt Outstanding|地方政府债务余额"></span></div>
    <div class="kpis" id="kpi_bal"></div>
    <div class="card"><h3 data-l="Local Government Debt Outstanding vs NPC Ceiling|地方政府债务余额与全国人大批准限额"></h3>
      <p class="note" data-l="Month-end stock of local government debt, general vs special (bars, RMB tn), against the full-year debt ceiling approved by the NPC in its March budget report (step line; raised in Nov 2024 when the NPC Standing Committee authorised 6tn of extra special-debt ceiling for the hidden-debt swap). Non-bond legacy debt (under 0.2tn) is included in the bars. Sources: MOF 地方政府债券发行和债务余额情况 (balance); NPC budget reports and the 2024-11-08 NPCSC decision (ceiling).|月末地方政府债务余额，一般债务与专项债务堆叠（万亿元），与全国人大三月批准的全年债务限额（阶梯线）对比；2024年11月人大常委会批准增加6万亿元专项债务限额置换隐性债务，限额相应上调。非政府债券形式存量政府债务（不足0.2万亿）计入柱内。来源：财政部《地方政府债券发行和债务余额情况》（余额）；全国人大预算报告及2024年11月8日人大常委会决议（限额）。"></p><div id="c_bal" class="chart"></div></div>
    <div class="subhead"><span data-l="Who Holds the Government Bonds|政府债券持有者结构"></span></div>
    <div class="card"><p class="note" data-l="Share of each bond’s outstanding stock by holder, % (bands sum to 100). Same holder split, same order in both panels. Foreign institutions hold 4.6% of central government bonds but 0.03% of local ones — offshore money buys the sovereign, not the province.|按持有机构划分的存量占比，%（合计 100）。两图口径与顺序一致。境外机构持有国债 4.6%，持有地方债仅 0.03%。"></p></div>
    <div class="row2">
      <div class="card"><h3 data-l="Central Government Bonds (CGB)|国债"></h3><div id="c_hold_cgb" class="chart sm"></div></div>
      <div class="card"><h3 data-l="Local Government Bonds (LGB)|地方政府债"></h3><div id="c_hold_lgb" class="chart sm"></div></div>
    </div>
    <div class="card"><h3 data-l="New Special-Bond Issuance, YTD by Year|新增专项债发行（年初至今，分年度）"></h3>
      <p class="note" data-l="Cumulative new special-bond issuance through each month; one line per year (RMB bn)|累计新增专项债发行，每年一条线（十亿元）"></p><div id="c_lgb_ytd" class="chart"></div></div>
    <div class="subhead"><span data-l="Use of New-Bond Proceeds (investment targets)|新增债券资金投向"></span> <select id="lgbsel"></select></div>
    <div class="card"><p class="note" id="note_use"></p><div id="c_lgb_use" class="chart"></div></div>
    <div class="row2">
      <div class="card"><h3 data-l="Average Maturity & Secondary-Market Turnover|平均期限与二级市场现券交易"></h3>
        <p class="note" id="note_lgb2"></p><div id="c_lgb2" class="chart sm"></div></div>
      <div class="card"><h3 data-l="Issuance YoY Growth|发行额同比增速"></h3>
        <p class="note" id="note_lgb_yoy"></p><div id="c_lgb_yoy" class="chart sm"></div></div>
    </div>
  </section>

  <!-- SECTION 4 -->
  <section>
    <div class="shead"><h2>4 · Provincial Quota &amp; Execution <span class="zh">各省新增债务限额与发行</span></h2>
      <p id="prov_sub"></p>
      <p class="note" id="prov_partial" hidden></p></div>
    <div class="controls" style="margin-bottom:.9rem">
      <span class="lbl" data-l="Year|年份"></span>
      <select id="provyear"></select>
      <span class="lbl" style="margin-left:.5rem" data-l="Map shows|地图指标"></span>
      <span class="seg" id="provmetric">
        <button data-v="exec" class="on" data-l="Execution %|执行率 %"></button>
        <button data-v="quota" data-l="Quota|限额"></button>
        <button data-v="dgdp" data-l="Debt / GDP|债务率"></button>
      </span>
    </div>
    <div class="kpis" id="kpi_prov"></div>
    <div class="row2">
      <div class="card"><h3 id="h_provmap"></h3>
        <p class="note" data-l="Annual, not monthly: the quota is set once a year. The five 计划单列市 and the XPCC issue separately and have no boundary of their own, so the map folds them into their province and the table keeps them apart.|年度数据（限额按年下达）。五个计划单列市与新疆生产建设兵团单独发行且无独立边界，地图并入所属省份，表格单列。"></p>
        <div id="c_provmap" class="chart"></div></div>
      <div class="card"><h3 data-l="Quota vs issuance, ranked|限额与发行额排序"></h3>
        <p class="note" data-l="Pale bar = quota allocated, solid bar = new bonds issued. A short solid bar inside a long pale one is unused quota. Refinancing is excluded: it rolls maturing debt and replaces hidden debt, and is not measured against the new-debt quota. Issuance above quota is not a breach: 结存限额, unused ceiling carried over from earlier years, is allocated separately and can be issued on top. Jiangsu 2025 is the clean example — it issued 2,785 of new special bonds against a 2,485 quota, and the 300 difference is exactly the carried-over tranche its November 2025 budget-adjustment report records.|浅色柱为下达限额，实色柱为实际新增发行；实色明显短于浅色即限额未用完。不含再融资（用于偿还到期债券及置换隐性债务，不计入新增限额执行率）。发行额超过限额并非超限：往年未用完的结存限额单独下达，可在新增限额之外发行。以江苏2025年为例，新增专项债发行2785亿元、新增限额2485亿元，差额300亿元恰为该省2025年11月预算调整报告所载的结存限额。"></p>
        <div id="c_provbar" class="chart tall"></div></div>
    </div>
    <div class="card"><h3 data-l="Debt burden vs quota execution|债务率与限额执行率"></h3>
      <p class="note" data-l="Debt outstanding as % of provincial GDP (x) against the share of the new-debt quota issued (y); bubble area = quota size. The provinces leaving quota unused are not the least indebted ones.|债务余额占本省GDP比重（横轴）与新增限额执行率（纵轴）；气泡面积为限额规模。未用完限额的并非债务率最低的省份。"></p>
      <div id="c_provsc" class="chart"></div></div>
    <div class="card"><h3 data-l="All issuers|全部发行主体"></h3>
      <p class="note" data-l="Click a column heading to sort. 亿元 unless marked. † = issuance taken from the Debt Center market report, ‡ = quota taken from that region&#39;s own budget report, both where the disclosure platform has no entry.|点击表头排序。单位亿元（另有标注除外）。† 发行额取自债务中心市场报告；‡ 限额取自该地区预算报告；均因平台无该项数据。"></p>
      <div style="overflow-x:auto"><table class="ptbl" id="provtbl"></table></div></div>
  </section>

__FOOTER__
</div>

<script>
const DATA = __DATA__;
const LGB  = __LGB__;
const NSB  = __NSB__;
const REP  = __REP__;
const HOLD = __HOLD__;
const TGT  = __TGT__;
const PROV = __PROV__;

const LIM  = __LIM__;
// Unify units: MOF fiscal figures are in 亿元 — convert to RMB billion (十亿元, ÷10).
const MFIELDS=['pub_rev','tax','nontax','pub_rev_central','pub_rev_local','pub_exp','pub_exp_central','pub_exp_local','fund_rev','land_rev','fund_exp'];
DATA.forEach(r=>{MFIELDS.forEach(k=>{if(r[k]&&r[k].v!=null)r[k].v=+(r[k].v/10).toFixed(2);});
  (r.tax_items||[]).forEach(i=>i.v=+(i.v/10).toFixed(2));
  (r.tax_sub||[]).forEach(i=>i.v=+(i.v/10).toFixed(2));   // same units as tax_items
  (r.exp_items||[]).forEach(i=>i.v=+(i.v/10).toFixed(2));});

const dark=matchMedia('(prefers-color-scheme: dark)').matches;
const AX=dark?'#9aa':'#666',GRID=dark?'#2c2e33':'#eee',FG=dark?'#e6e6e6':'#1a1a1a',CARD=dark?'#1e1f23':'#fff';
const C={rev:'#c00',exp:'#1463ff',fund:'#e07b00',land:'#0a9d6b',gen:'#1463ff',spec:'#c00',rate:'#e07b00',mat:'#0a9d6b'};
const PIE=['#c00','#1463ff','#e07b00','#0a9d6b','#7c4dff','#d81b60','#00838f','#5d4037','#558b2f','#ef6c00','#3949ab','#00897b','#c2185b','#6d4c41','#1e88e5','#43a047','#8e24aa'];
const charts={}; const mk=id=>charts[id]=echarts.init(document.getElementById(id));
const fmtB=v=>v==null?'–':(Math.abs(v)>=1000?'RMB '+(v/1000).toFixed(2)+'tn':'RMB '+Math.round(v).toLocaleString()+'bn');
const fmtT=v=>v==null?'–':'RMB '+(v/1000).toFixed(2)+'tn';
const gtxt=g=>g==null?'':(g>=0?'+':'')+g+'%';
let lang='en', basis='cum', split='total';
const L=(en,zh)=>lang==='en'?en:zh;
document.getElementById('lastyr').textContent=DATA[DATA.length-1].year;
const periods=DATA.map(r=>r.period);
const MON=['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function perEN(r){ if(r.month===12&&/^\d{4}年财政收支情况/.test(r.title)) return 'FY'+r.year; return 'Jan–'+MON[r.month]+' '+r.year; }
function perZH(r){ return r.title.replace('财政收支情况',''); }

// English names for tax / expenditure items (matched by keyword; order = specific first)
const NAMES=[
 [/出口/,'Export Tax Rebate'],[/进口货物增值税/,'Import VAT & Excise'],[/关税/,'Customs Duty'],[/国内增值税/,'Domestic VAT'],
 [/国内消费税/,'Domestic Excise'],[/企业所得税/,'Corporate Income Tax'],[/个人所得税/,'Individual Income Tax'],
 [/城市维护建设税/,'Urban Maint. & Constr. Tax'],[/车辆购置税/,'Vehicle Purchase Tax'],[/印花税/,'Stamp Tax'],
 [/资源税/,'Resource Tax'],[/契税/,'Deed Tax'],[/房产税/,'Property Tax'],[/城镇土地使用税/,'Urban Land-Use Tax'],
 [/土地增值税/,'Land Appreciation Tax'],[/耕地占用税/,'Farmland Occupation Tax'],[/环境保护税/,'Environmental Tax'],
 [/车船税|船舶吨税|烟叶税|其他/,'Other Taxes'],
 [/教育/,'Education'],[/科学技术/,'Science & Tech'],[/文化/,'Culture, Tourism & Media'],
 [/社会保障和就业/,'Social Security & Employment'],[/卫生健康|医疗卫生/,'Health'],[/节能环保/,'Energy & Environment'],
 [/城乡社区/,'Urban & Rural Community'],[/农林水/,'Agric., Forestry & Water'],[/交通运输/,'Transportation'],
 [/债务付息/,'Debt Interest']];
function enName(cn){ for(const[re,en]of NAMES) if(re.test(cn)) return en; return cn; }
const nm=cn=>lang==='en'?enName(cn):cn;
// short abbreviations for compact pie/bar labels (English mode)
const ABBR={'国内增值税':'VAT','国内消费税':'Excise','企业所得税':'CIT','个人所得税':'PIT',
 '进口货物增值税、消费税':'Import VAT&Excise','关税':'Customs','出口退税':'Export Rebate',
 '城市维护建设税':'City Maint.','车辆购置税':'Vehicle Purch.','印花税':'Stamp','资源税':'Resource',
 '契税':'Deed','房产税':'Property','城镇土地使用税':'Land-Use','土地增值税':'LAT','耕地占用税':'Farmland',
 '环境保护税':'Env. Tax','其他税收':'Other',
 '教育支出':'Education','科学技术支出':'Sci-Tech','文化旅游体育与传媒支出':'Culture','社会保障和就业支出':'Soc. Security',
 '卫生健康支出':'Health','节能环保支出':'Energy/Env.','城乡社区支出':'Community','农林水支出':'Agri-Water',
 '交通运输支出':'Transport','债务付息支出':'Debt Int.'};
const shortNm=cn=>lang==='en'?(ABBR[cn]||enName(cn)):cn;

function monthly(field){
  const byY={}; DATA.forEach(r=>{const o=r[field]; if(o)(byY[r.year]=byY[r.year]||[]).push({m:r.month,v:o.v});});
  const flow={}; Object.entries(byY).forEach(([y,a])=>{a.sort((x,z)=>x.m-z.m);let p=0;a.forEach((x,i)=>{flow[y+'-'+x.m]=i===0?x.v:+(x.v-p).toFixed(1);p=x.v;});});
  const out={}; DATA.forEach(r=>{if(!r[field])return;const c=flow[r.year+'-'+r.month],py=flow[(r.year-1)+'-'+r.month];
    out[r.period]={v:c,g:(py!=null&&py!==0)?+((c/py-1)*100).toFixed(1):null};}); return out;
}
function series(field,b){ if(b==='cum') return DATA.map(r=>r[field]?{v:r[field].v,g:r[field].g}:{v:null,g:null});
  const m=monthly(field); return DATA.map(r=>m[r.period]?m[r.period]:{v:null,g:null}); }

function kpi(el,cards){document.getElementById(el).innerHTML=cards.map(([t,zh,val,sub,g])=>{
  const gg=g!=null?`<div class="g ${g>=0?'up':'down'}">${gtxt(g)} YoY</div>`:'<div class="g"></div>';
  return `<div class="kpi"><div class="t"><b>${t}</b> <span class="zh">${zh}</span></div><div class="v">${val} ${sub?`<small>${sub}</small>`:''}</div>${gg}</div>`;}).join('');}

const baseX=()=>({type:'category',data:periods,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}});

function drawPanel(id,kind){
  const isRev=kind==='rev', col=isRev?C.rev:C.exp, ycol=isRev?'#7a0010':'#0a3a8a';
  let bars;
  if(split==='total') bars=[{f:isRev?'pub_rev':'pub_exp',n:isRev?['Revenue','收入']:['Expenditure','支出'],c:col}];
  else bars=isRev?[{f:'pub_rev_central',n:['Central','中央'],c:'#c00'},{f:'pub_rev_local',n:['Local','地方'],c:'#ff8a8a'}]
                 :[{f:'pub_exp_central',n:['Central','中央'],c:'#1463ff'},{f:'pub_exp_local',n:['Local','地方'],c:'#8ab4ff'}];
  const sers=bars.map(b=>({name:L(b.n[0],b.n[1]),type:'bar',stack:'lv',itemStyle:{color:b.c,opacity:.85},data:series(b.f,basis).map(x=>x.v)}));
  sers.push({name:L('YoY %','同比 %'),type:'line',yAxisIndex:1,smooth:true,showSymbol:false,symbol:'circle',symbolSize:4,lineStyle:{width:2.2,color:ycol},itemStyle:{color:ycol},data:series(isRev?'pub_rev':'pub_exp',basis).map(d=>d.g)});
  charts[id].setOption({grid:{left:48,right:46,top:28,bottom:48},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:sers.map(s=>s.name)},
    tooltip:{trigger:'axis',formatter:ps=>ps[0].axisValue+'<br>'+ps.map(p=>p.marker+p.seriesName+': '+(/YoY|同比/.test(p.seriesName)?(p.value==null?'–':p.value+'%'):fmtT(p.value))).join('<br>')},
    xAxis:baseX(),
    yAxis:[{type:'value',name:'RMB tn',alignTicks:true,axisLabel:{color:AX,formatter:v=>(v/1000).toFixed(0)},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
           {type:'value',name:'YoY %',alignTicks:true,axisLabel:{color:AX,formatter:'{value}%'},splitLine:{show:false},nameTextStyle:{color:AX}}],
    series:sers},true);
}
function drawGen(){
  document.getElementById('note_gen').textContent=L(
    basis==='cum'?'Cumulative YTD level (RMB tn, left) + YoY growth (%, right)':'Single-month flow (RMB tn, left) + YoY growth (%, right)',
    basis==='cum'?'累计（万亿元，左）+ 同比（%，右）':'当月（万亿元，左）+ 同比（%，右）');
  drawPanel('c_gen_rev','rev'); drawPanel('c_gen_exp','exp');
}

function drawFund(){
  document.getElementById('note_fund').textContent=L(basis==='cum'?'Cumulative YTD, RMB bn':'Derived single-month, RMB bn',basis==='cum'?'累计，十亿元':'当月推算，十亿元');
  const rev=series('fund_rev',basis),exp=series('fund_exp',basis),land=series('land_rev',basis);
  const other=rev.map((d,i)=>(d.v!=null&&land[i].v!=null)?+(d.v-land[i].v).toFixed(1):d.v);
  charts.c_fund.setOption({grid:{left:60,right:18,top:30,bottom:48},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('Land-Sale Revenue','土地出让收入'),L('Other Fund Revenue','其他基金收入'),L('Fund Expenditure','基金支出')]},
    tooltip:{trigger:'axis',valueFormatter:fmtB},
    xAxis:baseX(),
    yAxis:{type:'value',name:'RMB bn',axisLabel:{color:AX,formatter:v=>v>=1000?(v/1000)+'tn':v},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    series:[{name:L('Land-Sale Revenue','土地出让收入'),type:'bar',stack:'rev',itemStyle:{color:C.land,opacity:.9},data:land.map(d=>d.v)},
      {name:L('Other Fund Revenue','其他基金收入'),type:'bar',stack:'rev',itemStyle:{color:C.fund,opacity:.85},data:other},
      {name:L('Fund Expenditure','基金支出'),type:'bar',itemStyle:{color:'#9aa',opacity:.55},data:exp.map(d=>d.v)}]},true);
}
// Execution by year: cumulative YTD as % of that year's annual target — one line per year.
const EXECPAL={2021:'#9aa',2022:'#0a9d6b',2023:'#1463ff',2024:'#e07b00',2025:'#7c4dff',2026:'#c00'};
function drawExecYear(id,key){
  const years=[...new Set(DATA.map(r=>r.year))].filter(y=>TGT[y]).sort();
  const maxY=Math.max(...years);
  const sers=years.map(y=>({name:''+y,type:'line',smooth:true,connectNulls:true,showSymbol:true,symbolSize:4,
    lineStyle:{width:y===maxY?2.8:1.6,color:EXECPAL[y]||'#888'},itemStyle:{color:EXECPAL[y]||'#888'},
    data:Array.from({length:12},(_,i)=>{const r=DATA.find(x=>x.year===y&&x.month===i+1),t=TGT[y];
      return (r&&r[key]&&t&&t[key]!=null)?+(r[key].v/(t[key]/10)*100).toFixed(1):null;})}));
  sers[0].markLine={silent:true,symbol:'none',lineStyle:{color:AX,type:'dashed',opacity:.4},
    data:[{yAxis:100,label:{formatter:'100%',color:AX,fontSize:9,position:'insideEndTop'}}]};
  charts[id].setOption({grid:{left:46,right:16,top:28,bottom:34},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:years.map(String)},
    tooltip:{trigger:'axis',valueFormatter:v=>v==null?'–':v+'%'},
    xAxis:{type:'category',data:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],axisLabel:{color:AX},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',name:'% of budget',axisLabel:{color:AX,formatter:'{value}%'},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    series:sers},true);
}
function yoyChart(id,fields){charts[id].setOption({grid:{left:48,right:18,top:28,bottom:48},textStyle:{color:FG},
  legend:{top:0,textStyle:{color:AX},data:fields.map(f=>L(f[1],f[2]))},tooltip:{trigger:'axis',valueFormatter:v=>v==null?'–':v+'%'},
  xAxis:baseX(),yAxis:{type:'value',name:'%',axisLabel:{color:AX,formatter:'{value}%'},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
  series:fields.map(f=>({name:L(f[1],f[2]),type:'line',smooth:true,showSymbol:false,lineStyle:{width:2,color:f[3]},itemStyle:{color:f[3]},data:DATA.map(r=>r[f[0]]?r[f[0]].g:null)}))},true);}

function fillSel(id){const s=document.getElementById(id);const cur=s.value;s.innerHTML='';
  DATA.slice().reverse().forEach(r=>{if((r.tax_items||[]).length){const o=document.createElement('option');o.value=r.period;o.textContent=lang==='en'?perEN(r):(r.period+' '+perZH(r));s.appendChild(o);}});
  if(cur)s.value=cur;}

function drawComposition(pieId,growId,field,period){
  const r=DATA.find(x=>x.period===period)||DATA[DATA.length-1];
  const items=r[field];
  const pieItems=items.filter(i=>!/退/.test(i.name)).slice().sort((a,b)=>b.v-a.v);
  const tot=pieItems.reduce((s,i)=>s+i.v,0);
  charts[pieId].setOption({textStyle:{color:FG},color:PIE,
    tooltip:{trigger:'item',formatter:p=>nm(p.name)+'<br>'+fmtB(p.value)+' ('+p.percent+'%)'},
    series:[{type:'pie',radius:['34%','64%'],center:['50%','52%'],minShowLabelAngle:0,
      label:{color:FG,fontSize:9.5,formatter:p=>shortNm(p.name)+' '+p.percent+'%'},
      labelLine:{length:5,length2:5},
      data:pieItems.map(i=>({name:i.name,value:i.v}))}]},true);
  const g=items.slice().sort((a,b)=>(b.g??-999)-(a.g??-999));
  charts[growId].setOption({grid:{left:108,right:48,top:8,bottom:22},textStyle:{color:FG},
    tooltip:{trigger:'item',formatter:p=>nm(g[p.dataIndex].name)+'：'+gtxt(g[p.dataIndex].g)+'  ('+fmtB(g[p.dataIndex].v)+')'},
    xAxis:{type:'value',axisLabel:{color:AX,formatter:'{value}%'},splitLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'category',inverse:true,data:g.map(i=>shortNm(i.name)),axisLabel:{color:AX,fontSize:11}},
    series:[{type:'bar',data:g.map(i=>({value:i.g,itemStyle:{color:i.g>=0?C.up:C.down}})),
      label:{show:true,position:'right',color:AX,fontSize:10,formatter:p=>gtxt(g[p.dataIndex].g)}}]},true);
}

function drawNSB(){
  const years=[...new Set(NSB.map(r=>r.year))].sort();
  const pal={2021:'#9aa',2022:'#0a9d6b',2023:'#1463ff',2024:'#e07b00',2025:'#7c4dff',2026:'#c00'};
  const sers=years.map(y=>({name:''+y,type:'line',smooth:true,connectNulls:true,showSymbol:true,symbolSize:4,
    lineStyle:{width:y===Math.max(...years)?2.8:1.8,color:pal[y]||'#888'},itemStyle:{color:pal[y]||'#888'},
    data:Array.from({length:12},(_,i)=>{const r=NSB.find(x=>x.year===y&&x.month===i+1);return r?r.ytd:null;})}));
  charts.c_lgb_ytd.setOption({grid:{left:56,right:18,top:28,bottom:36},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:years.map(String)},
    tooltip:{trigger:'axis',valueFormatter:v=>v==null?'–':fmtB(v)},
    xAxis:{type:'category',data:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],axisLabel:{color:AX},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',name:'RMB bn',axisLabel:{color:AX,formatter:v=>v>=1000?(v/1000)+'tn':v},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    series:sers},true);
}
const lgbP=LGB.map(r=>r.period);
/* Year-to-date view of the bond series. The market report publishes single
   months, so YTD is accumulated within each calendar year; the reported
   cum_issue is used for the total where it exists (it agrees with the running
   sum to a rounding cent). Rates and maturities are averages, not sums, so they
   are re-weighted by issuance rather than added. */
function lgbCum(field){const run={},out=[];
  LGB.forEach(r=>{const v=r[field];
    if(v==null){out.push(run[r.year]==null?null:+run[r.year].toFixed(2));return;}
    run[r.year]=(run[r.year]||0)+v; out.push(+run[r.year].toFixed(2));});
  return out;}
function lgbCumIssue(){const c=lgbCum('issue');
  return LGB.map((r,i)=>r.cum_issue!=null?r.cum_issue:c[i]);}
function lgbWtd(field){/* issuance-weighted average to date, within the year */
  const num={},den={},out=[];
  LGB.forEach(r=>{const v=r[field],w=r.issue;
    if(v!=null&&w!=null){num[r.year]=(num[r.year]||0)+v*w; den[r.year]=(den[r.year]||0)+w;}
    out.push(den[r.year]?+(num[r.year]/den[r.year]).toFixed(2):null);});
  return out;}
function lgbVals(field){
  if(basis==='mom')return LGB.map(r=>r[field]);
  if(field==='issue')return lgbCumIssue();
  if(field==='rate'||field==='maturity')return lgbWtd(field);
  return lgbCum(field);}
function lgbYoY(){
  if(basis==='mom'){const by={};LGB.forEach(r=>by[r.year+'-'+r.month]=r.issue);
    return LGB.map(r=>{const py=by[(r.year-1)+'-'+r.month];return py?+((r.issue/py-1)*100).toFixed(1):null;});}
  const c=lgbCumIssue(),by={};LGB.forEach((r,i)=>by[r.year+'-'+r.month]=c[i]);
  return LGB.map(r=>{const py=by[(r.year-1)+'-'+r.month],cu=by[r.year+'-'+r.month];
    return(py&&cu)?+((cu/py-1)*100).toFixed(1):null;});}
function drawLGB(){
  charts.c_lgb.setOption({grid:{left:56,right:56,top:30,bottom:48},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('General','一般债'),L('Special','专项债'),L('Avg Rate','平均利率')]},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},xAxis:{type:'category',data:lgbP,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    yAxis:[{type:'value',name:'RMB bn',axisLabel:{color:AX},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
           {type:'value',name:'%',axisLabel:{color:AX,formatter:'{value}%'},splitLine:{show:false},nameTextStyle:{color:AX}}],
    series:[{name:L('General','一般债'),type:'bar',stack:'b',itemStyle:{color:C.gen},data:lgbVals('general')},
      {name:L('Special','专项债'),type:'bar',stack:'b',itemStyle:{color:C.spec},data:lgbVals('special')},
      {name:L('Avg Rate','平均利率'),type:'line',yAxisIndex:1,smooth:true,showSymbol:false,lineStyle:{width:2.4,color:C.rate},itemStyle:{color:C.rate},data:lgbVals('rate')}]},true);
  charts.c_lgb2.setOption({grid:{left:54,right:56,top:30,bottom:48},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('Avg Maturity','平均期限'),L('Secondary Turnover','二级市场交易')]},tooltip:{trigger:'axis'},
    xAxis:{type:'category',data:lgbP,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    yAxis:[{type:'value',name:L('years','年'),axisLabel:{color:AX},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
           {type:'value',name:'RMB bn',axisLabel:{color:AX},splitLine:{show:false},nameTextStyle:{color:AX}}],
    series:[{name:L('Secondary Turnover','二级市场交易'),type:'bar',yAxisIndex:1,itemStyle:{color:'#8ab4ff',opacity:.75},data:lgbVals('secondary')},
      {name:L('Avg Maturity','平均期限'),type:'line',smooth:true,showSymbol:false,lineStyle:{width:2.4,color:C.mat},itemStyle:{color:C.mat},data:lgbVals('maturity')}]},true);
  const yo=lgbYoY();
  charts.c_lgb_yoy.setOption({grid:{left:48,right:18,top:18,bottom:48},textStyle:{color:FG},tooltip:{trigger:'axis',valueFormatter:v=>v==null?'–':v+'%'},
    xAxis:{type:'category',data:lgbP,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',name:'%',axisLabel:{color:AX,formatter:'{value}%'},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    series:[{type:'line',smooth:true,showSymbol:false,lineStyle:{width:2,color:C.spec},itemStyle:{color:C.spec},data:yo,areaStyle:{opacity:.06,color:C.spec}}]},true);
  drawRefiRepay();drawHolders();
}
function drawRefiRepay(){
  // monthly principal repayment derived from YTD (亿 -> RMB bn); only diff consecutive months
  const ytdRefi={},ytdFisc={};
  REP.forEach(r=>{ytdRefi[r.period]=r.repay_refi_ytd; ytdFisc[r.period]=r.repay_fisc_ytd;});
  const pk=r=>r.year+'-'+String(r.month-1).padStart(2,'0');
  const mdiff=(map,r)=>{const c=map[r.period]; if(c==null)return null; if(r.month===1)return c; const p=map[pk(r)]; return p==null?null:+(c-p).toFixed(0);};
  const P=REP.map(r=>r.period), toB=v=>v==null?null:+(v/10).toFixed(1);
  const cum=basis==='cum';
  const repRefi=REP.map(r=>toB(cum?ytdRefi[r.period]:mdiff(ytdRefi,r)));
  const repFisc=REP.map(r=>toB(cum?ytdFisc[r.period]:mdiff(ytdFisc,r)));
  const refiAll=lgbVals('refi');
  const refiIss=P.map(p=>{const i=LGB.findIndex(x=>x.period===p);return i<0?null:refiAll[i];});
  // interest is published as a YTD figure with the month alongside it
  const interest=REP.map(r=>toB(cum?r.interest_ytd:r.interest_month));
  repayKpis(repRefi,repFisc,refiIss,interest);
  charts.c_lgb_refi.setOption({grid:{left:56,right:18,top:30,bottom:48},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('Repaid via refinancing','再融资偿还'),L('Repaid via fiscal funds','财政资金偿还'),L('Refinancing issuance','再融资发行'),L('Interest paid','付息')]},
    tooltip:{trigger:'axis',valueFormatter:v=>v==null?'–':'RMB '+v+'bn'},
    xAxis:{type:'category',data:P,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',name:'RMB bn',axisLabel:{color:AX,formatter:v=>v>=1000?(v/1000)+'tn':v},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    series:[
      {name:L('Repaid via refinancing','再融资偿还'),type:'bar',stack:'rp',itemStyle:{color:'#7c4dff'},data:repRefi},
      {name:L('Repaid via fiscal funds','财政资金偿还'),type:'bar',stack:'rp',itemStyle:{color:'#c9a96b'},data:repFisc},
      {name:L('Refinancing issuance','再融资发行'),type:'line',smooth:true,showSymbol:false,lineStyle:{width:2.4,color:'#0a9d6b'},itemStyle:{color:'#0a9d6b'},data:refiIss},
      {name:L('Interest paid','付息'),type:'line',smooth:true,showSymbol:false,lineStyle:{width:2,color:'#e07b00',type:'dashed'},itemStyle:{color:'#e07b00'},data:interest}]},true);
}
const USESHORT=[[/municipal.*industrial park/i,'Municipal & industrial-park infra'],[/transportation/i,'Transportation infra'],
 [/land reserve/i,'Land reserve'],[/social undertaking/i,'Social undertaking'],
 [/housing.*urban renewal|subsidized housing/i,'Affordable housing & urban renewal'],[/ecolog/i,'Ecology & environment'],
 [/forward-looking|strategic emerging/i,'Strategic emerging industries'],[/warehouse logistic/i,'Warehouse logistics'],
 [/new infrastructure/i,'New infrastructure'],[/^energy$/i,'Energy'],[/purchase existing|existing commercial housing/i,'Buy existing housing'],
 [/agricultur|forestry|water/i,'Agriculture, forestry & water'],[/health/i,'Healthcare'],[/educat/i,'Education'],
 [/^others?$/i,'Others']];
function useShort(f){for(const[re,s]of USESHORT)if(re.test(f))return s; return f.charAt(0).toUpperCase()+f.slice(1);}
// Holder composition of the government-bond stock, from the CCDC monthly.
// One panel per bond type, identical buckets and identical band order, so the
// two read against each other positionally rather than by hunting the legend.
// Hues are assigned in the fixed documented order — never re-ordered per panel.
const HOLDCAT=[
  {k:['banks'],                       en:'Commercial banks',  zh:'商业银行',   l:'#2a78d6', d:'#3987e5'},
  {k:['products'],                    en:'Funds & WMPs',      zh:'非法人产品', l:'#eb6834', d:'#d95926'},
  {k:['other_interbank','credit_unions'], en:'Other interbank', zh:'其他银行间', l:'#1baf7a', d:'#199e70'},
  {k:['insurance'],                   en:'Insurance',         zh:'保险机构',   l:'#eda100', d:'#c98500'},
  {k:['foreign'],                     en:'Foreign',           zh:'境外机构',   l:'#e87ba4', d:'#d55181'},
  {k:['securities'],                  en:'Securities firms',  zh:'证券公司',   l:'#008300', d:'#008300'},
  {k:['counter','other_market'],      en:'Exchange & OTC',    zh:'交易所及柜台', l:'#4a3aa7', d:'#9085e9'}];
function drawHolders(){
  [['c_hold_cgb','cgb'],['c_hold_lgb','lgb']].forEach(([id,bond])=>{
    const H=HOLD.filter(r=>r[bond]&&r[bond].total), P=H.map(r=>r.period), pick=c=>dark?c.d:c.l;
    const series=HOLDCAT.map((c,i)=>({
      name:L(c.en,c.zh), type:'line', stack:'h', showSymbol:false, emphasis:{focus:'series'},
      // band edge drawn in the card colour: a 2px surface gap, not a dark rule
      lineStyle:{width:2,color:CARD}, areaStyle:{color:pick(c),opacity:1}, itemStyle:{color:pick(c)},
      // only the bottom band is direct-labelled: its top edge equals its own
      // share, so the number is unambiguous on a cumulative axis
      endLabel:i===0?{show:true,color:AX,fontSize:10,formatter:p=>p.value.toFixed(0)+'%'}:{show:false},
      data:H.map(r=>{const t=r[bond].total; const v=c.k.reduce((a,k)=>a+(r[bond][k]||0),0); return +(v/t*100).toFixed(2);})}));
    charts[id].setOption({grid:{left:40,right:34,top:70,bottom:44},textStyle:{color:FG},
      // plain, wrapping legend — a scrolling one hides series behind an arrow
      legend:{top:0,width:'96%',textStyle:{color:AX,fontSize:10},itemWidth:10,itemHeight:8,itemGap:10,data:series.map(s=>s.name)},
      tooltip:{trigger:'axis',valueFormatter:v=>v==null?'\u2013':v.toFixed(2)+'%'},
      xAxis:{type:'category',boundaryGap:false,data:P,axisLabel:{color:AX,rotate:45,fontSize:9},axisLine:{lineStyle:{color:GRID}}},
      yAxis:{type:'value',max:100,axisLabel:{color:AX,formatter:'{value}%',fontSize:10},splitLine:{lineStyle:{color:GRID}}},
      series},true);
  });
}
/* Use of proceeds is reported per month. The YTD entries add the months of one
   calendar year together, field by field, so the mix can be read for the year
   so far and not only for the latest month. */
function useYTD(year){
  const rows=LGB.filter(r=>r.year===year&&r.use&&r.use.length);
  if(!rows.length)return null;
  const by={};rows.forEach(r=>r.use.forEach(u=>{by[u.field]=(by[u.field]||0)+u.v;}));
  return {months:rows.length,
          use:Object.keys(by).map(k=>({field:k,v:+by[k].toFixed(2)}))};
}
function fillLgbSel(){const s=document.getElementById('lgbsel');const cur=s.value;s.innerHTML='';
  const years=[...new Set(LGB.filter(r=>r.use&&r.use.length).map(r=>r.year))].sort((a,b)=>b-a);
  years.forEach(y=>{const y2=useYTD(y);if(!y2)return;
    const o=document.createElement('option');o.value='ytd-'+y;
    o.textContent=y+' '+L('YTD','年初至今')+' ('+y2.months+L('mo','个月')+')';s.appendChild(o);});
  LGB.filter(r=>r.use&&r.use.length).slice().reverse().forEach(r=>{const o=document.createElement('option');o.value=r.period;o.textContent=r.period;s.appendChild(o);});
  if(cur&&[...s.options].some(o=>o.value===cur))s.value=cur;}
function drawUse(period){
  let r,lab;
  if(period&&period.startsWith('ytd-')){const y=+period.slice(4);r=useYTD(y);lab=y+' '+L('YTD','年初至今');}
  if(!r){r=LGB.find(x=>x.period===period&&x.use&&x.use.length)||[...LGB].reverse().find(x=>x.use&&x.use.length);lab=r.period;}
  document.getElementById('note_use').textContent=period&&period.startsWith('ytd-')
    ?L('New-bond proceeds by investment field, summed over the months of '+lab+', RMB bn',
        lab+'各月新增债券资金投向合计，十亿元')
    :L('New special-bond proceeds by investment field for '+lab+', RMB bn',
        lab+'新增专项债券按投向分布，十亿元');
  const u=r.use.slice().sort((a,b)=>a.v-b.v);
  charts.c_lgb_use.setOption({grid:{left:210,right:60,top:8,bottom:24},textStyle:{color:FG},
    tooltip:{trigger:'item',formatter:p=>useShort(u[p.dataIndex].field)+'：RMB '+p.value+'bn'},
    xAxis:{type:'value',name:'RMB bn',axisLabel:{color:AX},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    yAxis:{type:'category',data:u.map(i=>useShort(i.field)),axisLabel:{color:AX,fontSize:11}},
    series:[{type:'bar',data:u.map(i=>i.v),itemStyle:{color:C.spec},
      label:{show:true,position:'right',color:AX,fontSize:10,formatter:p=>'RMB '+p.value+'bn'}}]},true);
}

function renderKPIs(){
  const Lt=DATA[DATA.length-1];
  document.getElementById('period_gen').innerHTML=L('Period: ','期间：')+'<span>'+(lang==='en'?perEN(Lt):perZH(Lt))+(Lt.month===12?'':L(' · YTD',' · 累计'))+'</span>';
  document.getElementById('period_fund').innerHTML=document.getElementById('period_gen').innerHTML;
  kpi('kpi_gen',[
    [L('Revenue','Revenue'),'一般公共预算收入',fmtB(Lt.pub_rev.v),'',Lt.pub_rev.g],
    [L('Expenditure','Expenditure'),'一般公共预算支出',fmtB(Lt.pub_exp.v),'',Lt.pub_exp.g],
    [L('Balance','Balance'),'收支差额',fmtB(Lt.pub_rev.v-Lt.pub_exp.v),L('rev − exp','收入−支出'),null],
    [L('Tax Revenue','Tax Revenue'),'税收收入',fmtB(Lt.tax.v),'',Lt.tax.g]]);
  kpi('kpi_fund',[
    [L('Fund Revenue','Fund Revenue'),'基金收入',fmtB(Lt.fund_rev.v),'',Lt.fund_rev.g],
    [L('Fund Expenditure','Fund Expenditure'),'基金支出',fmtB(Lt.fund_exp.v),'',Lt.fund_exp.g],
    [L('Land-Sale Revenue','Land-Sale Revenue'),'土地出让收入',Lt.land_rev?fmtB(Lt.land_rev.v):'–','',Lt.land_rev?Lt.land_rev.g:null],
    [L('Balance','Balance'),'收支差额',fmtB(Lt.fund_rev.v-Lt.fund_exp.v),L('rev − exp','收入−支出'),null]]);
  const i=LGB.length-1,G=LGB[i],yo=lgbYoY()[i],cum=basis==='cum';
  const iss=lgbVals('issue')[i],rt=lgbVals('rate')[i],mt=lgbVals('maturity')[i],
        gen=lgbVals('general')[i],spec=lgbVals('special')[i],
        nw=lgbVals('new')[i],rf=lgbVals('refi')[i];
  const tag=G.period+(G.src==='mof'?' *':'')+(cum?' '+L('YTD','年初至今'):'');
  kpi('kpi_lgb',[
    [L(cum?'YTD Issuance':'Monthly Issuance',''),cum?'年初至今发行':'当月发行',fmtB(iss),tag,yo],
    [L('General / Special',''),'一般债 / 专项债',fmtB(gen)+' / '+fmtB(spec),'',null],
    [L('New / Refinancing',''),'新增 / 再融资',fmtB(nw)+' / '+fmtB(rf),'',null],
    [L(cum?'Avg Rate YTD':'Avg Issue Rate',''),cum?'年初至今平均利率':'平均利率',(rt==null?'–':rt+'%'),
      cum?L('issuance-weighted','按发行额加权'):'',null],
    [L(cum?'Avg Maturity YTD':'Avg Maturity',''),cum?'年初至今平均期限':'平均期限',
      (mt==null?'–':mt+' <small>yr</small>'),cum?L('issuance-weighted','按发行额加权'):'',null]]);
  const T=(en,zh)=>L(en,zh);
  document.getElementById('h_lgb').textContent=cum
    ?T('YTD Issuance by Type & Average Rate','年初至今发行（按类型）与平均利率')
    :T('Monthly Issuance by Type & Average Rate','当月发行（按类型）与平均利率');
  document.getElementById('note_lgb').textContent=cum
    ?T('Bars: cumulative general vs special issuance within the year (RMB bn, left) · Line: issuance-weighted average rate to date (%, right)','柱：年内累计一般债与专项债发行（十亿元，左）· 线：年初至今按发行额加权平均利率（%，右）')
    :T('Bars: general vs special bonds (RMB bn, left) · Line: average issue rate (%, right)','柱：一般债与专项债（十亿元，左）· 线：平均发行利率（%，右）');
  const refiGap=T('Refinancing issuance runs above the principal actually repaid because refinancing special bonds also replace hidden debt under the NPC Standing Committee\u2019s November 2024 authorisation, not only roll maturing bonds.','再融资发行额高于实际偿还本金，因再融资专项债还用于置换存量隐性债务（2024年11月人大常委会授权），不止用于滚动到期债券。');
  document.getElementById('note_refi').textContent=(cum
    ?T('Cumulative principal repaid within the year, split by funding source (bars), vs cumulative refinancing-bond issuance and interest paid (lines), RMB bn','年内累计偿还本金（按资金来源堆叠）与累计再融资债券发行、付息（线），十亿元')
    :T('Monthly principal repaid, split by funding source (bars), vs refinancing-bond issuance and interest paid (lines), RMB bn','当月到期偿还本金（按资金来源堆叠）与再融资债券发行、付息（线），十亿元'))+'  '+refiGap;
  document.getElementById('note_lgb_yoy').textContent=cum
    ?T('YTD issuance vs the same point a year earlier, %','年初至今发行额与上年同期比较 %')
    :T('Monthly total issuance vs same month prior year, %','当月发行额同比 %');
  document.getElementById('note_lgb2').textContent=cum
    ?T('Line: issuance-weighted average maturity to date (years, left) · Bars: cumulative secondary-market turnover (RMB bn, right)','线：年初至今加权平均期限（年，左）· 柱：年内累计二级市场现券交易（十亿元，右）')
    :T('Line: average maturity (years, left) · Bars: secondary-market spot turnover (RMB bn, right)','线：平均期限（年，左）· 柱：二级市场现券交易（十亿元，右）');
}

function repayKpis(repRefi,repFisc,refiIss,interest){
  const cum=basis==='cum';
  // last month that actually has a repayment split
  let i=-1; for(let k=0;k<repRefi.length;k++) if(repRefi[k]!=null||repFisc[k]!=null) i=k;
  if(i<0){document.getElementById('kpi_repay').innerHTML='';return;}
  const per=REP[i].period, rr=repRefi[i], rf=repFisc[i], ri=refiIss[i], it=interest[i];
  const prin=(rr||0)+(rf||0);
  const pct=v=>v==null?'–':v.toFixed(1)+'%';
  const share=prin?(rr||0)/prin*100:null;          // how much of principal was rolled
  const cover=prin?(ri==null?null:ri/prin*100):null; // refinancing issued per unit repaid
  const svc=prin+(it||0);                           // principal + interest
  const tag=per+(cum?' '+L('YTD','年初至今'):'');
  kpi('kpi_repay',[
    [L('Principal Repaid',''),'偿还本金',fmtB(prin),tag,null],
    [L('via Refinancing / Fiscal Funds',''),'再融资 / 财政资金',fmtB(rr)+' / '+fmtB(rf),
      share==null?'':L('refinanced ','再融资占 ')+pct(share),null],
    [L('Refinancing Issued',''),'再融资发行',ri==null?'–':fmtB(ri),
      cover==null?'':pct(cover)+L(' of principal repaid','（占偿还本金）'),null],
    [L('Interest Paid',''),'付息',it==null?'–':fmtB(it),tag,null],
    [L('Total Debt Service',''),'还本付息合计',fmtB(svc),L('principal + interest','本金+利息'),null]]);
}

function drawBal(){
  const B=REP.filter(r=>r.bal!=null), P=B.map(r=>r.period), tn=v=>v==null?null:+(v/10000).toFixed(3);
  // NPC ceiling for the full calendar year (data/debt-limits.json); stepped in 2024-11 by the NPCSC's 6tn swap authorisation
  const ceil=p=>{let c=null;LIM.forEach(l=>{if(l.from<=p)c=l;});return c?c.total:null;};
  charts.c_bal.setOption({grid:{left:56,right:18,top:30,bottom:48},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('General debt','一般债务'),L('Special debt','专项债务'),L('NPC ceiling','人大限额')]},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>v==null?'–':v+' tn'},
    xAxis:{type:'category',data:P,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',name:'RMB tn',axisLabel:{color:AX},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    series:[{name:L('General debt','一般债务'),type:'bar',stack:'b',itemStyle:{color:C.gen},data:B.map(r=>tn(r.bal_gen))},
      {name:L('Special debt','专项债务'),type:'bar',stack:'b',itemStyle:{color:C.spec},data:B.map(r=>tn(r.bal_spec))},
      {name:L('NPC ceiling','人大限额'),type:'line',step:'end',showSymbol:false,lineStyle:{width:2,type:'dashed',color:C.rate},itemStyle:{color:C.rate},data:B.map(r=>tn(ceil(r.period)))}]},true);
  const G=B[B.length-1], py=B.find(r=>r.year===G.year-1&&r.month===G.month);
  const cl=ceil(G.period), yoy=py?+((G.bal/py.bal-1)*100).toFixed(1):null, hr=cl?(G.bal/cl*100).toFixed(1)+'% '+L('of ceiling','占限额'):'';
  kpi('kpi_bal',[
    [L('Debt Outstanding','Debt Outstanding'),'债务余额',tn(G.bal)+' <small>tn</small>',G.period+(hr?' · '+hr:''),yoy],
    [L('General / Special','General / Special'),'一般 / 专项',tn(G.bal_gen)+' / '+tn(G.bal_spec)+' <small>tn</small>','',null],
    [L('Avg Remaining Maturity','Avg Remaining Maturity'),'剩余平均年限',G.rem_mat+' <small>yr</small>',L('gen','一般')+' '+G.rem_mat_gen+' · '+L('spec','专项')+' '+G.rem_mat_spec,null],
    [L('Avg Coupon on Stock','Avg Coupon on Stock'),'存量平均利率',G.avg_rate+'%',L('gen','一般')+' '+G.avg_rate_gen+'% · '+L('spec','专项')+' '+G.avg_rate_spec+'%',null],
    [L('Interest Paid YTD','Interest Paid YTD'),'年初至今付息',fmtB(G.interest_ytd/10),G.interest_month?L('month','当月')+' '+fmtB(G.interest_month/10):'',null]]);
}
/* ---- Section 4: provincial quota vs execution (annual) -------------------
   This section is annual by nature -- the quota is allocated once a year -- so it
   deliberately does NOT follow the page's cumulative/monthly basis toggle, which
   only means something for the monthly flows in sections 1-3. */
const PSEQ = dark ? ['#15243f','#1d3a6b','#2b5fa8','#4e8fd6','#8dbdf0']
                  : ['#eaf1fb','#c3daf4','#8dbdf0','#4e8fd6','#1d3a6b'];
const PDIV = ['#b4472f','#d99a62','#e8e2d4','#79b39a','#2f7d5f'];
const PACC = C.spec;   // the page's accent red, from the shared palette
const PCOMPLETE = PROV.years.filter(y=>PROV.complete[y]);
let provYear = PCOMPLETE.length ? PCOMPLETE[PCOMPLETE.length-1] : PROV.years[PROV.years.length-1];
let provMetric = 'exec';
const pRows = y => PROV.rows.filter(r=>r.year===y);
const pName = r => L(r.en, r.cn);
const pPct = v => v==null ? '\u2013' : v.toFixed(1)+'%';
const PMETRIC = {
  exec:{en:'Execution rate, % of new-debt quota issued', zh:'执行率：新增限额已发行比例', div:true},
  quota:{en:'New-debt quota allocated', zh:'下达新增债务限额'},
  dgdp:{en:'Debt outstanding / provincial GDP', zh:'债务余额占本省GDP比重', unit:'%'},
  issue:{en:'New-bond issuance', zh:'新增债券发行额'}};

function pMapData(y){
  const by={};
  pRows(y).forEach(r=>{
    const key=r.parent||r.cn;
    if(!PROV.geo.features.some(f=>f.properties.name===key))return;
    const o=by[key]||(by[key]={cn:key,quota:0,issue:0,bal:0,gdp:0,parts:[]});
    o.quota+=r.quota||0; o.issue+=r.issue||0; o.bal+=r.bal||0;
    if(!r.parent)o.gdp=r.gdp||0; else o.parts.push(pName(r));
  });
  return Object.values(by).map(o=>({...o,
    exec:o.quota?+(o.issue/o.quota*100).toFixed(1):null,
    dgdp:o.gdp?+(o.bal/o.gdp*100).toFixed(1):null}));
}

function drawProvMap(){
  const d=pMapData(provYear);
  // execution is meaningless without a quota; show issuance instead
  const anyQ=d.some(o=>o.quota);
  const key=(provMetric==='exec'&&!anyQ)?'issue':provMetric;
  const M=PMETRIC[key]||PMETRIC.issue;
  const provMetricEff=key;
  const vals=d.map(o=>o[provMetricEff]).filter(v=>v!=null);
  const lo=vals.length?Math.min(...vals):0, hi=vals.length?Math.max(...vals):1;
  /* Execution is bimodal: most provinces sit within a point of 100 and a few fall
     far short, so a continuous ramp wide enough to hold the laggards leaves
     everyone else an identical neutral. Explicit bins keep the real thresholds. */
  const BINS=[{max:50,label:L('under 50%','低于50%'),color:PDIV[0]},
              {min:50,max:80,label:'50\u201380%',color:PDIV[1]},
              {min:80,max:95,label:'80\u201395%',color:PDIV[2]},
              {min:95,max:105,label:L('95\u2013105% (full)','95\u2013105%（用满）'),color:PDIV[3]},
              {min:105,label:L('over 105%','超过105%'),color:PDIV[4]}];
  charts.c_provmap.setOption({backgroundColor:'transparent',
    tooltip:{trigger:'item',formatter:p=>{const o=d.find(x=>x.cn===p.name);
      if(!o)return p.name+'<br>'+L('no data','无数据');
      return '<b>'+L(PROV.en[o.cn]||o.cn,o.cn)+'</b><br>'+
        L('Quota','限额')+' '+fmtB(o.quota/10)+'<br>'+
        L('Issued','发行')+' '+fmtB(o.issue/10)+'<br>'+
        L('Execution','执行率')+' '+pPct(o.exec)+'<br>'+
        L('Debt/GDP','债务率')+' '+pPct(o.dgdp)+
        (o.parts.length?'<br><span style="opacity:.7">'+L('incl. ','含 ')+o.parts.join('、')+'</span>':'');}},
    visualMap: M.div
      ? {type:'piecewise',left:8,bottom:10,itemGap:3,
         pieces:BINS.map(b=>({min:b.min,max:b.max,label:b.label,color:b.color})),
         textStyle:{color:AX,fontSize:10.5},outOfRange:{color:dark?'#23252b':'#f0f0f2'}}
      : {min:lo,max:hi,left:8,bottom:16,calculable:true,inRange:{color:PSEQ},
         textStyle:{color:AX,fontSize:10.5},
         formatter:v=>M.unit==='%'?v.toFixed(0)+'%':fmtB(v/10)},
    series:[{type:'map',map:'chinaprov',roam:false,
      data:d.map(o=>({name:o.cn,value:o[provMetricEff]})),label:{show:false},
      itemStyle:{borderColor:dark?'#2c2e33':'#fff',borderWidth:.6,
                 areaColor:dark?'#23252b':'#f0f0f2'},
      emphasis:{label:{show:false},itemStyle:{borderColor:PACC,borderWidth:1.4}},
      select:{disabled:true}}]},true);
  document.getElementById('h_provmap').textContent=L(M.en,M.zh);
}

function drawProvBar(){
  const rs=pRows(provYear).filter(r=>r.quota||r.issue);
  const byQuota=rs.some(r=>r.quota);
  const d=rs.sort((a,b)=>byQuota?((a.quota||0)-(b.quota||0)):((a.issue||0)-(b.issue||0)));
  charts.c_provbar.setOption({grid:{left:110,right:52,top:28,bottom:30},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('Quota','限额'),L('New-bond issuance','新增发行')]},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},formatter:ps=>{const r=d[ps[0].dataIndex];
      return '<b>'+pName(r)+'</b><br>'+L('Quota','限额')+' '+fmtB(r.quota/10)+'<br>'+
        L('Issued','发行')+' '+fmtB(r.issue/10)+'<br>'+L('Execution','执行率')+' '+pPct(r.exec)+
        '<br>'+L('Refinancing','再融资')+' '+fmtB((r.refi||0)/10);}},
    xAxis:{type:'value',name:'亿元',axisLabel:{color:AX,formatter:v=>v>=10000?(v/10000)+'万亿':v},
      splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    yAxis:{type:'category',data:d.map(pName),axisLabel:{color:AX,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    series:[{name:L('Quota','限额'),type:'bar',itemStyle:{color:dark?'#3a4556':'#cfd8e6'},
             barGap:'-100%',data:d.map(r=>r.quota)},
            {name:L('New-bond issuance','新增发行'),type:'bar',itemStyle:{color:PACC,opacity:.9},
             barWidth:'52%',data:d.map(r=>r.issue)}]},true);
}

function drawProvScatter(){
  const d=pRows(provYear).filter(r=>r.exec!=null&&r.dgdp!=null);
  const mx=d.length?Math.max(1,...d.map(r=>r.quota||0)):1;
  charts.c_provsc.setOption({grid:{left:56,right:24,top:22,bottom:44},textStyle:{color:FG},
    tooltip:{trigger:'item',formatter:p=>{const r=p.data.r;
      return '<b>'+pName(r)+'</b><br>'+L('Debt/GDP','债务率')+' '+pPct(r.dgdp)+'<br>'+
        L('Execution','执行率')+' '+pPct(r.exec)+'<br>'+L('Quota','限额')+' '+fmtB(r.quota/10);}},
    xAxis:{type:'value',name:L('Debt / GDP, %','债务率 %'),axisLabel:{color:AX,formatter:v=>v+'%'},
      splitLine:{lineStyle:{color:GRID}},nameLocation:'middle',nameGap:28,nameTextStyle:{color:AX}},
    yAxis:{type:'value',name:L('Execution, %','执行率 %'),axisLabel:{color:AX,formatter:v=>v+'%'},
      splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    series:[{type:'scatter',
      symbolSize:(v,pm)=>8+32*Math.sqrt(((pm.data&&pm.data.r&&pm.data.r.quota)||0)/mx),
      itemStyle:{color:PACC,opacity:.55,borderColor:PACC,borderWidth:1},
      label:{show:true,position:'top',color:AX,fontSize:9.5,formatter:p=>pName(p.data.r)},
      labelLayout:{hideOverlap:true},
      data:d.map(r=>({value:[r.dgdp,r.exec],r})),
      markLine:{silent:true,symbol:'none',lineStyle:{color:AX,type:'dashed',width:1},
        label:{color:AX,fontSize:10,formatter:L('full quota','限额用满')},data:[{yAxis:100}]}}]},true);
}

function provKpis(){
  const d=pRows(provYear), sum=k=>d.reduce((a,r)=>a+(r[k]||0),0);
  const rep=PROV.report[provYear]||{};
  const i=sum('issue'), rf=sum('refi'), bal=sum('bal');
  /* Execution must compare like with like: a region that has not reported a quota
     still reports issuance, so dividing total issuance by partial quota overstates
     it badly. Ratio only the issuers that have both. */
  const withQ=d.filter(r=>r.quota);
  const q=withQ.reduce((a,r)=>a+r.quota,0), iq=withQ.reduce((a,r)=>a+(r.issue||0),0);
  const qAll=withQ.length===d.length;
  const both=d.filter(r=>r.bal&&r.gdp), gdpOK=both.length>=d.length-2;
  const bg=both.reduce((a,r)=>a+r.bal,0), gd=both.reduce((a,r)=>a+r.gdp,0);
  const under=d.filter(r=>r.exec!=null&&r.exec<95).sort((a,b)=>a.exec-b.exec);
  const ytd=rep.ytd_through||null;
  kpi('kpi_prov',[
    [L(ytd?'New-debt quota (none yet)':'New-debt quota',''),'新增债务限额',q?fmtB(q/10):'–',
      (ytd&&!q)?L('not published for '+provYear+' yet','该年度尚未公布')
        :((qAll?provYear+' · '+d.length+L(' issuers','个主体')
             :provYear+' · '+withQ.length+L(' of ','/')+d.length+L(' issuers reporting','个主体已报'))
          +(rep.quota_sourced?' · '+rep.quota_sourced+L(' from budget reports','项取自预算报告'):'')),null],
    [L(ytd?'New bonds issued YTD':'New bonds issued',''),'新增债券发行',fmtB(i/10),
      (ytd?L('through ','截至 ')+ytd+' · ':'')+d.length+L(' issuers','个主体')
        +(rep.filled?' · '+rep.filled+L(' filled','项补录'):''),null],
    [L('Execution',''),'执行率',q?pPct(iq/q*100):'–',
      q?(qAll?L('all issuers','全部主体'):L('among the issuers reporting a quota','仅限已报限额的主体'))
       :L('needs a quota to compute','无限额，无法计算'),null],
    [L(ytd?'Refinancing issued YTD':'Refinancing issued',''),'再融资发行',fmtB(rf/10),
      L('not in execution','不计入执行率'),null],
    [L('Debt outstanding',''),'债务余额',fmtB(bal/10),
      (gdpOK&&gd)?'= '+pPct(bg/gd*100)+L(' of GDP','（占GDP）'):'',null]]);
  document.getElementById('prov_sub').textContent=L(
    'How much new borrowing each province was allowed for the year, and how much it actually issued. Annual; from MOF\u2019s bond disclosure platform.',
    '各省当年获批的新增债务限额与实际新增发行额。年度数据，来源于财政部地方政府债券信息公开平台。');
  const pe=document.getElementById('prov_partial');
  const noQ=d.filter(r=>!r.quota).map(pName);
  pe.hidden=!noQ.length;
  if(ytd){
    pe.hidden=false;
    pe.textContent=L(
      provYear+' is in progress. Issuance is year-to-date through '+ytd+' for all '+d.length+
        ' issuers, built from the platform\u2019s monthly series and cut at the last month whose '+
        'regions still sum to MOF\u2019s national release. The '+provYear+' quota has not been '+
        'published by region yet, so there is no execution rate and the map falls back to issuance.',
      provYear+'年度进行中。发行额为截至'+ytd+'的年初至今数据，覆盖全部'+d.length+
        '个主体，取自平台月度分地区序列，并截至分地区合计仍与财政部全国数一致的最后一个月。'+
        provYear+'年分地区新增限额尚未公布，故无执行率，地图改用发行额。');
  } else if(noQ.length){
    pe.textContent=L(
      'Issuance for '+provYear+' is complete for all '+d.length+' issuers'+
        (rep.filled?' ('+rep.filled+' taken from the Debt Center market report, which the platform has not yet restated)':'')+
        '. Quota is not: '+noQ.length+' issuers have not reported one ('+noQ.slice(0,6).join(', ')+
        (noQ.length>6?', …':'')+'), so the execution rate above covers only the '+(d.length-noQ.length)+
        ' that have, and those issuers are left out of the map and the scatter.',
      provYear+'年发行数据已覆盖全部'+d.length+'个主体'+
        (rep.filled?'（其中'+rep.filled+'个取自政府债务研究和评估中心市场报告，平台尚未更新）':'')+
        '；限额尚未报齐：'+noQ.length+'个主体未报（'+noQ.slice(0,6).join('、')+
        (noQ.length>6?'等':'')+'），故上方执行率仅覆盖已报限额的'+(d.length-noQ.length)+
        '个主体，这些主体不计入地图与散点图。');
  }
}

let pSortKey='quota', pSortDir=-1;
const PCOLS=[['cn','Issuer','发行主体'],['quota','Quota','新增限额'],['issue','Issued','新增发行'],
  ['exec','Exec %','执行率'],['ns','of which special','其中专项'],['refi','Refinancing','再融资'],
  ['rep','Principal repaid','还本'],['int','Interest','付息'],['bal','Debt balance','债务余额'],
  ['dgdp','Debt/GDP','债务率']];
function provTable(){
  const d=pRows(provYear), prov=d.filter(r=>!r.parent), sub=d.filter(r=>r.parent);
  // a year with no published quota would otherwise sort every row on a zero
  if(pSortKey==='quota'&&!d.some(r=>r.quota))pSortKey='issue';
  prov.sort((a,b)=>pSortKey==='cn'
    ? pSortDir*pName(a).localeCompare(pName(b))
    : pSortDir*(((a[pSortKey]==null)?-Infinity:a[pSortKey])-((b[pSortKey]==null)?-Infinity:b[pSortKey])));
  const mark=r=>(r.src==='market-report'
      ? ' <span title="'+L('issuance from the Debt Center market report','发行额取自债务中心市场报告')+'" style="opacity:.55">†</span>' : '')
    +(r.qsrc==='budget-report'
      ? ' <span title="'+L('quota from the region\u2019s own budget report','限额取自该地区预算报告')+'" style="opacity:.55">\u2021</span>' : '');
  const cell=(r,k)=>k==='cn' ? pName(r)+mark(r)
    : (k==='exec'||k==='dgdp')?pPct(r[k]):fmtB((r[k]||0)/10);
  let h='<thead><tr>'+PCOLS.map(c=>'<th data-k="'+c[0]+'">'+L(c[1],c[2])+
    (pSortKey===c[0]?(pSortDir<0?' \u25be':' \u25b4'):'')+'</th>').join('')+'</tr></thead><tbody>';
  const line=(r,cls)=>'<tr'+(cls?' class="'+cls+'"':'')+'>'+
    PCOLS.map(c=>'<td>'+cell(r,c[0])+'</td>').join('')+'</tr>';
  prov.forEach(r=>{h+=line(r);sub.filter(x=>x.parent===r.cn).forEach(x=>{h+=line(x,'sub');});});
  sub.filter(x=>!prov.some(r=>r.cn===x.parent)).forEach(x=>{h+=line(x,'sub');});
  const t=document.getElementById('provtbl'); t.innerHTML=h+'</tbody>';
  t.querySelectorAll('th').forEach(th=>th.onclick=()=>{
    const k=th.dataset.k;
    if(k===pSortKey)pSortDir=-pSortDir; else {pSortKey=k;pSortDir=k==='cn'?1:-1;}
    provTable();});
}

function drawProv(){
  [provKpis,drawProvMap,drawProvBar,drawProvScatter,provTable].forEach(fn=>{
    try{fn();}catch(e){console.error(fn.name,e);}});
}

function lgbPrelim(){const b=LGB.filter(r=>r.src==='mof').map(r=>r.period);
  const c=LGB.filter(r=>r.src==='cn').map(r=>r.period);
  const e=document.getElementById('lgb_prelim');
  e.hidden=!(b.length||c.length); if(e.hidden)return;
  const p=[];
  if(b.length)p.push(lang==='en'
    ?'* '+b.join(', ')+': issuance, rate and maturity taken from MOF\u2019s monthly 地方政府债券发行和债务余额情况 release, ahead of the Debt Center market report; secondary-market turnover and use of proceeds are not yet available for these months.'
    :'* '+b.join('、')+'：发行额、利率、期限取自财政部《地方政府债券发行和债务余额情况》月报，早于国债登记结算公司市场报告；该月二级市场交易与资金投向暂缺。');
  if(c.length)p.push(lang==='en'
    ?'* '+c.join(', ')+': from the Debt Center\u2019s Chinese 地方政府债券市场报告, which is published 3\u20134 weeks before its English translation. Figures are converted from 亿元 to RMB billion.'
    :'* '+c.join('、')+'：取自政府债务研究和评估中心《地方政府债券市场报告》中文版，该版早于英文版3–4周发布；数据由亿元折算为十亿元。');
  e.textContent=p.join('  ');}
function applyDataL(){document.querySelectorAll('[data-l]').forEach(e=>{const[en,zh]=e.getAttribute('data-l').split('|');e.textContent=lang==='en'?en:zh;});}

['c_provmap','c_provbar','c_provsc','c_gen_rev','c_gen_exp','c_tax_pie','c_tax_grow','c_exp_pie','c_exp_grow','c_fund','c_fund_yoy','c_exec_gen_rev','c_exec_gen_exp','c_exec_fund_rev','c_exec_fund_exp','c_lgb','c_lgb_refi','c_bal','c_hold_cgb','c_hold_lgb','c_lgb_ytd','c_lgb2','c_lgb_yoy','c_lgb_use'].forEach(mk);
document.getElementById('taxsel').onchange=e=>drawComposition('c_tax_pie','c_tax_grow','tax_items',e.target.value);
document.getElementById('expsel').onchange=e=>drawComposition('c_exp_pie','c_exp_grow','exp_items',e.target.value);
document.getElementById('lgbsel').onchange=e=>drawUse(e.target.value);
function seg(id,cb){document.querySelectorAll('#'+id+' button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#'+id+' button').forEach(x=>x.classList.remove('on'));b.classList.add('on');cb(b.dataset.v);});}
seg('basis',v=>{basis=v;drawGen();drawFund();drawLGB();drawRefiRepay();kpis();});
seg('split',v=>{split=v;drawGen();});
seg('lang',v=>{lang=v;document.body.classList.toggle('lang-en',v==='en');document.body.classList.toggle('lang-zh',v==='zh');applyDataL();fillSel('taxsel');fillSel('expsel');fillLgbSel();drawAll();});

function drawAll(){applyDataL();renderKPIs();drawGen();drawFund();
  drawExecYear('c_exec_gen_rev','pub_rev'); drawExecYear('c_exec_gen_exp','pub_exp');
  drawExecYear('c_exec_fund_rev','fund_rev'); drawExecYear('c_exec_fund_exp','fund_exp');
  yoyChart('c_fund_yoy',[['fund_rev','Fund Revenue','基金收入',C.fund],['fund_exp','Fund Expenditure','基金支出',C.exp],['land_rev','Land-Sale','土地出让',C.land]]);
  drawComposition('c_tax_pie','c_tax_grow','tax_items',document.getElementById('taxsel').value);
  drawComposition('c_exp_pie','c_exp_grow','exp_items',document.getElementById('expsel').value);
  drawLGB();drawNSB();drawUse(document.getElementById('lgbsel').value);lgbPrelim();drawBal();
  drawProv();}
echarts.registerMap('chinaprov', PROV.geo);
const pysel=document.getElementById('provyear');
PROV.years.slice().reverse().forEach(y=>{const o=document.createElement('option');
  const rp=PROV.report[y]||{};
  o.value=y;
  o.textContent=y+(rp.ytd_through?' (YTD '+rp.ytd_through.slice(5)+')':(PROV.complete[y]?'':' *'));
  pysel.appendChild(o);});
pysel.value=provYear;
pysel.onchange=e=>{provYear=+e.target.value;drawProv();};
seg('provmetric',v=>{provMetric=v;drawProvMap();});
addEventListener('resize',()=>Object.values(charts).forEach(c=>c.resize()));
fillSel('taxsel');fillSel('expsel');fillLgbSel();applyDataL();drawAll();
</script>
</body>
</html>
'''
HTML=HTML.replace('__FOOTER__', footer(['mof_monthly', 'debt_center', 'mof_balance', 'npc_budget', 'chinabond', 'celma', 'geoatlas', 'echarts'], page='fiscal-monitor.html', notes=BASIS_NOTE, map_page=True)).replace('__DATA__',DATA).replace('__LGB__',LGB).replace('__NSB__',NSB).replace('__REP__',REP).replace('__HOLD__',HOLD).replace('__TGT__',TGT).replace('__LIM__',LIM).replace('__PROV__',PROV)
open(base+'fiscal-monitor.html','w',encoding='utf-8').write(HTML)
if os.path.isdir(base+'docs'):  # the published site (GitHub Pages serves docs/)
    open(base+'docs/fiscal-monitor.html','w',encoding='utf-8').write(HTML)
print('wrote fiscal-monitor.html',round(len(HTML)/1024,1),'KB')
