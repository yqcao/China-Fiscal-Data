#!/usr/bin/env python3
"""Build mohrss.html from data/mohrss/mohrss_series.json.

Covers every indicator MOHRSS publishes in its monthly 主要统计快报数据 table:
employment, the social-insurance schemes (participants / fund revenue / fund
expenditure / balance), labour-dispute arbitration and labour inspection.
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
D = json.load(open(BASE + 'data/mohrss/mohrss_series.json'))

# ---- schemes and series metadata (kind: flow = differenceable, stock = not) --
SCHEMES = [
    {'k': 'pension_urban', 'en': 'Urban employee pension', 'zh': '城镇职工基本养老保险'},
    {'k': 'pension_rural', 'en': 'Rural/non-working pension', 'zh': '城乡居民基本养老保险'},
    {'k': 'ui',            'en': 'Unemployment insurance',   'zh': '失业保险'},
    {'k': 'injury',        'en': 'Work-injury insurance',    'zh': '工伤保险'},
    {'k': 'medical',       'en': 'Medical insurance',        'zh': '医疗保险'},
    {'k': 'maternity',     'en': 'Maternity insurance',      'zh': '生育保险'},
]

META = {
    'emp_new':    ('New urban jobs', '城镇新增就业人数', '万人', 'flow'),
    'emp_reemp':  ('Re-employed', '城镇失业人员再就业人数', '万人', 'flow'),
    'emp_hard':   ('Hard-to-employ placed', '就业困难人员就业人数', '万人', 'flow'),
    'skill_certs': ('New skill certificates', '新增技师以上获证人次', '万人次', 'flow'),
    'unemp_survey': ('Surveyed urban unemployment', '城镇调查失业率', '%', 'stock'),
    'unemp_registered': ('Registered urban unemployment', '期末城镇登记失业率', '%', 'stock'),
    'disp_cases': ('Cases accepted', '立案受理案件总数', '万件', 'flow'),
    'disp_workers': ('Workers involved', '涉及劳动者人数', '万人', 'flow'),
    'disp_concluded': ('Cases concluded', '当期审结案件数', '万件', 'flow'),
    'insp_closed': ('Inspection cases closed', '劳动保障监察案件结案数', '万件', 'flow'),
    'insp_checked': ('Employers inspected', '主动检查用人单位户数', '万户', 'flow'),
    'insp_contracts': ('Contracts signed', '督促补签劳动合同', '万人', 'flow'),
    'insp_wages': ('Back wages recovered', '追发工资等待遇金额', '亿元', 'flow'),
    'insp_siprem': ('SI premiums recovered', '督促缴纳社会保险费金额', '亿元', 'flow'),
}
for s in SCHEMES:
    META[s['k'] + '_insured'] = (s['en'] + ' participants', s['zh'] + '参保人数', '万人', 'stock')
    META[s['k'] + '_rev'] = (s['en'] + ' fund revenue', s['zh'] + '基金收入', '亿元', 'flow')
    META[s['k'] + '_exp'] = (s['en'] + ' fund expenditure', s['zh'] + '基金支出', '亿元', 'flow')
    META[s['k'] + '_bal'] = (s['en'] + ' fund balance', s['zh'] + '基金结余', '亿元', 'flow')

cur = D[-1]
first_pdf = next((r['period'] for r in D if r['src'] == 'pdf'), None)
head = {
    'period': cur['period'],
    'emp_new': cur['emp_new'], 'unemp': cur['unemp_survey'] or cur['unemp_registered'],
    'ui_exp': cur['ui_exp'], 'ui_rev': cur['ui_rev'], 'ui_bal': cur['ui_bal'],
    'ui_insured': cur['ui_insured'],
    'span': [D[0]['period'], D[-1]['period']], 'n': len(D),
    'first_pdf': first_pdf,
}
# year-ago comparison at the same month
prev = next((r for r in D if r['year'] == cur['year'] - 1 and r['month'] == cur['month']), None)
if prev:
    for k in ('emp_new', 'ui_exp', 'ui_rev'):
        a, b = cur.get(k), prev.get(k)
        head[k + '_yoy'] = round((a / b - 1) * 100, 1) if (a and b) else None

PAYLOAD = {'rows': D, 'meta': META, 'schemes': SCHEMES, 'head': head}

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Employment &amp; Social Insurance · 就业与社会保险</title>
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
.sub{color:var(--mut);margin:.2rem 0 1.3rem;font-size:.9rem}
.sub a{color:var(--accent)}
.controls{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:1.3rem}
.seg{display:inline-flex;border:1px solid var(--bd);border-radius:9px;overflow:hidden;background:var(--card);flex-wrap:wrap}
.seg button{border:0;background:transparent;color:var(--fg);padding:.45rem .8rem;font-size:.85rem;cursor:pointer}
.seg button.on{background:var(--accent);color:#fff}
.lbl{font-size:.78rem;color:var(--mut);margin-right:.1rem}
section{margin:2.2rem 0}
.shead{border-top:2px solid var(--accent);padding-top:.7rem;margin-bottom:.9rem}
.shead h2{font-size:1.22rem;margin:0}
.shead .zh{font-size:.95rem}
.shead p{margin:.25rem 0 0;font-size:.82rem;color:var(--mut)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.8rem;margin-bottom:1.3rem}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:.85rem .95rem}
.kpi .t{font-size:.76rem;color:var(--mut)}
.kpi .v{font-size:1.4rem;font-weight:650;margin:.15rem 0 .05rem}
.kpi .v small{font-size:.78rem;font-weight:400;color:var(--mut)}
.kpi .g{font-size:.8rem;color:var(--mut);min-height:1.1em}
.up{color:var(--up)}.down{color:var(--down)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1rem .5rem;margin-bottom:1.1rem}
.card h3{font-size:.98rem;margin:.1rem 0 .15rem;font-weight:650}
.card h3 .zh{font-size:.83rem}
.card .note{font-size:.77rem;color:var(--mut);margin:.2rem 0 .45rem}
.chart{width:100%;height:360px}
.chart.sm{height:320px}
footer{margin-top:1.6rem;font-size:.78rem;color:var(--mut)}footer a{color:var(--mut)}
.caveat{font-size:.79rem;color:var(--mut);background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:.85rem 1rem;margin-top:1.5rem}
.caveat li{margin:.3rem 0}
.caveat b{color:var(--fg)}
</style>
</head>
<body class="lang-en">
<div class="wrap">

<h1>Employment &amp; Social Insurance <span class="zh">就业与社会保险月度数据</span></h1>
<p class="sub">
  <span data-l="Every indicator in the MOHRSS monthly statistical release|人力资源和社会保障部月度统计快报全部指标"></span> ·
  <a href="index.html" data-l="&larr; all data|&larr; 全部数据"></a> ·
  <a href="fiscal-drag.html" data-l="Fiscal Drag|财政拖累监测"></a> ·
  <span data-l="Source|来源"></span>:
  <a href="https://www.mohrss.gov.cn/SYrlzyhshbzb/zwgk/szrs/tjsj/">MOHRSS 人力资源和社会保障部</a>
</p>

<div class="controls">
  <span class="seg" id="lang"><button data-v="en" class="on">EN</button><button data-v="zh">中文</button></span>
  <span class="lbl" data-l="basis|口径"></span>
  <span class="seg" id="basis">
    <button data-v="ytd" class="on" data-l="Cumulative YTD|年初累计"></button>
    <button data-v="mom" data-l="Single month|当月"></button>
  </span>
</div>

<div class="kpis" id="kpi"></div>

<section>
  <div class="shead"><h2>Employment <span class="zh">就业和再就业</span></h2>
    <p data-l="Job creation and placement, plus the urban unemployment rate.|就业创造与安置，以及城镇失业率。"></p></div>
  <div class="card">
    <h3><span data-l="Jobs created and placements|新增就业与再就业"></span></h3>
    <p class="note" data-l="New urban jobs, re-employed unemployed, and hard-to-employ people placed.|城镇新增就业人数、失业人员再就业人数、就业困难人员就业人数。"></p>
    <div id="c_emp" class="chart"></div>
  </div>
  <div class="card">
    <h3><span data-l="Urban unemployment rate|城镇失业率"></span></h3>
    <p class="note" data-l="Two different measures. The registered rate (in this table to 2021) counts people who register as unemployed; the surveyed rate (carried here from 2022) is a labour-force survey. They are not comparable and are drawn as separate lines.|两种口径。登记失业率（本表至2021年）统计主动登记人数；调查失业率（本表2022年起）为劳动力调查。二者不可比，分别绘制。"></p>
    <div id="c_unemp" class="chart sm"></div>
  </div>
</section>

<section>
  <div class="shead"><h2>Social insurance funds <span class="zh">社会保险基金</span></h2>
    <p data-l="Revenue, expenditure and the resulting balance, by scheme.|分险种的基金收入、支出与收支结余。"></p></div>
  <div class="controls">
    <span class="lbl" data-l="scheme|险种"></span>
    <span class="seg" id="scheme"></span>
  </div>
  <div class="card">
    <h3><span id="fundTitle"></span></h3>
    <p class="note" data-l="Bars are revenue and expenditure; the line is the balance (revenue minus expenditure). Below zero means the scheme paid out more than it took in.|柱为基金收入与支出，线为收支结余（收入减支出）。低于零表示支出大于收入。"></p>
    <div id="c_fund" class="chart"></div>
  </div>
  <div class="card">
    <h3><span data-l="Participants, all schemes|各险种参保人数"></span></h3>
    <p class="note" data-l="End-of-period participants. A stock, so it is never differenced — the single-month toggle does not apply here.|期末参保人数。存量指标，不做差分——当月口径对此不适用。"></p>
    <div id="c_insured" class="chart"></div>
  </div>
</section>

<section>
  <div class="shead"><h2>Labour disputes &amp; inspection <span class="zh">劳动人事争议与劳动保障监察</span></h2>
    <p data-l="Arbitration caseload and enforcement activity.|争议仲裁案件量与执法监察情况。"></p></div>
  <div class="card">
    <h3><span data-l="Dispute arbitration|劳动人事争议处理"></span></h3>
    <p class="note" data-l="Cases accepted, workers involved, and cases concluded.|立案受理案件总数、涉及劳动者人数、当期审结案件数。"></p>
    <div id="c_disp" class="chart sm"></div>
  </div>
  <div class="card">
    <h3><span data-l="Labour inspection|劳动保障监察"></span></h3>
    <p class="note" data-l="Enforcement cases closed, employers inspected, contracts signed under order, and money recovered for workers.|监察案件结案数、主动检查用人单位户数、督促补签劳动合同，以及为劳动者追发的金额。"></p>
    <div id="c_insp" class="chart sm"></div>
  </div>
</section>

<div class="caveat">
  <b data-l="How to read this / caveats|读法与说明"></b>
  <ul>
    <li data-l="Figures are cumulative from January within each year (年初累计). Unlike the MOF fiscal reports, MOHRSS publishes a standalone January release, so single-month values are available for every month.|数据为年初至当期累计。与财政部报告不同，人社部单独发布1月数据，故各月均可还原当月值。"></li>
    <li data-l="The single-month toggle applies only to flow indicators (fund revenue and expenditure, jobs created, case counts). Participants and unemployment rates are stocks and are never differenced.|当月口径仅适用于流量指标（基金收支、新增就业、案件数）。参保人数与失业率为存量/比率，不做差分。"></li>
    <li data-l="Medical and maternity insurance leave the table after 2018 — medical insurance moved to the new National Healthcare Security Administration (国家医保局), and maternity insurance was merged into it. Those series therefore stop, rather than falling to zero.|医疗保险与生育保险自2018年后不再出现在本表——医保划归国家医保局，生育保险并入医保。相关序列到此终止，而非归零。"></li>
    <li data-l="The registered and surveyed unemployment rates measure different things and are not spliced together.|登记失业率与调查失业率口径不同，未作拼接。"></li>
    <li data-l="Some indicators appear only in the quarterly and annual editions of the release, so their lines are sparser than the monthly ones. Gaps are genuine publication gaps, not parse failures.|部分指标仅在季度、年度版本中发布，故其序列较稀疏。缺口为发布口径所致，非解析失败。"></li>
    <li id="cv_src"></li>
  </ul>
</div>

<footer>
  <span data-l="Source: Ministry of Human Resources and Social Security · built for|数据来源：人力资源和社会保障部 · 构建于"></span>
  <a href="https://github.com/yqcao/China-Fiscal-Data">github.com/yqcao/China-Fiscal-Data</a>
</footer>
</div>

<script>
const P = __PAYLOAD__;
const R = P.rows, META = P.meta, SCH = P.schemes, H = P.head;
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
const AX = dark ? '#9aa' : '#666', GRID = dark ? '#2c2e33' : '#eee', FG = dark ? '#e6e6e6' : '#1a1a1a';
const RED = dark ? '#ff6b6b' : '#c00', BLUE = '#1463ff', GREEN = '#0a9d6b', ORANGE = '#e07b00',
      PURPLE = '#8b5cf6', TEAL = '#0891b2';
let lang = 'en', basis = 'ytd', scheme = 'ui';
const L = (e, z) => lang === 'en' ? e : z;
const P_ = R.map(r => r.period);
const nm = k => { const m = META[k]; return m ? L(m[0], m[1]) : k; };
const unit = k => (META[k] || [,,''])[2];
const kind = k => (META[k] || [,,,'flow'])[3];

// YTD -> single month, but only for flows and only when the previous month of the
// same year is actually present (2016 has two missing releases).
function ser(k) {
  const stock = kind(k) === 'stock';
  return R.map((r, i) => {
    const v = r[k];
    if (v == null) return null;
    if (basis === 'ytd' || stock) return v;
    if (r.month === 1) return v;
    const p = R[i - 1];
    if (!p || p.year !== r.year || p.month !== r.month - 1 || p[k] == null) return null;
    return Math.round((v - p[k]) * 1e4) / 1e4;
  });
}

function applyL() {
  document.querySelectorAll('[data-l]').forEach(e => {
    const a = e.getAttribute('data-l'), i = a.indexOf('|');
    e.innerHTML = lang === 'en' ? a.slice(0, i) : a.slice(i + 1);
  });
  document.getElementById('cv_src').innerHTML = L(
    'Archive covers <b>' + H.n + '</b> monthly releases, ' + H.span[0] + ' to ' + H.span[1] +
    '. Releases up to ' + (H.first_pdf ? '2019-12' : '') + ' are legacy .xls; from ' + H.first_pdf +
    ' they are PDFs, and the two eras carry slightly different indicator sets.',
    '存档共 <b>' + H.n + '</b> 期月度数据，' + H.span[0] + ' 至 ' + H.span[1] +
    '。2019-12 及以前为 .xls，' + H.first_pdf + ' 起为 PDF，两个时期的指标集略有差异。');
}

function kpis() {
  const g = v => v == null ? '' : (v > 0 ? '+' : '') + v.toFixed(1) + '% ' + L('YoY', '同比');
  const c = v => v == null ? '' : (v >= 0 ? 'up' : 'down');
  const K = [
    [L('New urban jobs', '城镇新增就业'), H.emp_new == null ? '—' : H.emp_new.toLocaleString() + '<small> 万人</small>',
      g(H.emp_new_yoy), c(H.emp_new_yoy)],
    [L('Urban unemployment', '城镇失业率'), H.unemp == null ? '—' : H.unemp.toFixed(1) + '<small>%</small>', '', ''],
    [L('UI fund expenditure', '失业保险基金支出'), H.ui_exp == null ? '—' : H.ui_exp.toLocaleString() + '<small> 亿元</small>',
      g(H.ui_exp_yoy), c(H.ui_exp_yoy)],
    [L('UI fund balance', '失业保险收支结余'),
      (H.ui_bal == null ? '—' : (H.ui_bal >= 0 ? '+' : '−') + Math.abs(H.ui_bal).toFixed(1) + '<small> 亿元</small>'),
      L(H.ui_bal >= 0 ? 'surplus' : 'deficit', H.ui_bal >= 0 ? '结余' : '缺口'), c(H.ui_bal)],
    [L('UI participants', '失业保险参保人数'), H.ui_insured == null ? '—' : H.ui_insured.toLocaleString() + '<small> 万人</small>', '', ''],
  ];
  document.getElementById('kpi').innerHTML = K.map(k =>
    '<div class="kpi"><div class="t">' + k[0] + '</div><div class="v">' + k[1] +
    '</div><div class="g ' + k[3] + '">' + k[2] + '</div></div>').join('');
}

const charts = {};
const init = id => charts[id] || (charts[id] = echarts.init(document.getElementById(id)));
const base = extra => Object.assign({
  backgroundColor: 'transparent',
  grid: { left: 60, right: 30, top: 44, bottom: 56 },
  tooltip: { trigger: 'axis', confine: true },
  legend: { top: 4, textStyle: { color: FG, fontSize: 11 }, itemWidth: 16, itemHeight: 9 },
  textStyle: { color: FG },
  dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 12,
              textStyle: { color: AX, fontSize: 9 } }],
  xAxis: { type: 'category', data: P_, axisLabel: { color: AX, fontSize: 10 },
           axisLine: { lineStyle: { color: GRID } } },
}, extra || {});
const yA = (name, extra) => Object.assign({
  type: 'value', name: name, nameTextStyle: { color: AX, fontSize: 10 },
  axisLabel: { color: AX, fontSize: 10 }, splitLine: { lineStyle: { color: GRID } },
}, extra || {});
const line = (k, color, extra) => Object.assign({
  name: nm(k), type: 'line', data: ser(k), connectNulls: true, symbol: 'none',
  lineStyle: { width: 2, color: color }, itemStyle: { color: color },
}, extra || {});

function draw() {
  init('c_emp').setOption({ ...base(), yAxis: yA(L('10k people', '万人')),
    series: [line('emp_new', RED, { lineStyle: { width: 2.6, color: RED } }),
             line('emp_reemp', BLUE), line('emp_hard', GREEN), line('skill_certs', ORANGE)] }, true);

  init('c_unemp').setOption({ ...base(), yAxis: yA('%', { min: 3, max: 7 }),
    series: [line('unemp_survey', RED, { symbol: 'circle', symbolSize: 4 }),
             line('unemp_registered', BLUE, { symbol: 'circle', symbolSize: 4,
                                              lineStyle: { width: 2, type: 'dashed', color: BLUE } })] }, true);

  const s = scheme;
  document.getElementById('fundTitle').textContent =
    L(META[s + '_rev'][0].replace(' fund revenue', ''), META[s + '_rev'][1].replace('基金收入', '')) +
    L(' — revenue, expenditure and balance', ' — 基金收入、支出与结余');
  init('c_fund').setOption({ ...base(), yAxis: yA(L('RMB 100m', '亿元')),
    series: [
      { name: L('Fund revenue', '基金收入'), type: 'bar', data: ser(s + '_rev'),
        itemStyle: { color: GREEN }, barMaxWidth: 10 },
      { name: L('Fund expenditure', '基金支出'), type: 'bar', data: ser(s + '_exp'),
        itemStyle: { color: ORANGE }, barMaxWidth: 10 },
      { name: L('Balance', '收支结余'), type: 'line', data: ser(s + '_bal'),
        symbol: 'none', lineStyle: { width: 2.4, color: RED }, itemStyle: { color: RED }, z: 5 },
    ] }, true);

  const cols = [RED, BLUE, GREEN, ORANGE, PURPLE, TEAL];
  init('c_insured').setOption({ ...base(), yAxis: yA(L('10k people', '万人')),
    series: SCH.map((x, i) => line(x.k + '_insured', cols[i],
      { name: L(x.en, x.zh), lineStyle: { width: 2, color: cols[i] } })) }, true);

  init('c_disp').setOption({ ...base(), yAxis: yA(L('10k cases / 10k people', '万件 / 万人')),
    series: [line('disp_cases', RED, { symbol: 'circle', symbolSize: 3 }),
             line('disp_workers', BLUE, { symbol: 'circle', symbolSize: 3 }),
             line('disp_concluded', GREEN, { symbol: 'circle', symbolSize: 3 })] }, true);

  init('c_insp').setOption({ ...base(), yAxis: [yA(L('10k', '万')), yA(L('RMB 100m', '亿元'), { position: 'right' })],
    series: [line('insp_closed', RED, { symbol: 'circle', symbolSize: 3 }),
             line('insp_checked', BLUE, { symbol: 'circle', symbolSize: 3 }),
             line('insp_contracts', GREEN, { symbol: 'circle', symbolSize: 3 }),
             line('insp_wages', ORANGE, { yAxisIndex: 1, symbol: 'circle', symbolSize: 3 }),
             line('insp_siprem', PURPLE, { yAxisIndex: 1, symbol: 'circle', symbolSize: 3 })] }, true);
}

function schemeButtons() {
  const lastYear = +H.span[1].slice(0, 4);
  document.getElementById('scheme').innerHTML = SCH.map(x => {
    const yrs = R.filter(r => r[x.k + '_rev'] != null).map(r => r.year);
    const till = yrs.length ? Math.max(...yrs) : null;
    // schemes that leave the table get their final year shown on the button
    const tag = (till && till < lastYear) ? ' <span style="opacity:.6">\u2192' + till + '</span>' : '';
    return '<button data-v="' + x.k + '"' + (x.k === scheme ? ' class="on"' : '') + '>' +
           L(x.en, x.zh) + tag + '</button>';
  }).join('');
}

function renderAll() { applyL(); kpis(); schemeButtons(); draw(); }

document.getElementById('lang').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  lang = b.dataset.v;
  document.querySelectorAll('#lang button').forEach(x => x.classList.toggle('on', x === b));
  document.body.classList.toggle('lang-en', lang === 'en');
  renderAll();
});
document.getElementById('basis').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  basis = b.dataset.v;
  document.querySelectorAll('#basis button').forEach(x => x.classList.toggle('on', x === b));
  draw();
});
document.getElementById('scheme').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  scheme = b.dataset.v;
  document.querySelectorAll('#scheme button').forEach(x => x.classList.toggle('on', x === b));
  draw();
});
addEventListener('resize', () => Object.values(charts).forEach(c => c.resize()));
renderAll();
</script>
</body>
</html>
'''

out = HTML.replace('__PAYLOAD__', json.dumps(PAYLOAD, ensure_ascii=False, separators=(',', ':')))
open(BASE + 'mohrss.html', 'w').write(out)
print('wrote mohrss.html %.1f KB  (%d months %s..%s)'
      % (len(out) / 1024, len(D), D[0]['period'], D[-1]['period']))
print('  latest: new urban jobs %s万人, UI exp %s亿元, UI balance %s亿元'
      % (cur['emp_new'], cur['ui_exp'], cur['ui_bal']))
