#!/usr/bin/env python3
"""Build fiscal-drag.html — is fiscal execution adding to, or subtracting from, activity?

The argument in four steps, one chart each:
  1. Execution pace   — how much of the full-year budget has actually been spent by month
  2. Fiscal impulse   — YoY change in the broad (two-account) deficit, in RMB trillion
  3. Pass-through     — broad spending growth vs. fixed-asset investment and GDP
  4. The constraint   — land-sale / fund revenue collapse behind the fund-account squeeze
  5. Track record     — full-year execution vs. budget, 2022-2025

"Broad" = general public budget (account 1) + government-managed fund budget (account 2),
the two accounts the MOF reports monthly. All levels in RMB trillion (原始数据单位: 亿元).
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
YI2TN = 1e-4          # 亿元 -> RMB trillion

fis = json.load(open(BASE + 'data/mof-reports/fiscal_series.json'))
tgt = json.load(open(BASE + 'data/budget-targets.json'))['targets']

def macro(name):
    p = BASE + 'data/macro/%s_series.json' % name
    try:
        return json.load(open(p))
    except Exception:
        return []

fai = {r['period']: r.get('ytd_yoy') for r in macro('fai')}
gdp_q = {(r['year'], r['quarter'] * 3): r.get('gdp_yoy') for r in macro('gdp')}

def newest(name, key):
    """Latest non-null reading of one macro series, as (period, value)."""
    for r in reversed(macro(name)):
        if r.get(key) is not None:
            return {'period': r['period'], 'v': r[key]}
    return None

# NBS publishes activity ~4 weeks before MOF publishes the matching fiscal month,
# so these can sit one month ahead of the newest fiscal report.
activity = {
    'fai': newest('fai', 'ytd_yoy'),
    'pmi': newest('pmi', 'mfg'),
    'cpi': newest('cpi', 'yoy'),
    'retail': newest('retail', 'ytd'),
}

def v(rec, key):
    d = rec.get(key)
    return d.get('v') if isinstance(d, dict) else None

# ---- per-report row -------------------------------------------------------
rows = []
for r in fis:
    pub_e, fund_e = v(r, 'pub_exp'), v(r, 'fund_exp')
    pub_r, fund_r = v(r, 'pub_rev'), v(r, 'fund_rev')
    if None in (pub_e, fund_e, pub_r, fund_r):
        continue
    y, m = r['year'], r['month']
    t = tgt.get(str(y))
    budget = (t['pub_exp'] + t['fund_exp']) if t else None
    rows.append({
        'p': r['period'], 'y': y, 'm': m,
        'exp': pub_e + fund_e, 'rev': pub_r + fund_r,
        'pub_exp': pub_e, 'fund_exp': fund_e,
        'land': v(r, 'land_rev'), 'fund_rev': fund_r,
        'budget': budget,
        'pace': round((pub_e + fund_e) / budget * 100, 2) if budget else None,
    })

by_ym = {(r['y'], r['m']): r for r in rows}

def yoy(cur, prev):
    if cur is None or prev in (None, 0):
        return None
    return round((cur / prev - 1) * 100, 2)

for r in rows:
    q = by_ym.get((r['y'] - 1, r['m']))
    r['deficit'] = round((r['exp'] - r['rev']) * YI2TN, 3)
    if q:
        r['exp_yoy'] = yoy(r['exp'], q['exp'])
        r['rev_yoy'] = yoy(r['rev'], q['rev'])
        r['pub_exp_yoy'] = yoy(r['pub_exp'], q['pub_exp'])
        r['fund_exp_yoy'] = yoy(r['fund_exp'], q['fund_exp'])
        r['fund_rev_yoy'] = yoy(r['fund_rev'], q['fund_rev'])
        r['land_yoy'] = yoy(r['land'], q['land'])
        # fiscal impulse: YoY change in the broad YTD deficit (+ = expansion)
        r['impulse'] = round(((r['exp'] - r['rev']) - (q['exp'] - q['rev'])) * YI2TN, 3)
        r['d_exp'] = round((r['exp'] - q['exp']) * YI2TN, 3)
        r['d_rev'] = round((r['rev'] - q['rev']) * YI2TN, 3)
    else:
        for k in ('exp_yoy', 'rev_yoy', 'pub_exp_yoy', 'fund_exp_yoy',
                  'fund_rev_yoy', 'land_yoy', 'impulse', 'd_exp', 'd_rev'):
            r[k] = None
    r['fai'] = fai.get(r['p'])
    r['gdp'] = gdp_q.get((r['y'], r['m']))

# ---- chart 1: execution pace, [month, % of full-year budget] per year ------
pace_by_year = {}
for r in rows:
    if r['pace'] is not None:
        pace_by_year.setdefault(str(r['y']), []).append([r['m'], r['pace']])
for k in pace_by_year:
    pace_by_year[k].sort()

# ---- chart 5: full-year execution vs. budget (years with a December report)-
annual = []
for y in sorted({r['y'] for r in rows}):
    r = by_ym.get((y, 12))
    if not r or not r['budget']:
        continue
    annual.append({
        'y': y,
        'actual': round(r['exp'] * YI2TN, 2),
        'budget': round(r['budget'] * YI2TN, 2),
        'pct': round(r['exp'] / r['budget'] * 100, 1),
        'gap': round((r['exp'] - r['budget']) * YI2TN, 2),
    })

# ---- headline numbers -----------------------------------------------------
cur = rows[-1]
prev = by_ym.get((cur['y'] - 1, cur['m']))
py_full = by_ym.get((cur['y'] - 1, 12))
last_done = annual[-1] if annual else None

# what H2 (rest of year) must do, YoY, to hit the full-year budget
catchup = None
if prev and py_full and cur['budget']:
    rest_needed = cur['budget'] - cur['exp']
    rest_last = py_full['exp'] - prev['exp']
    if rest_last:
        catchup = round((rest_needed / rest_last - 1) * 100, 1)

head = {
    'period': cur['p'],
    'exp_tn': round(cur['exp'] * YI2TN, 2),
    'exp_yoy': cur['exp_yoy'],
    'pace': cur['pace'],
    'pace_prev': prev['pace'] if prev else None,
    'impulse': cur['impulse'],
    'catchup': catchup,
    'rest_months': 12 - cur['m'],
    'last_year': last_done['y'] if last_done else None,
    'last_pct': last_done['pct'] if last_done else None,
    'last_gap': last_done['gap'] if last_done else None,
    'fai': cur['fai'],
    'gdp': cur['gdp'] or next((r['gdp'] for r in reversed(rows) if r['gdp'] is not None), None),
    'years': sorted(pace_by_year.keys()),
}

PAYLOAD = {'rows': rows, 'pace': pace_by_year, 'annual': annual, 'head': head, 'activity': activity}

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fiscal Drag Monitor · 财政拖累监测</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{color-scheme:light dark;--bg:#f7f7f8;--fg:#1a1a1a;--card:#fff;--bd:#e3e3e6;--mut:#666;--accent:#c00;--up:#16a34a;--down:#dc2626;--warn:#e07b00;}
@media(prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#e6e6e6;--card:#1e1f23;--bd:#2c2e33;--mut:#9aa;--accent:#ff6b6b;}}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",Helvetica,Arial,sans-serif;background:var(--bg);color:var(--fg);line-height:1.5}
body.lang-en .zh{display:none}
.wrap{max-width:1080px;margin:0 auto;padding:2rem 1.1rem 4rem}
h1{font-size:1.7rem;margin:0 0 .15rem}
.zh{color:var(--mut);font-weight:400}
h1 .zh{font-size:1.05rem;display:block;margin-top:.1rem}
.sub{color:var(--mut);margin:.2rem 0 1.2rem;font-size:.9rem}
.sub a{color:var(--accent)}
.controls{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:1.2rem}
.seg{display:inline-flex;border:1px solid var(--bd);border-radius:9px;overflow:hidden;background:var(--card)}
.seg button{border:0;background:transparent;color:var(--fg);padding:.45rem .8rem;font-size:.85rem;cursor:pointer}
.seg button.on{background:var(--accent);color:#fff}
.lede{background:var(--card);border:1px solid var(--bd);border-left:4px solid var(--accent);border-radius:10px;padding:.9rem 1.05rem;margin-bottom:1.3rem;font-size:.93rem}
.lede p{margin:.35rem 0}
.lede b{font-weight:650}
.ahead{font-size:.84rem;color:var(--mut);margin:-.6rem 0 1.2rem;padding-left:.2rem}
.ahead b{color:var(--fg);font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:.8rem;margin-bottom:1.5rem}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:.85rem .95rem}
.kpi .t{font-size:.76rem;color:var(--mut)}
.kpi .v{font-size:1.45rem;font-weight:650;margin:.15rem 0 .05rem}
.kpi .v small{font-size:.78rem;font-weight:400;color:var(--mut)}
.kpi .g{font-size:.8rem;color:var(--mut);min-height:1.1em}
.up{color:var(--up)}.down{color:var(--down)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1rem .5rem;margin-bottom:1.2rem}
.card h3{font-size:1rem;margin:.1rem 0 .1rem;font-weight:650}
.card h3 .step{color:var(--accent);margin-right:.4rem}
.card h3 .zh{font-size:.85rem;display:block;font-weight:400}
.card .note{font-size:.79rem;color:var(--mut);margin:.25rem 0 .4rem}
.card .take{font-size:.83rem;margin:.1rem 0 .6rem;padding:.45rem .6rem;background:rgba(204,0,0,.06);border-radius:7px}
@media(prefers-color-scheme:dark){.card .take{background:rgba(255,107,107,.09)}}
.chart{width:100%;height:380px}
.chart.sm{height:330px}
footer{margin-top:1.6rem;font-size:.78rem;color:var(--mut)}
footer a{color:var(--mut)}
.caveat{font-size:.78rem;color:var(--mut);background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:.8rem .95rem;margin-top:1.4rem}
.caveat li{margin:.25rem 0}
</style>
</head>
<body class="lang-en">
<div class="wrap">

<h1>Fiscal Drag Monitor <span class="zh">财政拖累监测</span></h1>
<p class="sub">
  <span data-l="Is budget execution adding to demand, or subtracting from it?|预算执行是在扩张需求，还是在收缩需求？"></span> ·
  <a href="index.html" data-l="&larr; all data|&larr; 全部数据"></a> ·
  <a href="fiscal-monitor.html" data-l="Fiscal Monitor|财政运行监测"></a> ·
  <span data-l="Source|来源"></span>: <a href="https://www.mof.gov.cn/zhengwuxinxi/redianzhuanti/quanguocaizhengshouzhiqingkuang/">MOF 财政部</a> / <a href="https://www.stats.gov.cn/sj/zxfb/">NBS 国家统计局</a>
</p>

<div class="controls">
  <span class="seg" id="lang"><button data-v="en" class="on">EN</button><button data-v="zh">中文</button></span>
</div>

<div class="lede" id="lede"></div>
<p class="ahead" id="ahead"></p>
<div class="kpis" id="kpi"></div>

<div class="card">
  <h3><span class="step">1</span><span data-l="Is the budget actually being spent?|预算真的花出去了吗？"></span>
      <span class="zh">广义财政支出进度（占全年预算 %）</span></h3>
  <p class="note" data-l="Cumulative broad expenditure as a share of the full-year budget, by month. Each line is one year.|年初至当月广义财政支出占全年预算的比重，按月。每条线代表一年。"></p>
  <div class="take" id="take1"></div>
  <div id="c1" class="chart"></div>
</div>

<div class="card">
  <h3><span class="step">2</span><span data-l="Fiscal impulse: the deficit change, in yuan|财政脉冲：赤字变化（万亿元）"></span>
      <span class="zh">广义赤字同比变化</span></h3>
  <p class="note" data-l="YoY change in the broad YTD deficit (expenditure minus revenue). Bars above zero = fiscal is injecting more demand than a year ago; below zero = withdrawing it.|广义累计赤字（支出减收入）的同比变化。柱在零上＝比去年同期注入更多需求；零下＝在回收需求。"></p>
  <div class="take" id="take2"></div>
  <div id="c2" class="chart"></div>
</div>

<div class="card">
  <h3><span class="step">3</span><span data-l="Pass-through to activity|向实体活动的传导"></span>
      <span class="zh">广义支出增速 vs 固定资产投资与GDP</span></h3>
  <p class="note" data-l="Broad spending growth split into its two accounts. The government-fund account is the one that finances infrastructure — it moves with fixed-asset investment.|广义支出增速及其两本账拆分。政府性基金账户是基建的资金来源，与固定资产投资同向变动。"></p>
  <div class="take" id="take3"></div>
  <div id="c3" class="chart"></div>
</div>

<div class="card">
  <h3><span class="step">4</span><span data-l="Why execution slips: the funding side|执行为何落后：资金来源"></span>
      <span class="zh">土地出让收入与政府性基金收支</span></h3>
  <p class="note" data-l="The government-fund account is financed largely by land sales. When land revenue falls, the spending it funds follows.|政府性基金账户主要依靠土地出让收入。土地收入下滑，其支撑的支出随之回落。"></p>
  <div class="take" id="take4"></div>
  <div id="c4" class="chart sm"></div>
</div>

<div class="card">
  <h3><span class="step">5</span><span data-l="Track record: budgets are not fully executed|历史记录：预算并未足额执行"></span>
      <span class="zh">全年实际支出 vs 年初预算</span></h3>
  <p class="note" data-l="Full-year broad expenditure versus the budget approved at the start of the year. A negative gap is money appropriated but not spent.|全年广义支出与年初预算的差额。负值＝已列预算但未支出的资金。"></p>
  <div class="take" id="take5"></div>
  <div id="c5" class="chart sm"></div>
</div>

<div class="caveat">
  <b data-l="How to read this / caveats|读法与说明"></b>
  <ul>
    <li data-l="&quot;Broad&quot; = general public budget + government-managed fund budget, the two accounts MOF reports monthly. It excludes the social-insurance and SOE-capital accounts.|广义＝一般公共预算＋政府性基金预算，即财政部按月公布的两本账，不含社保基金与国有资本经营预算。"></li>
    <li data-l="Growth rates here are computed from reported levels; MOF's own YoY figures may differ slightly where it restates on a comparable basis (可比口径).|此处增速由公布的绝对额计算；财政部按可比口径公布的同比可能略有差异。"></li>
    <li data-l="Budget = the figure approved by the NPC each March (年初预算). Mid-year supplementary budgets are not reflected, so late-year execution ratios can overstate any shortfall.|预算＝每年3月全国人大批准的年初预算，未反映年中调整预算，故年末执行率可能高估缺口。"></li>
    <li data-l="MOF publishes cumulative (YTD) figures; each year's first release covers January-February combined, so month 1 has no standalone point.|财政部公布累计数，每年首份报告为1—2月合计，故无单独1月数据。"></li>
    <li data-l="This page shows co-movement, not a causal estimate. Fiscal is one of several forces acting on activity.|本页展示的是同向变动，并非因果估计。财政只是影响经济活动的因素之一。"></li>
  </ul>
</div>

<footer>
  <span data-l="Data: Ministry of Finance (fiscal), National Bureau of Statistics (FAI, GDP) · built for|数据：财政部（财政）、国家统计局（固投、GDP）· 构建于"></span>
  <a href="https://github.com/yqcao/China-Fiscal-Data">github.com/yqcao/China-Fiscal-Data</a>
</footer>
</div>

<script>
const D = __PAYLOAD__;
const R = D.rows, H = D.head;
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
const AX = dark ? '#9aa' : '#666', GRID = dark ? '#2c2e33' : '#eee', FG = dark ? '#e6e6e6' : '#1a1a1a';
const RED = dark ? '#ff6b6b' : '#c00', BLUE = '#1463ff', GREEN = '#0a9d6b', ORANGE = '#e07b00', GREY = dark ? '#5a5f68' : '#c3c6cc';
let lang = 'en';
const L = (e, z) => lang === 'en' ? e : z;
const n1 = x => x == null ? '—' : (x > 0 ? '+' : '') + x.toFixed(1);
const n2 = x => x == null ? '—' : (x > 0 ? '+' : '') + x.toFixed(2);
const cls = x => x == null ? '' : (x >= 0 ? 'up' : 'down');

// pretty period label: 2026-06 -> "Jan-Jun 2026" / "2026年1—6月"
function plabel(p) {
  const [y, m] = p.split('-').map(Number);
  return lang === 'en' ? 'Jan–' + ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][m] + ' ' + y
                       : y + '年1—' + m + '月';
}

function applyL() {
  document.querySelectorAll('[data-l]').forEach(e => {
    const i = e.getAttribute('data-l').indexOf('|');
    e.innerHTML = lang === 'en' ? e.getAttribute('data-l').slice(0, i) : e.getAttribute('data-l').slice(i + 1);
  });
}

function renderText() {
  const per = plabel(H.period);
  const paceGap = (H.pace != null && H.pace_prev != null) ? (H.pace - H.pace_prev) : null;
  document.getElementById('lede').innerHTML = L(
    '<p>Through <b>' + per + '</b>, broad fiscal spending — the general public budget plus the government-fund budget — totalled <b>¥' + H.exp_tn.toFixed(2) + ' tn</b>, <b class="' + cls(H.exp_yoy) + '">' + n1(H.exp_yoy) + '%</b> versus a year earlier. That is <b>' + H.pace.toFixed(1) + '%</b> of the full-year budget, against ' + (H.pace_prev != null ? H.pace_prev.toFixed(1) + '% at the same point last year' : 'no comparable prior year') + '.</p>' +
    '<p>Because spending fell while revenue held up, the broad deficit is <b class="' + cls(H.impulse) + '">¥' + Math.abs(H.impulse).toFixed(2) + ' tn ' + (H.impulse < 0 ? 'smaller' : 'larger') + '</b> than at this point last year. A narrower deficit means the budget is <b>' + (H.impulse < 0 ? 'withdrawing' : 'adding') + '</b> demand — a fiscal ' + (H.impulse < 0 ? 'drag' : 'impulse') + '. Over the same window fixed-asset investment ran at <b class="' + cls(H.fai) + '">' + n1(H.fai) + '%</b> and real GDP growth was <b>' + (H.gdp == null ? '—' : H.gdp.toFixed(1) + '%</b>') + '.</p>',
    '<p>截至<b>' + per + '</b>，广义财政支出（一般公共预算＋政府性基金预算）合计<b>' + H.exp_tn.toFixed(2) + '万亿元</b>，同比<b class="' + cls(H.exp_yoy) + '">' + n1(H.exp_yoy) + '%</b>，仅完成全年预算的<b>' + H.pace.toFixed(1) + '%</b>' + (H.pace_prev != null ? '，而去年同期为' + H.pace_prev.toFixed(1) + '%' : '') + '。</p>' +
    '<p>支出下降而收入平稳，广义财政赤字比去年同期<b class="' + cls(H.impulse) + '">' + (H.impulse < 0 ? '缩小' : '扩大') + Math.abs(H.impulse).toFixed(2) + '万亿元</b>。赤字缩小意味着预算在<b>' + (H.impulse < 0 ? '回收' : '注入') + '</b>需求，即财政' + (H.impulse < 0 ? '拖累' : '拉动') + '。同期固定资产投资<b class="' + cls(H.fai) + '">' + n1(H.fai) + '%</b>，实际GDP增速<b>' + (H.gdp == null ? '—' : H.gdp.toFixed(1) + '%') + '</b>。</p>'
  );

  // activity prints can run a month ahead of the fiscal data — say so rather than hiding it
  const A = D.activity || {}, newest = A.fai && A.fai.period;
  const el = document.getElementById('ahead');
  if (newest && newest > H.period) {
    const bits = [];
    if (A.fai) bits.push(L('fixed-asset investment ', '固定资产投资') + '<b class="' + cls(A.fai.v) + '">' + n1(A.fai.v) + '%</b>');
    if (A.retail) bits.push(L('retail sales ', '社零') + '<b class="' + cls(A.retail.v) + '">' + n1(A.retail.v) + '%</b>');
    if (A.pmi) bits.push(L('manufacturing PMI ', '制造业PMI') + '<b class="' + (A.pmi.v >= 50 ? 'up' : 'down') + '">' + A.pmi.v.toFixed(1) + '</b>');
    if (A.cpi) bits.push(L('CPI ', 'CPI') + '<b class="' + cls(A.cpi.v) + '">' + n1(A.cpi.v) + '%</b>');
    el.innerHTML = L('Activity data already runs a month ahead of the fiscal reports — ' + plabel(newest).replace('Jan–', '') + ': ',
                     '实体数据已比财政报告多一个月——' + newest.slice(0, 4) + '年' + Number(newest.slice(5)) + '月：') + bits.join(L(' · ', ' · '));
  } else { el.innerHTML = ''; }

  const K = [
    ['Broad fiscal spending|广义财政支出', L('¥' + H.exp_tn.toFixed(2) + '<small> tn</small>', H.exp_tn.toFixed(2) + '<small> 万亿元</small>'), n1(H.exp_yoy) + '% ' + L('YoY', '同比'), cls(H.exp_yoy)],
    ['Budget executed|预算执行进度', H.pace.toFixed(1) + '<small>%</small>',
      (paceGap == null ? '' : n1(paceGap) + 'pp ' + L('vs last year', '比去年同期')), cls(paceGap)],
    ['Fiscal impulse|财政脉冲', (H.impulse >= 0 ? '+' : '−') + L('¥' + Math.abs(H.impulse).toFixed(2) + '<small> tn</small>', Math.abs(H.impulse).toFixed(2) + '<small> 万亿元</small>'),
      L(H.impulse < 0 ? 'deficit narrower → drag' : 'deficit wider → support', H.impulse < 0 ? '赤字缩小 → 拖累' : '赤字扩大 → 支持'), cls(H.impulse)],
    ['Needed in remaining ' + H.rest_months + ' months|剩余' + H.rest_months + '个月所需',
      (H.catchup == null ? '—' : n1(H.catchup) + '<small>%</small>'), L('YoY, to hit the budget', '同比，方能完成预算'), cls(H.catchup)],
    [H.last_year + ' execution|' + H.last_year + '年执行率', H.last_pct.toFixed(1) + '<small>%</small>',
      L('¥' + Math.abs(H.last_gap).toFixed(2) + ' tn ' + (H.last_gap < 0 ? 'unspent' : 'over'), Math.abs(H.last_gap).toFixed(2) + '万亿元' + (H.last_gap < 0 ? '未支出' : '超支')), cls(H.last_gap)],
  ];
  document.getElementById('kpi').innerHTML = K.map(k =>
    '<div class="kpi"><div class="t">' + L(k[0].split('|')[0], k[0].split('|')[1]) + '</div>' +
    '<div class="v">' + k[1] + '</div><div class="g ' + k[3] + '">' + k[2] + '</div></div>').join('');

  const behind = paceGap == null ? null : -paceGap;
  document.getElementById('take1').innerHTML = L(
    behind == null ? '' : (behind > 0
      ? '<b>' + H.period.slice(0, 4) + ' is running ' + behind.toFixed(1) + 'pp behind last year’s pace</b> at the same month — the budget exists on paper but the cash has not gone out.'
      : '<b>' + H.period.slice(0, 4) + ' is running ' + (-behind).toFixed(1) + 'pp ahead of last year’s pace</b> at the same month.'),
    behind == null ? '' : (behind > 0
      ? '<b>' + H.period.slice(0, 4) + '年同月份执行进度比去年慢' + behind.toFixed(1) + '个百分点</b>——预算已列，但资金未落地。'
      : '<b>' + H.period.slice(0, 4) + '年同月份执行进度比去年快' + (-behind).toFixed(1) + '个百分点</b>。'));

  document.getElementById('take2').innerHTML = L(
    'Latest reading <b class="' + cls(H.impulse) + '">' + n2(H.impulse) + ' tn</b>. Bars below zero are periods when the budget took more out of the economy than it put in, relative to a year earlier.',
    '最新读数 <b class="' + cls(H.impulse) + '">' + n2(H.impulse) + '万亿元</b>。零下的柱表示相比去年同期，财政从经济中抽走的多于注入的。');

  const lastFundExp = R[R.length - 1].fund_exp_yoy, lastPubExp = R[R.length - 1].pub_exp_yoy;
  document.getElementById('take3').innerHTML = L(
    'The public budget is roughly flat (<b class="' + cls(lastPubExp) + '">' + n1(lastPubExp) + '%</b>) but the government-fund account — the infrastructure account — is at <b class="' + cls(lastFundExp) + '">' + n1(lastFundExp) + '%</b>. Fixed-asset investment tracks it.',
    '一般公共预算基本持平（<b class="' + cls(lastPubExp) + '">' + n1(lastPubExp) + '%</b>），但政府性基金账户（基建资金）为<b class="' + cls(lastFundExp) + '">' + n1(lastFundExp) + '%</b>。固定资产投资与之同步。');

  const lastLand = R[R.length - 1].land_yoy;
  document.getElementById('take4').innerHTML = L(
    'Land-sale revenue is <b class="' + cls(lastLand) + '">' + n1(lastLand) + '%</b> YoY. That is the binding constraint on the spending account above.',
    '国有土地出让收入同比<b class="' + cls(lastLand) + '">' + n1(lastLand) + '%</b>，是上方支出账户的硬约束。');

  const shortfalls = D.annual.filter(a => a.gap < 0);
  document.getElementById('take5').innerHTML = L(
    shortfalls.length + ' of the ' + D.annual.length + ' completed years came in <b>under</b> budget' +
      (H.last_gap < 0 ? ', most recently ' + H.last_year + ' by <b>¥' + Math.abs(H.last_gap).toFixed(2) + ' tn</b>' : '') +
      '. Under-execution is the norm, not the exception.',
    '已完整年份中有' + shortfalls.length + '/' + D.annual.length + '年<b>低于</b>预算' +
      (H.last_gap < 0 ? '，最近的' + H.last_year + '年少支出<b>' + Math.abs(H.last_gap).toFixed(2) + '万亿元</b>' : '') +
      '。执行不足是常态而非例外。');
}

const base = extra => Object.assign({
  backgroundColor: 'transparent',
  grid: { left: 52, right: 56, top: 42, bottom: 34 },
  tooltip: { trigger: 'axis', confine: true },
  legend: { top: 4, textStyle: { color: FG, fontSize: 11 }, itemWidth: 16, itemHeight: 9 },
  textStyle: { color: FG },
}, extra || {});

const catX = () => ({ type: 'category', data: R.map(r => r.p), axisLabel: { color: AX, fontSize: 10 }, axisLine: { lineStyle: { color: GRID } } });
const valY = (name, extra) => Object.assign({
  type: 'value', name: name, nameTextStyle: { color: AX, fontSize: 10 },
  axisLabel: { color: AX, fontSize: 10 }, splitLine: { lineStyle: { color: GRID } },
}, extra || {});

const c1 = echarts.init(document.getElementById('c1'));
const c2 = echarts.init(document.getElementById('c2'));
const c3 = echarts.init(document.getElementById('c3'));
const c4 = echarts.init(document.getElementById('c4'));
const c5 = echarts.init(document.getElementById('c5'));

function draw() {
  const yrs = H.years, cy = yrs[yrs.length - 1];
  // 1 — execution pace
  c1.setOption({
    ...base({ grid: { left: 52, right: 24, top: 42, bottom: 34 } }),
    tooltip: { trigger: 'axis', confine: true, valueFormatter: v => v == null ? '—' : v.toFixed(1) + '%' },
    xAxis: { type: 'value', min: 2, max: 12, interval: 1, name: L('month', '月份'), nameLocation: 'end', nameTextStyle: { color: AX, fontSize: 10 }, axisLabel: { color: AX, fontSize: 10 }, splitLine: { lineStyle: { color: GRID } } },
    yAxis: valY(L('% of full-year budget', '占全年预算 %')),
    series: yrs.map((y, i) => ({
      name: y, type: 'line', data: D.pace[y], connectNulls: true,
      symbol: 'circle', symbolSize: y === cy ? 7 : 4,
      z: y === cy ? 10 : 1,
      lineStyle: { width: y === cy ? 3.2 : 1.4, color: y === cy ? RED : (y === yrs[yrs.length - 2] ? BLUE : GREY) },
      itemStyle: { color: y === cy ? RED : (y === yrs[yrs.length - 2] ? BLUE : GREY) },
    })),
  }, true);

  // 2 — fiscal impulse
  c2.setOption({
    ...base(),
    tooltip: {
      trigger: 'axis', confine: true,
      formatter: ps => ps[0].axisValue + '<br>' + ps.map(p =>
        p.marker + p.seriesName + ': <b>' + (p.value == null ? '—' : (p.seriesIndex === 0 ? n2(p.value) + ' tn' : n1(p.value) + '%')) + '</b>').join('<br>'),
    },
    xAxis: catX(),
    yAxis: [valY(L('¥ tn', '万亿元')), valY('%', { position: 'right' })],
    series: [
      { name: L('Change in broad deficit', '广义赤字同比变化'), type: 'bar', yAxisIndex: 0,
        data: R.map(r => r.impulse), barMaxWidth: 16, color: GREY,
        itemStyle: { color: p => p.value >= 0 ? GREEN : RED } },
      { name: L('Fixed-asset investment YoY', '固投累计同比'), type: 'line', yAxisIndex: 1,
        data: R.map(r => r.fai), connectNulls: true, symbol: 'none', lineStyle: { width: 2, color: BLUE }, itemStyle: { color: BLUE } },
      { name: L('Real GDP YoY', '实际GDP同比'), type: 'line', yAxisIndex: 1,
        data: R.map(r => r.gdp), connectNulls: true, symbol: 'circle', symbolSize: 5, lineStyle: { width: 2, type: 'dashed', color: ORANGE }, itemStyle: { color: ORANGE } },
    ],
  }, true);

  // 3 — pass-through
  const line = (name, key, color, extra) => Object.assign({
    name: name, type: 'line', data: R.map(r => r[key]), connectNulls: true,
    symbol: 'none', lineStyle: { width: 2, color: color }, itemStyle: { color: color },
  }, extra || {});
  c3.setOption({
    ...base({ grid: { left: 52, right: 24, top: 42, bottom: 34 } }),
    tooltip: { trigger: 'axis', confine: true, valueFormatter: v => v == null ? '—' : n1(v) + '%' },
    xAxis: catX(),
    yAxis: valY('% YoY'),
    series: [
      line(L('Broad expenditure', '广义支出'), 'exp_yoy', RED, { lineStyle: { width: 3, color: RED } }),
      line(L('Public budget expenditure', '一般公共预算支出'), 'pub_exp_yoy', GREY),
      line(L('Government-fund expenditure', '政府性基金支出'), 'fund_exp_yoy', GREEN),
      line(L('Fixed-asset investment', '固定资产投资'), 'fai', BLUE, { lineStyle: { width: 2.4, type: 'dashed', color: BLUE } }),
    ],
  }, true);

  // 4 — funding constraint
  c4.setOption({
    ...base({ grid: { left: 52, right: 24, top: 42, bottom: 34 } }),
    tooltip: { trigger: 'axis', confine: true, valueFormatter: v => v == null ? '—' : n1(v) + '%' },
    xAxis: catX(),
    yAxis: valY('% YoY'),
    series: [
      { name: L('Land-sale revenue', '土地出让收入'), type: 'bar', data: R.map(r => r.land_yoy),
        barMaxWidth: 16, color: ORANGE, itemStyle: { color: p => p.value >= 0 ? GREEN : ORANGE } },
      line(L('Government-fund revenue', '政府性基金收入'), 'fund_rev_yoy', BLUE),
      line(L('Government-fund expenditure', '政府性基金支出'), 'fund_exp_yoy', RED, { lineStyle: { width: 3, color: RED } }),
    ],
  }, true);

  // 5 — annual execution
  c5.setOption({
    ...base({ grid: { left: 56, right: 56, top: 42, bottom: 34 } }),
    tooltip: { trigger: 'axis', confine: true },
    xAxis: { type: 'category', data: D.annual.map(a => a.y), axisLabel: { color: AX }, axisLine: { lineStyle: { color: GRID } } },
    yAxis: [valY(L('¥ tn vs budget', '万亿元（与预算差）')), valY(L('% executed', '执行率 %'), { position: 'right', min: 85, max: 105 })],
    series: [
      { name: L('Actual minus budget', '实际减预算'), type: 'bar', yAxisIndex: 0, barMaxWidth: 44, color: GREY,
        data: D.annual.map(a => a.gap), itemStyle: { color: p => p.value >= 0 ? GREEN : RED },
        label: { show: true, position: 'top', color: FG, fontSize: 11, formatter: p => n2(p.value) } },
      { name: L('Execution rate', '执行率'), type: 'line', yAxisIndex: 1, data: D.annual.map(a => a.pct),
        symbol: 'circle', symbolSize: 7, lineStyle: { width: 2, color: BLUE }, itemStyle: { color: BLUE } },
    ],
  }, true);
}

function renderAll() { applyL(); renderText(); draw(); }

document.getElementById('lang').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  lang = b.dataset.v;
  document.querySelectorAll('#lang button').forEach(x => x.classList.toggle('on', x === b));
  document.body.classList.toggle('lang-en', lang === 'en');
  renderAll();
});
addEventListener('resize', () => [c1, c2, c3, c4, c5].forEach(c => c.resize()));
renderAll();
</script>
</body>
</html>
'''

out = HTML.replace('__PAYLOAD__', json.dumps(PAYLOAD, ensure_ascii=False, separators=(',', ':')))
path = BASE + 'fiscal-drag.html'
open(path, 'w').write(out)
print('wrote fiscal-drag.html %.1f KB  (latest %s)' % (len(out) / 1024, cur['p']))
print('  broad exp YTD %.2f tn (%s%% YoY), pace %.1f%%, impulse %+.2f tn'
      % (cur['exp'] * YI2TN, cur['exp_yoy'], cur['pace'], cur['impulse']))
for a in annual:
    print('  %d execution %.1f%%  gap %+.2f tn' % (a['y'], a['pct'], a['gap']))
