#!/usr/bin/env python3
"""Build tax-split.html — how each tax is divided between centre and provinces.

Two things the page has to keep apart:

  the rule    Statutory sharing ratios per tax, from the State Council decisions
              in data/tax-sharing-rules.json. Two of the eighteen lines MOF
              reports (印花税, 其他税收) bundle items on different rules, so they
              carry no ratio and are shown as unallocated rather than guessed.

  the outturn What the centre and the provinces actually end up with, from the
              MOF monthly release. This is NOT the rule applied to the tax take:
              the reported central/local revenue split also carries non-tax
              revenue, and local spending is largely funded by transfers that
              never appear in local revenue at all.

Applying the rule to the tax take is therefore labelled an estimate, and the
page shows the reported outturn beside it rather than in place of it.

Inputs: data/mof-reports/fiscal_series.json, data/tax-sharing-rules.json.
"""
import json, os

BASE  = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
YI2BN = 0.1                                     # 亿元 -> RMB bn

fis   = json.load(open(BASE + 'data/mof-reports/fiscal_series.json'))
rules = json.load(open(BASE + 'data/tax-sharing-rules.json'))
RULE  = {t['cn']: t for t in rules['taxes']}

def v(r, k):
    d = r.get(k)
    return d.get('v') if isinstance(d, dict) else None

# ---- 1. the latest complete calendar year, by tax line -------------------
year = max(r['year'] for r in fis if r['month'] == 12)
dec  = next(r for r in fis if r['year'] == year and r['month'] == 12)
# 出口退税 is printed as a positive number but deducted from the total: it is a
# refund the centre pays out, so it enters the split as negative central revenue.
REBATE = '出口退税'

taxes = []
for it in dec['tax_items']:
    cn = it['name']
    ru = RULE.get(cn)
    if not ru:
        print(f'  WARNING no rule for {cn}'); continue
    amt = it['v'] * YI2BN * (-1 if cn == REBATE else 1)
    known = ru['central'] is not None
    taxes.append({
        'cn': cn, 'en': ru['en'], 'amt': round(amt, 1),
        'c_pct': ru['central'], 'l_pct': ru['local'],
        'c_amt': round(amt * ru['central'] / 100, 1) if known else None,
        'l_amt': round(amt * ru['local'] / 100, 1) if known else None,
        'note': ru.get('note', ''), 'src': [rules['sources'][s] for s in ru['src']]})
taxes.sort(key=lambda t: -abs(t['amt']))

est_c = sum(t['c_amt'] for t in taxes if t['c_amt'] is not None)
est_l = sum(t['l_amt'] for t in taxes if t['l_amt'] is not None)
unalloc = sum(t['amt'] for t in taxes if t['c_amt'] is None)

# ---- 2. reported central/local outturn, monthly --------------------------
ser = []
for r in fis:
    rc, rl, ec, el = (v(r, 'pub_rev_central'), v(r, 'pub_rev_local'),
                      v(r, 'pub_exp_central'), v(r, 'pub_exp_local'))
    if None in (rc, rl, ec, el): continue
    ser.append({'period': r['period'], 'year': r['year'], 'month': r['month'],
                'rev_c': round(rc * YI2BN, 1), 'rev_l': round(rl * YI2BN, 1),
                'exp_c': round(ec * YI2BN, 1), 'exp_l': round(el * YI2BN, 1)})

# full calendar years, for the revenue-vs-spending gap
years = [s for s in ser if s['month'] == 12]

last = ser[-1]
kpi = {
    'period':   last['period'],
    'rev_loc':  round(last['rev_l'] / (last['rev_c'] + last['rev_l']) * 100, 1),
    'exp_loc':  round(last['exp_l'] / (last['exp_c'] + last['exp_l']) * 100, 1),
    'gap':      round(last['exp_l'] - last['rev_l'], 1),
    'year': year, 'est_c': round(est_c, 1), 'est_l': round(est_l, 1),
    'est_c_pct': round(est_c / (est_c + est_l) * 100, 1),
    'unalloc': round(unalloc, 1),
}

P = json.dumps({'taxes': taxes, 'ser': ser, 'years': years, 'kpi': kpi,
                'sources': rules['sources'], 'note': rules['note']},
               ensure_ascii=False, separators=(',', ':'))

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tax Split · 中央与地方税收划分</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{color-scheme:light dark;--bg:#f7f7f8;--fg:#1a1a1a;--card:#fff;--bd:#e3e3e6;--mut:#666;--accent:#c00;}
@media(prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#e6e6e6;--card:#1e1f23;--bd:#2c2e33;--mut:#9aa;--accent:#ff6b6b;}}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",Helvetica,Arial,sans-serif;background:var(--bg);color:var(--fg);line-height:1.5}
body.lang-en .zh{display:none}
.wrap{max-width:1080px;margin:0 auto;padding:2rem 1.1rem 4rem}
h1{font-size:1.7rem;margin:0 0 .15rem}
.zh{color:var(--mut);font-weight:400}
h1 .zh{font-size:1.05rem;display:block;margin-top:.1rem}
.sub{color:var(--mut);margin:.2rem 0 1.3rem;font-size:.9rem}.sub a{color:var(--accent)}
.controls{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:1.3rem}
.seg{display:inline-flex;border:1px solid var(--bd);border-radius:9px;overflow:hidden;background:var(--card)}
.seg button{border:0;background:transparent;color:var(--fg);padding:.45rem .8rem;font-size:.85rem;cursor:pointer}
.seg button.on{background:var(--accent);color:#fff}
.lbl{font-size:.78rem;color:var(--mut);margin-right:.1rem}
section{margin:2.2rem 0}
.shead{border-top:2px solid var(--accent);padding-top:.7rem;margin-bottom:.9rem}
.shead h2{font-size:1.22rem;margin:0}.shead .zh{font-size:.95rem}
.shead p{margin:.25rem 0 0;font-size:.82rem;color:var(--mut)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1rem .5rem;margin-bottom:1.1rem}
.card h3{font-size:.98rem;margin:.1rem 0 .15rem;font-weight:650}.card h3 .zh{font-size:.83rem}
.card .note{font-size:.77rem;color:var(--mut);margin:.2rem 0 .45rem}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.8rem;margin-bottom:1.4rem}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:.85rem .95rem}
.kpi .k{font-size:.76rem;color:var(--mut)}
.kpi .n{font-size:1.5rem;font-weight:660;margin:.1rem 0 0}
.kpi .s{font-size:.74rem;color:var(--mut)}
.chart{width:100%;height:520px}.chart.md{height:400px}.chart.sm{height:330px}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem}
@media(max-width:820px){.row2{grid-template-columns:1fr}}
table.src{width:100%;border-collapse:collapse;font-size:.78rem;margin-top:.3rem}
table.src td{padding:.32rem .4rem;border-top:1px solid var(--bd);vertical-align:top}
table.src td:first-child{white-space:nowrap;color:var(--fg);font-weight:600}
table.src td:nth-child(2){color:var(--mut)}
.caveat{font-size:.79rem;color:var(--mut);background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:.85rem 1rem;margin-top:1.5rem}
.caveat li{margin:.35rem 0}.caveat b{color:var(--fg)}
footer{margin-top:1.6rem;font-size:.78rem;color:var(--mut)}footer a{color:var(--mut)}
</style>
</head>
<body class="lang-en">
<div class="wrap">

<h1>How Tax Is Split <span class="zh">中央与地方税收划分</span></h1>
<p class="sub">
  <span data-l="The statutory sharing rules, what they yield, and why local government still cannot fund itself|法定分成规则、由此产生的收入分配，以及地方为何仍无法自给"></span> ·
  <a href="index.html" data-l="&larr; all data|&larr; 全部数据"></a> ·
  <a href="fiscal-monitor.html" data-l="Fiscal Monitor|财政运行监测"></a> ·
  <a href="spending.html" data-l="Spending Composition|支出构成"></a>
</p>

<div class="controls">
  <span class="lbl" data-l="language|语言"></span>
  <div class="seg" id="lang"><button data-v="en" class="on">EN</button><button data-v="zh">中文</button></div>
</div>

<div class="kpis" id="kpis"></div>

<section>
  <div class="shead"><h2><span data-l="1 · The rule|一 · 规则"></span></h2>
    <p data-l="What each tax line is worth, and the statutory share of it that goes to each level. Ordered by size, so the taxes that decide the split sit at the top.|各税种的规模，以及法定分成比例。按规模排序，决定分配格局的税种列在最上方。"></p></div>
  <div class="card">
    <h3><span data-l="Statutory split by tax|分税种法定分成"></span></h3>
    <p class="note" data-l="Share of each tax, %. Export rebates are a refund the centre pays out, not a receipt.|各税种分成占比，%。出口退税为中央支付的退库，非收入。"></p>
    <div id="c_rule" class="chart"></div>
  </div>
  <div class="card">
    <h3><span data-l="…and what that is in money|…折算成金额"></span></h3>
    <p class="note" id="moneynote"></p>
    <div id="c_money" class="chart"></div>
  </div>
</section>

<section>
  <div class="shead"><h2><span data-l="2 · The outturn|二 · 实际结果"></span></h2>
    <p data-l="The reported split of the general public budget. It is not the rule applied to the tax take: it also carries non-tax revenue, and central revenue is measured before the transfers that fund most local spending.|一般公共预算的实际分配。并非规则直接折算：其中还包含非税收入，且中央收入为转移支付前口径，而地方支出主要依靠转移支付。"></p></div>
  <div class="row2">
    <div class="card">
      <h3><span data-l="Local share of revenue vs of spending|地方占收入与支出的比重"></span></h3>
      <p class="note" data-l="Cumulative year-to-date, %. The gap between the two lines is the vertical fiscal imbalance.|年初累计，%。两线之差即纵向财政失衡。"></p>
      <div id="c_share" class="chart sm"></div>
    </div>
    <div class="card">
      <h3><span data-l="Local own revenue vs local spending|地方本级收入与地方支出"></span></h3>
      <p class="note" data-l="Full calendar years, RMB bn. The shortfall is closed by central transfers and local borrowing.|全年，十亿元。缺口由中央转移支付与地方举债弥补。"></p>
      <div id="c_gap" class="chart sm"></div>
    </div>
  </div>
</section>

<section>
  <div class="shead"><h2><span data-l="3 · Where the rules come from|三 · 规则出处"></span></h2>
    <p data-l="Every ratio on this page traces to a State Council decision. Superseded ratios are not shown.|本页每一比例均可追溯至国务院决定。已被取代的比例不予列示。"></p></div>
  <div class="card"><table class="src" id="srctable"></table></div>
</section>

<div class="caveat">
  <ul>
    <li><b data-l="Estimate, not outturn.|估算，非决算。"></b>
      <span data-l="Section 1 applies the statutory ratio to the national tax take. It ignores the carve-outs written into the rules — income tax from the railways, the major state banks, the policy banks, PetroChina, Sinopec and offshore oil firms is 100% central and never enters the 60/40 split — so it overstates the local share of income tax.|第一部分以法定比例折算全国税收，未扣除规则中的例外：铁路、国有大型银行、政策性银行、中石油、中石化及海洋石油企业的所得税全额归中央，不参与六四分成，故高估了地方所得税份额。"></span></li>
    <li><b data-l="Two lines carry no ratio.|两个税种无单一比例。"></b>
      <span data-l="Stamp duty bundles securities transaction stamp duty (100% central since 2016) with all other stamp duty (100% local); “other taxes” is a residual of several small taxes on different rules. Both are shown as unallocated rather than guessed.|印花税包含证券交易印花税（2016年起全额归中央）与其他印花税（全额归地方）；“其他税收”为若干小税种的残差。两者列为未分配，不作推测。"></span></li>
    <li><b data-l="Local revenue here is own revenue.|地方收入为本级口径。"></b>
      <span data-l="地方一般公共预算本级收入 excludes transfers received, while 地方一般公共预算支出 includes transfer-funded spending. That is exactly why the two lines in section 2 diverge, and it is a definitional gap, not a deficit.|地方一般公共预算本级收入不含所获转移支付，而地方一般公共预算支出含转移支付所支撑的支出。这正是第二部分两线背离的原因，属口径差异而非赤字。"></span></li>
  </ul>
</div>

<footer>
  <span data-l="Rules: State Council decisions as listed. Outturn: MOF 全国财政收支情况, monthly.|规则：国务院相关决定。实际数据：财政部《全国财政收支情况》月度发布。"></span><br>
  Data &copy; Ministry of Finance, PRC &middot; built for <a href="https://github.com/yqcao/China-Fiscal-Data">github.com/yqcao/China-Fiscal-Data</a>
</footer>
</div>

<script>
const P = __PAYLOAD__;
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
const AX = dark ? '#9aa' : '#666', GRID = dark ? '#2c2e33' : '#eee',
      FG = dark ? '#e6e6e6' : '#1a1a1a', CARD = dark ? '#1e1f23' : '#fff';
/* Two levels of government = two categorical hues, taken in the fixed documented
   order and validated for CVD separation and contrast on both card surfaces.
   Unallocated is deliberately NOT a third hue - it is an absence of data, so it
   wears a neutral grey and can never be read as a third level of government. */
const CEN = dark ? '#3987e5' : '#2a78d6',
      LOC = dark ? '#d95926' : '#eb6834',
      UNK = dark ? '#6b6f76' : '#b6b8bd';
let lang = 'en';
const L = (e, z) => lang === 'en' ? e : z;
const nm = t => L(t.en, t.cn);
const bn = x => x == null ? '–' : x === 0 ? '0'
      : Math.abs(x) >= 1000 ? (x / 1000).toFixed(2) + 'tn'
      : Math.round(x).toLocaleString() + 'bn';

function applyL(){
  document.querySelectorAll('[data-l]').forEach(e=>{
    const a = e.getAttribute('data-l'), i = a.indexOf('|');
    e.innerHTML = lang === 'en' ? a.slice(0, i) : a.slice(i + 1);
  });
}
const charts = {};
const mk = id => charts[id] = echarts.init(document.getElementById(id));

function kpis(){
  const k = P.kpi;
  const cards = [
    [L('Local share of revenue','地方占收入'),  k.rev_loc + '%',
     L('general public budget, '+k.period,'一般公共预算，'+k.period)],
    [L('Local share of spending','地方占支出'), k.exp_loc + '%',
     L('general public budget, '+k.period,'一般公共预算，'+k.period)],
    [L('Local spending gap','地方支出缺口'),    'RMB ' + bn(k.gap),
     L('local spending less local own revenue','地方支出减地方本级收入')],
    [L('Statutory split of tax','税收法定分成'), k.est_c_pct + '% / ' + (100 - k.est_c_pct).toFixed(1) + '%',
     L('centre / local, '+k.year+' tax take','中央/地方，'+k.year+'年税收')],
  ];
  document.getElementById('kpis').innerHTML = cards.map(([a,b,c])=>
    `<div class="kpi"><div class="k">${a}</div><div class="n">${b}</div><div class="s">${c}</div></div>`).join('');
}

/* 1 - statutory share per tax, 100% stacked bars, biggest tax at the top */
function drawRule(){
  const T = P.taxes.slice().reverse();          // ECharts y-axis runs bottom-up
  const s = (name, col, pick) => ({name, type:'bar', stack:'r', itemStyle:{color:col},
      barMaxWidth:16, data:T.map(pick), emphasis:{focus:'series'}});
  charts.c_rule.setOption({grid:{left:8,right:60,top:34,bottom:28,containLabel:true},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('Central','中央'),L('Local','地方'),L('No single ratio','无单一比例')]},
    tooltip:{trigger:'item',formatter:p=>{
      const t = T[p.dataIndex];
      return `<b>${nm(t)}</b><br>${p.seriesName}: ${p.value}%<br>` +
             `${L('Size','规模')}: RMB ${bn(t.amt)} (${P.kpi.year})` +
             (t.note ? `<br><span style="opacity:.7">${t.note.slice(0,110)}…</span>` : '');}},
    xAxis:{type:'value',max:100,axisLabel:{color:AX,formatter:'{value}%'},splitLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'category',data:T.map(nm),axisLabel:{color:AX,fontSize:11},axisLine:{lineStyle:{color:GRID}}},
    series:[s(L('Central','中央'), CEN, t=>t.c_pct),
            s(L('Local','地方'),   LOC, t=>t.l_pct),
            s(L('No single ratio','无单一比例'), UNK, t=>t.c_pct==null?100:null)]},true);
}

/* 2 - the same taxes as money */
function drawMoney(){
  const T = P.taxes.slice().reverse();
  const s = (name, col, pick) => ({name, type:'bar', stack:'m', itemStyle:{color:col},
      barMaxWidth:16, data:T.map(pick), emphasis:{focus:'series'}});
  charts.c_money.setOption({grid:{left:8,right:60,top:34,bottom:28,containLabel:true},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('Central','中央'),L('Local','地方'),L('Unallocated','未分配')]},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},
      valueFormatter:v=>v==null?'–':'RMB '+bn(v)},
    xAxis:{type:'value',axisLabel:{color:AX,formatter:v=>bn(v)},splitLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'category',data:T.map(nm),axisLabel:{color:AX,fontSize:11},axisLine:{lineStyle:{color:GRID}}},
    series:[s(L('Central','中央'), CEN, t=>t.c_amt),
            s(L('Local','地方'),   LOC, t=>t.l_amt),
            s(L('Unallocated','未分配'), UNK, t=>t.c_amt==null?t.amt:null)]},true);
  document.getElementById('moneynote').innerHTML = L(
    `Statutory ratio applied to the ${P.kpi.year} tax take, RMB bn. An estimate — see the note at the foot of the page.`,
    `以法定比例折算 ${P.kpi.year} 年税收，十亿元。为估算口径，参见页末说明。`);
}

/* 3 - local share of revenue vs of spending */
function drawShare(){
  const S = P.ser, X = S.map(r=>r.period);
  const line = (name,col,pick)=>({name,type:'line',smooth:true,showSymbol:false,
      lineStyle:{width:2.2,color:col},itemStyle:{color:col},data:S.map(pick)});
  charts.c_share.setOption({grid:{left:44,right:16,top:30,bottom:48},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX}},
    tooltip:{trigger:'axis',valueFormatter:v=>v==null?'–':v.toFixed(1)+'%'},
    xAxis:{type:'category',data:X,axisLabel:{color:AX,rotate:45,fontSize:9},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',min:40,max:100,axisLabel:{color:AX,formatter:'{value}%'},splitLine:{lineStyle:{color:GRID}}},
    series:[line(L('Local share of spending','地方占支出'), LOC, r=>+(r.exp_l/(r.exp_c+r.exp_l)*100).toFixed(1)),
            line(L('Local share of revenue','地方占收入'),  CEN, r=>+(r.rev_l/(r.rev_c+r.rev_l)*100).toFixed(1))]},true);
}

/* 4 - the gap, in money, by full calendar year */
function drawGap(){
  const Y = P.years, X = Y.map(r=>r.year);
  charts.c_gap.setOption({grid:{left:52,right:16,top:30,bottom:34},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX}},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:v=>'RMB '+bn(v)},
    xAxis:{type:'category',data:X,axisLabel:{color:AX},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',axisLabel:{color:AX,formatter:v=>bn(v)},splitLine:{lineStyle:{color:GRID}}},
    series:[{name:L('Local own revenue','地方本级收入'),type:'bar',barMaxWidth:34,
             itemStyle:{color:CEN},data:Y.map(r=>r.rev_l)},
            {name:L('Local spending','地方支出'),type:'bar',barMaxWidth:34,
             itemStyle:{color:LOC},data:Y.map(r=>r.exp_l),
             label:{show:true,position:'top',color:AX,fontSize:10,
                    formatter:p=>'+'+bn(Y[p.dataIndex].exp_l-Y[p.dataIndex].rev_l)}}]},true);
}

function srctable(){
  document.getElementById('srctable').innerHTML = P.taxes.filter(t=>t.src.length).map(t=>
    `<tr><td>${nm(t)}</td><td>${t.src.join('<br>')}${t.note?'<br><i>'+t.note+'</i>':''}</td></tr>`).join('');
}

function all(){ kpis(); drawRule(); drawMoney(); drawShare(); drawGap(); srctable(); }

['c_rule','c_money','c_share','c_gap'].forEach(mk);
document.getElementById('lang').onclick = e => {
  if (e.target.tagName !== 'BUTTON') return;
  lang = e.target.dataset.v;
  [...e.currentTarget.children].forEach(b => b.classList.toggle('on', b === e.target));
  document.body.classList.toggle('lang-en', lang === 'en');
  applyL(); all();
};
addEventListener('resize', () => Object.values(charts).forEach(c => c.resize()));
applyL(); all();
</script>
</body>
</html>
'''

HTML = HTML.replace('__PAYLOAD__', P)
open(BASE + 'tax-split.html', 'w', encoding='utf-8').write(HTML)
print(f'wrote tax-split.html {round(len(HTML)/1024,1)} KB')
print(f'  rules   {len(taxes)} tax lines, {sum(1 for t in taxes if t["c_amt"] is None)} unallocated')
print(f'  {year}    statutory estimate: centre RMB {est_c:,.0f}bn / local RMB {est_l:,.0f}bn'
      f'  ({kpi["est_c_pct"]}% / {100-kpi["est_c_pct"]:.1f}%), unallocated RMB {unalloc:,.0f}bn')
print(f'  outturn {len(ser)} periods {ser[0]["period"]}..{ser[-1]["period"]};'
      f' local {kpi["rev_loc"]}% of revenue, {kpi["exp_loc"]}% of spending')
