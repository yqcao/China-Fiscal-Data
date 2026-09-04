#!/usr/bin/env python3
"""Build growth-targets.html — provincial GDP growth targets on a map.

Reads data/prov-reports/targets.json (extracted from each province's own work
report) and data/prov-reports/sources.json (the URL registry, including the
provinces whose portal could not be reached), plus the province boundaries in
data/geo/china-provinces.json.

The map colours the midpoint of each target, because a third of provinces publish
a range ("4.5%—5%") rather than a point. The ranked chart beside it shows the
range itself, since a choropleth cannot express an interval and area misleads on
magnitude anyway — Tibet is large and Shanghai is not.

Provinces with no retrieved report are drawn in a neutral grey that is outside
the data ramp, so "not retrieved" can never read as a low target.
"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'

tg   = json.load(open(BASE + 'data/prov-reports/targets.json', encoding='utf-8'))
reg  = json.load(open(BASE + 'data/prov-reports/sources.json', encoding='utf-8'))
geo  = json.load(open(BASE + 'data/geo/china-provinces.json', encoding='utf-8'))

YEAR = max(r['year'] for r in tg)
have = {r['cn']: r for r in tg if r['year'] == YEAR}

# every province, whether or not its report came down
rows = []
for p in reg['provinces']:
    r = have.get(p['cn'])
    rows.append({
        'cn': p['cn'], 'en': p['en'], 'code': p['code'], 'domain': p['domain'],
        'low': r['low'] if r else None, 'high': r['high'] if r else None,
        'mid': round((r['low'] + r['high']) / 2, 2) if r else None,
        'phrasing': r['phrasing'] if r else '',
        'sentence': r['sentence'] if r else '',
        'url': (p['reports'].get(str(YEAR)) or ''),
        'tier': (p.get('tier') or {}).get(str(YEAR), 'portal' if p['reports'] else ''),
        'status': 'ok' if r else ('no-url' if not p['reports'] else 'unreachable'),
    })
rows.sort(key=lambda x: (x['mid'] is None, -(x['mid'] or 0), x['cn']))

got = [x for x in rows if x['mid'] is not None]
P = json.dumps({'year': YEAR, 'rows': rows, 'geo': geo,
                'n_have': len(got), 'n_all': len(rows),
                'lo': min(x['mid'] for x in got), 'hi': max(x['mid'] for x in got)},
               ensure_ascii=False, separators=(',', ':'))

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Provincial Growth Targets · 各省增长目标</title>
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
.controls{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:1.2rem}
.seg{display:inline-flex;border:1px solid var(--bd);border-radius:9px;overflow:hidden;background:var(--card)}
.seg button{border:0;background:transparent;color:var(--fg);padding:.45rem .8rem;font-size:.85rem;cursor:pointer}
.seg button.on{background:var(--accent);color:#fff}
.lbl{font-size:.78rem;color:var(--mut);margin-right:.1rem}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.8rem;margin-bottom:1.3rem}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:.8rem .9rem}
.kpi .k{font-size:.76rem;color:var(--mut)}
.kpi .n{font-size:1.45rem;font-weight:660;margin:.1rem 0 0}
.kpi .s{font-size:.74rem;color:var(--mut)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1rem .5rem;margin-bottom:1.1rem}
.card h3{font-size:.98rem;margin:.1rem 0 .15rem;font-weight:650}
.card .note{font-size:.77rem;color:var(--mut);margin:.2rem 0 .45rem}
#c_map{width:100%;height:560px}
#c_bar{width:100%;height:620px}
.row2{display:grid;grid-template-columns:1.15fr 1fr;gap:1.1rem}
@media(max-width:900px){.row2{grid-template-columns:1fr}#c_map{height:420px}}
table.src{width:100%;border-collapse:collapse;font-size:.78rem}
table.src th{text-align:left;font-weight:650;padding:.35rem .4rem;border-bottom:1px solid var(--bd);color:var(--mut)}
table.src td{padding:.32rem .4rem;border-top:1px solid var(--bd);vertical-align:top}
table.src td a{color:var(--accent);word-break:break-all}
.pill{display:inline-block;font-size:.7rem;padding:.05rem .4rem;border-radius:6px;border:1px solid var(--bd);color:var(--mut)}
.caveat{font-size:.79rem;color:var(--mut);background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:.85rem 1rem;margin-top:1.4rem}
.caveat li{margin:.35rem 0}.caveat b{color:var(--fg)}
footer{margin-top:1.6rem;font-size:.78rem;color:var(--mut)}footer a{color:var(--mut)}
</style>
</head>
<body class="lang-en">
<div class="wrap">

<h1>Provincial Growth Targets <span class="zh">各省经济增长目标</span></h1>
<p class="sub">
  <span data-l="The GDP growth target each province set for itself, read from its own government work report|各省在本省政府工作报告中提出的地区生产总值增长目标"></span> ·
  <a href="index.html" data-l="&larr; all data|&larr; 全部数据"></a> ·
  <a href="fiscal-monitor.html" data-l="Fiscal Monitor|财政运行监测"></a> ·
  <a href="tax-split.html" data-l="Tax Split|税收划分"></a>
</p>

<div class="controls">
  <span class="lbl" data-l="language|语言"></span>
  <div class="seg" id="lang"><button data-v="en" class="on">EN</button><button data-v="zh">中文</button></div>
</div>

<div class="kpis" id="kpis"></div>

<div class="row2">
  <div class="card">
    <h3><span data-l="Target by province|分省目标"></span></h3>
    <p class="note" data-l="Midpoint of the published target. Grey = report not retrieved, not a low target.|按公布目标的中值着色。灰色表示未取得报告，并非低目标。"></p>
    <div id="c_map"></div>
  </div>
  <div class="card">
    <h3><span data-l="Ranked, with the published range|排序及目标区间"></span></h3>
    <p class="note" data-l="A bar per province. Where a range was published, the bar spans it.|每省一条。公布区间的，条形覆盖整个区间。"></p>
    <div id="c_bar"></div>
  </div>
</div>

<div class="card">
  <h3><span data-l="Every province, with its source|全部省份及出处"></span></h3>
  <p class="note" data-l="Each link goes to the province's own official site. Nothing here comes from an aggregator or a news compilation.|每条链接均指向该省官方网站。本页不使用任何汇编或新闻转载来源。"></p>
  <div style="overflow-x:auto"><table class="src" id="srctable"></table></div>
</div>

<div class="caveat">
  <ul>
    <li><b data-l="Colour is the midpoint.|着色为区间中值。"></b>
      <span data-l="A third of provinces publish a range rather than a point. The map has one colour per province so it shows the midpoint; the ranked chart beside it shows the actual range. &ldquo;5% 以上&rdquo; and &ldquo;5% 左右&rdquo; are both plotted at 5.0 — the qualifier is in the tooltip and the table, because there is no defensible number to add or subtract for it.|约三分之一省份公布的是区间而非点值。地图每省仅一色，故以中值着色；右侧排序图显示实际区间。&ldquo;5%以上&rdquo;与&ldquo;5%左右&rdquo;均按 5.0 绘制——限定语见提示框与下表，因无法为其加减一个有依据的数值。"></span></li>
    <li><b data-l="Grey is missing data, not a low target.|灰色为缺失数据，非低目标。"></b>
      <span data-l="Grey provinces sit outside the colour ramp entirely. Their reports could not be retrieved: several provincial portals are unreachable from outside China, three reject non-browser clients, and one publishes its full text only through a script-rendered index. Each still has its official URL in the table below.|灰色省份完全不在色阶之内。其报告未能取得：部分省级门户在境外无法访问，三个拒绝非浏览器访问，一个仅通过脚本渲染的索引发布全文。下表仍列出各自的官方网址。"></span></li>
    <li><b data-l="Targets are not forecasts.|目标不是预测。"></b>
      <span data-l="These are the numbers each provincial government set for itself and put to its own people's congress. Provinces have historically set targets above what they then achieved, and the sum of provincial targets does not have to equal the national one.|这些是各省政府自行设定并提交本级人民代表大会的目标。历史上各省目标常高于实际完成值，且各省目标之和不必等于全国目标。"></span></li>
  </ul>
</div>

<footer>
  <span data-l="Source: each province's own government work report, from that province's official website. Boundaries: DataV.GeoAtlas province boundaries.|来源：各省政府工作报告，取自该省官方网站。行政区划边界：DataV.GeoAtlas。"></span><br>
  built for <a href="https://github.com/yqcao/China-Fiscal-Data">github.com/yqcao/China-Fiscal-Data</a>
</footer>
</div>

<script>
const P = __PAYLOAD__;
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
const AX = dark ? '#9aa' : '#666', GRID = dark ? '#2c2e33' : '#eee',
      FG = dark ? '#e6e6e6' : '#1a1a1a', CARD = dark ? '#1e1f23' : '#fff',
      BD = dark ? '#2c2e33' : '#e3e3e6';
/* Sequential = ONE hue, light to dark. Magnitude is not identity, so this is a
   ramp and not the categorical palette. "No data" is a neutral grey deliberately
   off the ramp — it must never read as the bottom of the scale. */
const RAMP = dark ? ['#184f95','#256abf','#2a78d6','#3987e5','#6da7ec','#9ec5f4']
                  : ['#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95'];
/* The choropleth may use the full ramp — a filled region carries its own area.
   The dot plot may not: discrete marks need the step nearest the surface to
   clear 2:1, so the dots start one stop in from each end. */
const DOTS = dark ? ['#184f95','#256abf','#2a78d6','#3987e5','#5598e7','#86b6ef']
                  : ['#86b6ef','#5598e7','#3987e5','#2a78d6','#256abf','#184f95'];
const NODATA = dark ? '#3a3d43' : '#dcdde0';
let lang = 'en';
const L = (e, z) => lang === 'en' ? e : z;
const nm = r => lang === 'en' ? r.en : r.cn;
/* Render the target the way the province wrote it, qualifier and all. */
function shown(r){
  if (r.low == null) return L('not retrieved','未取得');
  const base = r.high !== r.low ? r.low + '–' + r.high + '%' : r.low + '%';
  const q = {'左右':L(' (around)','左右'), '以上':L(' (or more)','以上'),
             '以内':L(' (or less)','以内'), '区间':''}[r.phrasing] || '';
  return base + q;
}
function applyL(){
  document.querySelectorAll('[data-l]').forEach(e=>{
    const a = e.getAttribute('data-l'), i = a.indexOf('|');
    e.innerHTML = lang === 'en' ? a.slice(0, i) : a.slice(i + 1);
  });
}
const charts = {};
echarts.registerMap('china', P.geo);

function kpis(){
  const g = P.rows.filter(r=>r.mid!=null);
  const mean = g.reduce((s,r)=>s+r.mid,0)/g.length;
  const top = g[0];
  const cards = [
    [L('Provinces with a target','已取得目标省份'), P.n_have + ' / ' + P.n_all,
     L('read from the province’s own report','取自各省本级报告')],
    [L('Range across provinces','各省区间'), P.lo + '% – ' + P.hi + '%',
     L('midpoint of each published target','按各省目标中值')],
    [L('Unweighted mean','简单平均'), mean.toFixed(2) + '%',
     L('of the provinces retrieved','已取得省份的算术平均')],
    [L('Highest','最高'), nm(top) + ' ' + shown(top),
     L('year ' + P.year + ' target','' + P.year + '年目标')],
  ];
  document.getElementById('kpis').innerHTML = cards.map(([a,b,c])=>
    `<div class="kpi"><div class="k">${a}</div><div class="n">${b}</div><div class="s">${c}</div></div>`).join('');
}

function drawMap(){
  const data = P.rows.map(r=>({name:r.cn, value:r.mid, _r:r}));
  charts.map.setOption({
    textStyle:{color:FG},
    tooltip:{trigger:'item', formatter:p=>{
      const r = (p.data && p.data._r); if(!r) return p.name;
      return `<b>${nm(r)}</b><br>${L('Target','目标')}: ${shown(r)}` +
             (r.mid==null ? `<br><span style="opacity:.7">${L('report not retrieved','未取得报告')}</span>` : '');
    }},
    visualMap:{ type:'continuous', min:P.lo, max:P.hi, left:12, bottom:14,
      inRange:{color:RAMP}, calculable:true, textStyle:{color:AX},
      text:[P.hi+'%', P.lo+'%'] },
    series:[{ type:'map', map:'china', roam:false, data,
      itemStyle:{areaColor:NODATA, borderColor:BD, borderWidth:.6},
      emphasis:{label:{show:false}, itemStyle:{areaColor:null, borderColor:FG, borderWidth:1.2}},
      select:{disabled:true} }]
  }, true);
}

function drawBar(){
  const g = P.rows.filter(r=>r.mid!=null).slice().reverse();   // y-axis runs bottom-up
  const floor = Math.floor(P.lo*2)/2 - 0.5;
  const ramp = DOTS;
  const hue = r => ramp[Math.min(ramp.length-1,
      Math.round(((r.mid-P.lo)/((P.hi-P.lo)||1))*(ramp.length-1)))];
  // Most provinces publish a point, not a range, so the dot is the primary mark
  // and the bar behind it shows the interval where there is one. Colours are
  // precomputed per datum: an itemStyle.color callback silently yields no fill.
  charts.bar.setOption({
    grid:{left:8,right:96,top:12,bottom:28,containLabel:true}, textStyle:{color:FG},
    tooltip:{trigger:'axis', axisPointer:{type:'shadow'}, formatter:p=>{
      const r = g[p[0].dataIndex];
      return `<b>${nm(r)}</b><br>${L('Target','目标')}: ${shown(r)}<br>` +
             `<span style="opacity:.7">${r.domain}</span>`;
    }},
    xAxis:{type:'value', min:floor, max:Math.ceil(P.hi*2)/2,
      axisLabel:{color:AX, formatter:'{value}%'}, splitLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'category', data:g.map(nm),
      axisLabel:{color:AX, fontSize:10}, axisLine:{lineStyle:{color:GRID}}},
    series:[
      {type:'bar', stack:'b', itemStyle:{color:'transparent'}, silent:true,
       data:g.map(r=>r.low - floor)},
      {type:'bar', stack:'b', barMaxWidth:9,
       data:g.map(r=>({value:Math.max(r.high-r.low, 0.02),
                       itemStyle:{color:hue(r), opacity:.5, borderRadius:2}}))},
      {type:'scatter', symbolSize:11, z:3,
       data:g.map((r,i)=>({value:[r.mid, i], itemStyle:{color:hue(r)}})),
       label:{show:true, position:'right', distance:8, color:AX, fontSize:10,
              formatter:p=>shown(g[p.dataIndex])}}
    ]
  }, true);
}

function table(){
  const st = {ok:L('retrieved','已取得'), unreachable:L('not reachable','无法访问'),
              'no-url':L('no URL found','未找到网址')};
  const tier = {portal:L('provincial portal','省级门户'), dept:L('department site','部门网站'),
                summary:L('official summary','官方摘要'), '':''};
  document.getElementById('srctable').innerHTML =
    `<tr><th>${L('Province','省份')}</th><th>${L('Target','目标')}</th>` +
    `<th>${L('Source','出处')}</th><th>${L('Status','状态')}</th></tr>` +
    P.rows.map(r=>`<tr><td>${nm(r)}</td><td>${shown(r)}</td>` +
      `<td>${r.url?`<a href="${r.url}" target="_blank" rel="noopener">${r.domain}</a> <span class="pill">${tier[r.tier]||''}</span>`:'&ndash;'}</td>` +
      `<td>${st[r.status]}</td></tr>`).join('');
}

function all(){ kpis(); drawMap(); drawBar(); table(); }
charts.map = echarts.init(document.getElementById('c_map'));
charts.bar = echarts.init(document.getElementById('c_bar'));
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
open(BASE + 'growth-targets.html', 'w', encoding='utf-8').write(HTML)
print(f'wrote growth-targets.html {round(len(HTML)/1024,1)} KB')
print(f'  {YEAR}: {len(got)} of {len(rows)} provinces with a target, '
      f'{min(x["mid"] for x in got)}%–{max(x["mid"] for x in got)}%')
miss = [x['cn'] for x in rows if x['mid'] is None]
if miss: print(f'  no target ({len(miss)}): {" ".join(miss)}')
