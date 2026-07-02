#!/usr/bin/env python3
"""Build cpi.html from data/macro/cpi_series.json (CPI YoY line + MoM bars)."""
import json, os
base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
CPI=json.dumps(json.load(open(base+'data/macro/cpi_series.json')), ensure_ascii=False, separators=(',',':'))

HTML=r'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>China CPI Monitor · 中国CPI月度监测</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{color-scheme:light dark;--bg:#f7f7f8;--fg:#1a1a1a;--card:#fff;--bd:#e3e3e6;--mut:#666;--accent:#c00;--up:#16a34a;--down:#dc2626;}
@media(prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#e6e6e6;--card:#1e1f23;--bd:#2c2e33;--mut:#9aa;--accent:#ff6b6b;}}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",Helvetica,Arial,sans-serif;background:var(--bg);color:var(--fg);line-height:1.5}
body.lang-en .zh{display:none}
.wrap{max-width:1000px;margin:0 auto;padding:2rem 1.1rem 4rem}
h1{font-size:1.6rem;margin:0 0 .15rem}
h1 .zh{font-size:1rem;color:var(--mut);font-weight:400;display:block;margin-top:.1rem}
.sub{color:var(--mut);margin:.2rem 0 1.3rem;font-size:.9rem}.sub a{color:var(--accent)}
.controls{margin-bottom:1.2rem}
.seg{display:inline-flex;border:1px solid var(--bd);border-radius:9px;overflow:hidden;background:var(--card)}
.seg button{border:0;background:transparent;color:var(--fg);padding:.45rem .8rem;font-size:.85rem;cursor:pointer}
.seg button.on{background:var(--accent);color:#fff}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:.8rem;margin-bottom:1.3rem}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:.85rem .95rem}
.kpi .t{font-size:.78rem;color:var(--mut)} .kpi .v{font-size:1.5rem;font-weight:650;margin-top:.1rem}
.up{color:var(--up)}.down{color:var(--down)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1rem .5rem}
.card h3{font-size:1rem;margin:.1rem 0 .1rem}.card .note{font-size:.78rem;color:var(--mut);margin:0 0 .4rem}
.chart{width:100%;height:420px}
footer{margin-top:1.5rem;font-size:.78rem;color:var(--mut)}footer a{color:var(--mut)}
</style></head>
<body class="lang-en"><div class="wrap">
<h1>China CPI Monitor <span class="zh">中国CPI月度监测</span></h1>
<p class="sub"><span data-l="Consumer Price Index, monthly|居民消费价格指数，月度"></span> · <a href="index.html">&larr; all data</a> · <a href="fiscal-monitor.html" data-l="Fiscal Monitor|财政运行监测"></a> · <span data-l="Source|来源"></span>: <a href="https://www.stats.gov.cn/sj/zxfb/">NBS 国家统计局</a></p>
<div class="controls"><span class="seg" id="lang"><button data-v="en" class="on">EN</button><button data-v="zh">中文</button></span></div>
<div class="kpis" id="kpi"></div>
<div class="card"><h3 data-l="CPI Inflation|CPI 通胀"></h3>
  <p class="note" data-l="Line: year-on-year % (left) · Bars: month-on-month % (right)|线：同比 %（左）· 柱：环比 %（右）"></p>
  <div id="c" class="chart"></div></div>
<footer><span data-l="Data: National Bureau of Statistics (NBS) · built for|数据：国家统计局 · 构建于"></span>
 <a href="https://github.com/yqcao/China-Fiscal-Data">github.com/yqcao/China-Fiscal-Data</a></footer>
</div>
<script>
const CPI=__CPI__;
const dark=matchMedia('(prefers-color-scheme: dark)').matches;
const AX=dark?'#9aa':'#666',GRID=dark?'#2c2e33':'#eee',FG=dark?'#e6e6e6':'#1a1a1a';
let lang='en';const L=(e,z)=>lang==='en'?e:z;
const periods=CPI.map(r=>r.period);
const chart=echarts.init(document.getElementById('c'));
function applyL(){document.querySelectorAll('[data-l]').forEach(e=>{const[a,b]=e.getAttribute('data-l').split('|');e.textContent=lang==='en'?a:b;});}
function fmt(v){return v==null?'–':(v>=0?'+':'')+v+'%';}
function kpis(){
  const last=CPI[CPI.length-1];
  document.getElementById('kpi').innerHTML=[
    [L('CPI (YoY)','CPI 同比'),last.yoy,last.period],
    [L('CPI (MoM)','CPI 环比'),last.mom,last.period],
  ].map(([t,v,p])=>`<div class="kpi"><div class="t">${t} · ${p}</div><div class="v ${v>=0?'up':'down'}">${fmt(v)}</div></div>`).join('');
}
function draw(){
  chart.setOption({grid:{left:44,right:44,top:30,bottom:52},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('YoY %','同比 %'),L('MoM %','环比 %')]},
    tooltip:{trigger:'axis',valueFormatter:v=>v==null?'–':v+'%'},
    xAxis:{type:'category',data:periods,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    yAxis:[{type:'value',name:'YoY %',axisLabel:{color:AX,formatter:'{value}%'},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
           {type:'value',name:'MoM %',axisLabel:{color:AX,formatter:'{value}%'},splitLine:{show:false},nameTextStyle:{color:AX}}],
    series:[
      {name:L('MoM %','环比 %'),type:'bar',yAxisIndex:1,itemStyle:{color:'#8ab4ff',opacity:.7},data:CPI.map(r=>r.mom)},
      {name:L('YoY %','同比 %'),type:'line',smooth:true,showSymbol:false,lineStyle:{width:2.4,color:'#c00'},itemStyle:{color:'#c00'},
       areaStyle:{opacity:.05,color:'#c00'},data:CPI.map(r=>r.yoy),
       markLine:{silent:true,symbol:'none',lineStyle:{color:AX,type:'dashed',opacity:.4},data:[{yAxis:0}]}}]},true);
}
function render(){applyL();kpis();draw();}
document.querySelectorAll('#lang button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#lang button').forEach(x=>x.classList.remove('on'));b.classList.add('on');lang=b.dataset.v;document.body.classList.toggle('lang-en',lang==='en');render();});
addEventListener('resize',()=>chart.resize());
render();
</script></body></html>'''
open(base+'cpi.html','w',encoding='utf-8').write(HTML.replace('__CPI__',CPI))
print('wrote cpi.html')
