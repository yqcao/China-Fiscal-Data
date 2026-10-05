#!/usr/bin/env python3
"""Build prov-debt.html — provincial new-debt quota, issuance and execution, annual.

Reads data/celma/prov_panel.json (MOF's 地方政府债券信息公开平台, via fetch_celma.py
and build_prov_debt_panel.py) and the province boundaries in data/geo/.

Why a map AND a ranked chart: a choropleth shows where, but area misleads on
magnitude — Tibet is large and Shanghai is not — so every level is also drawn as a
ranked bar. The scatter carries the one relationship worth seeing directly, debt
burden against how much of the year's quota a province actually issued.

The 5 计划单列市 (Dalian, Ningbo, Xiamen, Qingdao, Shenzhen) and the XPCC issue
their own bonds and are reported separately from their province. The map has no
geometry for them, so it folds them into the parent province and says so; the
table keeps them as their own rows.
"""
import json, os
from page_footer import footer

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
panel = json.load(open(BASE + 'data/celma/prov_panel.json', encoding='utf-8'))
geo = json.load(open(BASE + 'data/geo/china-provinces.json', encoding='utf-8'))

EN = {'北京市':'Beijing','天津市':'Tianjin','河北省':'Hebei','山西省':'Shanxi','内蒙古自治区':'Inner Mongolia',
 '辽宁省':'Liaoning','吉林省':'Jilin','黑龙江省':'Heilongjiang','上海市':'Shanghai','江苏省':'Jiangsu',
 '浙江省':'Zhejiang','安徽省':'Anhui','福建省':'Fujian','江西省':'Jiangxi','山东省':'Shandong',
 '河南省':'Henan','湖北省':'Hubei','湖南省':'Hunan','广东省':'Guangdong','广西壮族自治区':'Guangxi',
 '海南省':'Hainan','重庆市':'Chongqing','四川省':'Sichuan','贵州省':'Guizhou','云南省':'Yunnan',
 '西藏自治区':'Tibet','陕西省':'Shaanxi','甘肃省':'Gansu','青海省':'Qinghai','宁夏回族自治区':'Ningxia',
 '新疆维吾尔自治区':'Xinjiang','大连市':'Dalian','宁波市':'Ningbo','厦门市':'Xiamen','青岛市':'Qingdao',
 '深圳市':'Shenzhen','新疆生产建设兵团':'Xinjiang Corps'}
PARENT = {'大连市':'辽宁省','宁波市':'浙江省','厦门市':'福建省','青岛市':'山东省','深圳市':'广东省'}

rows = panel['rows']
comp = {int(k): v for k, v in panel['completeness'].items()}
YEARS = sorted({r['year'] for r in rows if any(
    r.get(k) for k in ('quota_total', 'issue_new_total', 'bal_total'))})

out = []
for r in rows:
    if r['year'] not in YEARS: continue
    out.append({'cn': r['region'], 'en': EN.get(r['region'], r['region']),
                'parent': PARENT.get(r['region']), 'year': r['year'],
                'quota': r['quota_total'], 'issue': r['issue_new_total'],
                'exec': r['execution_pct'], 'refi': r['issue_refi_total'],
                'bal': r['bal_total'], 'dgdp': r['debt_to_gdp_pct'], 'gdp': r['gdp'],
                'ng': r['issue_new_general'], 'ns': r['issue_new_special'],
                'rg': r['issue_refi_general'], 'rs': r['issue_refi_special'],
                'int': (r['interest_general'] or 0) + (r['interest_special'] or 0) or None,
                'rep': (r['repay_general'] or 0) + (r['repay_special'] or 0) or None,
                'rev': r['budget_rev'], 'fund': r['fund_rev']})

P = json.dumps({'rows': out, 'geo': geo, 'years': YEARS,
                'complete': {str(y): comp[y]['complete'] for y in YEARS},
                'parent': PARENT, 'en': EN},
               ensure_ascii=False, separators=(',', ':'))

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Provincial Debt Quota &amp; Execution · 各省新增债务限额与发行</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{color-scheme:light dark;--bg:#f7f7f8;--fg:#1a1a1a;--card:#fff;--bd:#e3e3e6;--mut:#666;--accent:#c00;}
@media(prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#e6e6e6;--card:#1e1f23;--bd:#2c2e33;--mut:#9aa;--accent:#ff6b6b;}}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",Helvetica,Arial,sans-serif;background:var(--bg);color:var(--fg);line-height:1.5}
body.lang-en .zh{display:none}
.wrap{max-width:1140px;margin:0 auto;padding:2rem 1.1rem 4rem}
h1{font-size:1.7rem;margin:0 0 .15rem}
.zh{color:var(--mut);font-weight:400}
h1 .zh{font-size:1.05rem;display:block;margin-top:.1rem}
.sub{color:var(--mut);margin:.2rem 0 1.1rem;font-size:.9rem}.sub a{color:var(--accent)}
.controls{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:1rem}
.seg{display:inline-flex;border:1px solid var(--bd);border-radius:9px;overflow:hidden;background:var(--card);flex-wrap:wrap}
.seg button{border:0;background:transparent;color:var(--fg);padding:.45rem .8rem;font-size:.85rem;cursor:pointer}
.seg button.on{background:var(--accent);color:#fff}
.lbl{font-size:.78rem;color:var(--mut);margin-right:.1rem}
select{background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:8px;padding:.4rem .5rem;font-size:.85rem}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:.8rem;margin-bottom:1.1rem}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:.8rem .9rem}
.kpi .k{font-size:.76rem;color:var(--mut)}
.kpi .n{font-size:1.4rem;font-weight:660;margin:.1rem 0 0}
.kpi .s{font-size:.74rem;color:var(--mut)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1rem .6rem;margin-bottom:1.1rem}
.card h3{font-size:.98rem;margin:.1rem 0 .15rem;font-weight:650}
.card .note{font-size:.77rem;color:var(--mut);margin:.2rem 0 .45rem}
#c_map{width:100%;height:540px}
#c_bar{width:100%;height:640px}
#c_sc{width:100%;height:420px}
#c_tr{width:100%;height:360px}
.row2{display:grid;grid-template-columns:1.1fr 1fr;gap:1.1rem}
@media(max-width:900px){.row2{grid-template-columns:1fr}#c_map{height:400px}#c_bar{height:560px}}
table.tbl{width:100%;border-collapse:collapse;font-size:.79rem}
table.tbl th{text-align:right;font-weight:650;padding:.38rem .45rem;border-bottom:1px solid var(--bd);color:var(--mut);cursor:pointer;white-space:nowrap}
table.tbl th:first-child,table.tbl td:first-child{text-align:left}
table.tbl td{padding:.32rem .45rem;border-top:1px solid var(--bd);text-align:right;white-space:nowrap}
table.tbl tr.sub td:first-child{padding-left:1.3rem;color:var(--mut)}
.tw{overflow-x:auto}
.warn{font-size:.79rem;color:var(--fg);background:rgba(224,123,0,.1);border:1px solid rgba(224,123,0,.45);border-radius:10px;padding:.7rem .9rem;margin-bottom:1rem}
.caveat{font-size:.79rem;color:var(--mut);background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:.85rem 1rem;margin-top:1.3rem}
.caveat li{margin:.35rem 0}.caveat b{color:var(--fg)}
</style>
</head>
<body class="lang-en">
<div class="wrap">
<h1>Provincial Debt Quota &amp; Execution <span class="zh">各省新增债务限额与债券发行</span></h1>
<p class="sub">
  <span data-l="How much new borrowing each province was allowed, and how much it actually issued|各省获批的新增债务限额与实际发行额"></span> ·
  <a href="index.html" data-l="&larr; all data|&larr; 全部数据"></a> ·
  <a href="fiscal-monitor.html" data-l="Fiscal Monitor|财政运行监测"></a> ·
  <a href="#sources" data-l="Sources &amp; disclaimer|数据来源与免责声明"></a>
</p>

<div class="controls">
  <span class="seg" id="lang"><button data-v="en" class="on">EN</button><button data-v="zh">中文</button></span>
  <span class="lbl" style="margin-left:.4rem" data-l="Year|年份"></span>
  <select id="year"></select>
  <span class="lbl" style="margin-left:.4rem" data-l="Map shows|地图指标"></span>
  <span class="seg" id="metric">
    <button data-v="exec" class="on" data-l="Execution %|执行率 %"></button>
    <button data-v="quota" data-l="Quota|限额"></button>
    <button data-v="issue" data-l="Issued|发行额"></button>
    <button data-v="dgdp" data-l="Debt / GDP|债务率"></button>
  </span>
</div>

<div class="warn" id="partial" hidden></div>
<div class="kpis" id="kpi"></div>

<div class="row2">
  <div class="card"><h3 id="h_map"></h3>
    <p class="note" id="n_map"></p><div id="c_map"></div></div>
  <div class="card"><h3 data-l="Ranked|排序"></h3>
    <p class="note" id="n_bar"></p><div id="c_bar"></div></div>
</div>

<div class="card"><h3 data-l="Debt burden vs quota execution|债务率与限额执行率"></h3>
  <p class="note" data-l="Each province: debt outstanding as % of its GDP (x) against the share of its new-debt quota it issued (y). Bubble area = quota size. The provinces that leave quota unused are not the least indebted ones.|每省：债务余额占本省GDP比重（横轴）与新增限额执行率（纵轴）；气泡面积为限额规模。未用完限额的并非债务率最低的省份。"></p>
  <div id="c_sc"></div></div>

<div class="card"><h3 data-l="National quota vs issuance over time|全国限额与发行额历年对比"></h3>
  <p class="note" data-l="Sum of all 37 issuers. Bars: new-debt quota and new-bond issuance. Line: execution rate.|37个发行主体合计。柱：新增债务限额与新增债券发行额；线：执行率。"></p>
  <div id="c_tr"></div></div>

<div class="card"><h3 data-l="All issuers|全部发行主体"></h3>
  <p class="note" data-l="Click a column heading to sort. 亿元 unless marked. The five 计划单列市 and the XPCC are listed under their province but issue separately.|点击表头排序。单位亿元（另有标注除外）。五个计划单列市与新疆生产建设兵团单独发行，列于所属省份之下。"></p>
  <div class="tw"><table class="tbl" id="tbl"></table></div></div>

<div class="caveat">
  <ul>
    <li><b data-l="What the quota is.|限额的含义。"></b>
      <span data-l="新增一般债务限额 + 新增专项债务限额: the additional borrowing the State Council allocated to that region for the year, within the national ceiling the NPC approves each March. It is not the same as the region's total debt ceiling.|新增一般债务限额与新增专项债务限额之和，即国务院在全国人大三月批准的总限额内下达给该地区的当年新增举债额度，与该地区债务限额总额不同。"></span></li>
    <li><b data-l="Execution above 100%.|执行率超过100%。"></b>
      <span data-l="A region may draw on headroom carried over from earlier years (结存限额), so issuance can exceed the current year's allocation. Nationally the regions report more quota than the NPC's headline annual increase for the same reason.|地方可动用往年结存限额，故发行额可超过当年下达额度；全国各地区上报的限额合计高于人大批准的当年新增额，原因相同。"></span></li>
    <li><b data-l="Refinancing is excluded from execution.|执行率不含再融资。"></b>
      <span data-l="Refinancing bonds roll maturing debt and, since the November 2024 NPCSC authorisation, replace hidden debt. They are shown separately and are not measured against the new-debt quota.|再融资债券用于偿还到期债券，2024年11月人大常委会授权后亦用于置换隐性债务；单列显示，不计入新增限额执行率。"></span></li>
    <li><b data-l="Completeness.|数据完整性。"></b>
      <span id="cav_comp"></span></li>
    <li><b data-l="Map geometry.|地图口径。"></b>
      <span data-l="The five 计划单列市 and the XPCC have no separate boundary, so the map folds them into the province that contains them; the table keeps them separate. Boundaries are for drawing only.|五个计划单列市与新疆生产建设兵团无单独边界，地图并入所在省份，表格单列。边界仅用于绘图。"></span></li>
  </ul>
</div>

__FOOTER__
</div>

<script>
const P = __PAYLOAD__;
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
const AX = dark ? '#9aa' : '#666', GRID = dark ? '#2c2e33' : '#eee',
      FG = dark ? '#e6e6e6' : '#1a1a1a', CARD = dark ? '#1e1f23' : '#fff',
      BD = dark ? '#2c2e33' : '#e3e3e6';
/* Sequential = one hue, light to dark: these are magnitudes, not identities.
   Execution gets a diverging ramp instead, because 100% is a real midpoint --
   under and over are different kinds of miss, not more and less of one thing. */
const SEQ = dark ? ['#15243f','#1d3a6b','#2b5fa8','#4e8fd6','#8dbdf0']
                 : ['#eaf1fb','#c3daf4','#8dbdf0','#4e8fd6','#1d3a6b'];
const DIV = ['#b4472f','#d99a62','#e8e2d4','#79b39a','#2f7d5f'];
const ACC = dark ? '#ff6b6b' : '#c00';
/* Open on the newest year whose regions reconcile to the national totals. A
   partial year's headline execution rate is not just noisy, it is wrong -- the
   provinces that have reported issuance but not quota push it far above 100. */
const COMPLETE=P.years.filter(y=>P.complete[y]);
let lang='en', year=(COMPLETE.length?COMPLETE[COMPLETE.length-1]:P.years[P.years.length-1]), metric='exec';
const L=(e,z)=>lang==='en'?e:z;
const charts={};
['c_map','c_bar','c_sc','c_tr'].forEach(id=>charts[id]=echarts.init(document.getElementById(id)));
echarts.registerMap('china', P.geo);

const fmt=v=>v==null?'–':(Math.abs(v)>=10000?(v/10000).toFixed(2)+L(' tn','万亿'):Math.round(v).toLocaleString());
const pct=v=>v==null?'–':v.toFixed(1)+'%';
const rowsOf=y=>P.rows.filter(r=>r.year===y);
const name=r=>L(r.en,r.cn);

/* fold the separately-issuing cities into the province the map can draw */
function mapData(y){
  const by={};
  rowsOf(y).forEach(r=>{
    const key=r.parent||r.cn;
    if(!P.geo.features.some(f=>f.properties.name===key))return;
    const o=by[key]||(by[key]={cn:key,quota:0,issue:0,bal:0,gdp:0,parts:[]});
    o.quota+=r.quota||0; o.issue+=r.issue||0; o.bal+=r.bal||0;
    if(!r.parent)o.gdp=r.gdp||0;
    if(r.parent)o.parts.push(name(r));
  });
  return Object.values(by).map(o=>({...o,
    exec:o.quota?+(o.issue/o.quota*100).toFixed(1):null,
    dgdp:o.gdp?+(o.bal/o.gdp*100).toFixed(1):null}));
}
const METRIC={
  exec:{en:'Execution rate, % of new-debt quota issued',zh:'执行率：新增限额已发行比例',unit:'%',div:true},
  quota:{en:'New-debt quota allocated',zh:'下达新增债务限额',unit:'亿元'},
  issue:{en:'New-bond issuance',zh:'新增债券发行额',unit:'亿元'},
  dgdp:{en:'Debt outstanding / provincial GDP',zh:'债务余额占本省GDP比重',unit:'%'}};

function drawMap(){
  const d=mapData(year), M=METRIC[metric];
  const vals=d.map(o=>o[metric]).filter(v=>v!=null);
  const lo=vals.length?Math.min(...vals):0, hi=vals.length?Math.max(...vals):1;
  /* Execution is bimodal: most provinces land within a point or two of 100 and a
     handful fall far short. A continuous ramp centred on 100 would have to span
     30-170 to hold Tianjin, leaving everyone else an identical neutral. Explicit
     bins keep the thresholds people actually read, and the full-quota line stays
     the break between the two colour directions. */
  const BINS=[{max:50,label:L('under 50%','低于50%'),color:DIV[0]},
              {min:50,max:80,label:'50–80%',color:DIV[1]},
              {min:80,max:95,label:'80–95%',color:DIV[2]},
              {min:95,max:105,label:L('95–105% (full)','95–105%（用满）'),color:DIV[3]},
              {min:105,label:L('over 105%','超过105%'),color:DIV[4]}];
  const opt={
    backgroundColor:'transparent',
    tooltip:{trigger:'item',formatter:p=>{const o=d.find(x=>x.cn===p.name);
      if(!o)return p.name+'<br>'+L('no data','无数据');
      return '<b>'+L((P.en[o.cn]||o.cn),o.cn)+'</b><br>'+
        L('Quota','限额')+' '+fmt(o.quota)+'<br>'+
        L('Issued','发行')+' '+fmt(o.issue)+'<br>'+
        L('Execution','执行率')+' '+pct(o.exec)+'<br>'+
        L('Debt/GDP','债务率')+' '+pct(o.dgdp)+
        (o.parts.length?'<br><span style="opacity:.7">'+L('incl. ','含 ')+o.parts.join('、')+'</span>':'');}},
    visualMap:M.div
      ? {type:'piecewise',left:8,bottom:14,itemGap:4,
         pieces:BINS.map(b=>({min:b.min,max:b.max,label:b.label,color:b.color})),
         textStyle:{color:AX,fontSize:11},
         outOfRange:{color:dark?'#23252b':'#f0f0f2'}}
      : {min:lo,max:hi,left:8,bottom:18,calculable:true,
         inRange:{color:SEQ},textStyle:{color:AX,fontSize:11},
         text:[M.unit==='%'?'%':L('high','高'),''],
         formatter:v=>M.unit==='%'?v.toFixed(0)+'%':fmt(v)},
    series:[{type:'map',map:'china',roam:false,
      data:d.map(o=>({name:o.cn,value:o[metric]})),
      label:{show:false},
      itemStyle:{borderColor:dark?'#2c2e33':'#fff',borderWidth:.6,areaColor:dark?'#23252b':'#f0f0f2'},
      emphasis:{label:{show:false},itemStyle:{borderColor:ACC,borderWidth:1.4}},
      select:{disabled:true}}]};
  charts.c_map.setOption(opt,true);
  document.getElementById('h_map').textContent=L(M.en,M.zh);
  document.getElementById('n_map').textContent=L(
    'Hover a province for its figures. Area misleads on magnitude, so the ranked chart beside it carries the levels.',
    '悬停查看各省数据。地图面积不代表规模，右侧排序图显示具体水平。');
}

function drawBar(){
  const d=rowsOf(year).slice().filter(r=>r.quota||r.issue)
    .sort((a,b)=>(a.quota||0)-(b.quota||0));
  charts.c_bar.setOption({grid:{left:112,right:58,top:28,bottom:30},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('Quota','限额'),L('New-bond issuance','新增发行')]},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},
      formatter:ps=>{const r=d[ps[0].dataIndex];
        return '<b>'+name(r)+'</b><br>'+L('Quota','限额')+' '+fmt(r.quota)+'<br>'+
          L('Issued','发行')+' '+fmt(r.issue)+'<br>'+L('Execution','执行率')+' '+pct(r.exec)+
          '<br>'+L('Refinancing','再融资')+' '+fmt(r.refi);}},
    xAxis:{type:'value',name:'亿元',axisLabel:{color:AX,formatter:v=>v>=10000?(v/10000)+'万亿':v},
      splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    yAxis:{type:'category',data:d.map(name),axisLabel:{color:AX,fontSize:10.5},axisLine:{lineStyle:{color:GRID}}},
    series:[
      {name:L('Quota','限额'),type:'bar',itemStyle:{color:dark?'#3a4556':'#cfd8e6'},
       barGap:'-100%',data:d.map(r=>r.quota)},
      {name:L('New-bond issuance','新增发行'),type:'bar',itemStyle:{color:ACC,opacity:.9},
       barWidth:'52%',data:d.map(r=>r.issue)}]},true);
  document.getElementById('n_bar').textContent=L(
    'Pale bar = quota allocated, solid bar = new bonds actually issued. A short solid bar inside a long pale one is unused quota.',
    '浅色柱为下达限额，实色柱为实际新增发行；实色明显短于浅色即为限额未用完。');
}

function drawScatter(){
  const d=rowsOf(year).filter(r=>r.exec!=null&&r.dgdp!=null);
  const mx=d.length?Math.max(1,...d.map(r=>r.quota||0)):1;
  charts.c_sc.setOption({grid:{left:56,right:24,top:24,bottom:44},textStyle:{color:FG},
    tooltip:{trigger:'item',formatter:p=>{const r=p.data.r;
      return '<b>'+name(r)+'</b><br>'+L('Debt/GDP','债务率')+' '+pct(r.dgdp)+'<br>'+
        L('Execution','执行率')+' '+pct(r.exec)+'<br>'+L('Quota','限额')+' '+fmt(r.quota);}},
    xAxis:{type:'value',name:L('Debt / GDP, %','债务率 %'),axisLabel:{color:AX,formatter:v=>v+'%'},
      splitLine:{lineStyle:{color:GRID}},nameLocation:'middle',nameGap:28,nameTextStyle:{color:AX}},
    yAxis:{type:'value',name:L('Execution, %','执行率 %'),axisLabel:{color:AX,formatter:v=>v+'%'},
      splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    series:[{type:'scatter',
      symbolSize:(v,pm)=>8+34*Math.sqrt(((pm.data&&pm.data.r&&pm.data.r.quota)||0)/mx),
      itemStyle:{color:ACC,opacity:.55,borderColor:ACC,borderWidth:1},
      label:{show:true,position:'top',color:AX,fontSize:9.5,formatter:p=>name(p.data.r)},
      labelLayout:{hideOverlap:true},
      data:d.map(r=>({value:[r.dgdp,r.exec],r})),
      markLine:{silent:true,symbol:'none',lineStyle:{color:AX,type:'dashed',width:1},
        label:{color:AX,fontSize:10,formatter:L('full quota','限额用满')},
        data:[{yAxis:100}]}}]},true);
}

function drawTrend(){
  const ys=P.years.filter(y=>P.complete[y]);
  const q=ys.map(y=>rowsOf(y).reduce((a,r)=>a+(r.quota||0),0));
  const i=ys.map(y=>rowsOf(y).reduce((a,r)=>a+(r.issue||0),0));
  charts.c_tr.setOption({grid:{left:62,right:56,top:30,bottom:34},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('Quota','限额'),L('Issued','发行额'),L('Execution','执行率')]},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
    xAxis:{type:'category',data:ys,axisLabel:{color:AX},axisLine:{lineStyle:{color:GRID}}},
    yAxis:[{type:'value',name:'亿元',axisLabel:{color:AX,formatter:v=>v>=10000?(v/10000)+'万亿':v},
      splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
      {type:'value',name:'%',min:60,max:110,axisLabel:{color:AX,formatter:v=>v+'%'},
       splitLine:{show:false},nameTextStyle:{color:AX}}],
    series:[
      {name:L('Quota','限额'),type:'bar',itemStyle:{color:dark?'#3a4556':'#cfd8e6'},data:q},
      {name:L('Issued','发行额'),type:'bar',itemStyle:{color:ACC,opacity:.9},data:i},
      {name:L('Execution','执行率'),type:'line',yAxisIndex:1,smooth:true,symbolSize:5,
       lineStyle:{width:2.4,color:'#0a9d6b'},itemStyle:{color:'#0a9d6b'},
       data:ys.map((y,k)=>q[k]?+(i[k]/q[k]*100).toFixed(1):null)}]},true);
}

function kpis(){
  const d=rowsOf(year);
  const s=k=>d.reduce((a,r)=>a+(r[k]||0),0);
  const q=s('quota'),i=s('issue'),rf=s('refi'),bal=s('bal');
  // only ratio the stock to GDP when both sides cover the same issuers
  const withBoth=d.filter(r=>r.bal&&r.gdp);
  const gdpOK=withBoth.length>=d.length-2;
  const balG=withBoth.reduce((a,r)=>a+r.bal,0), gdp=withBoth.reduce((a,r)=>a+r.gdp,0);
  const done=d.filter(r=>r.exec!=null);
  const under=done.filter(r=>r.exec<95).sort((a,b)=>a.exec-b.exec);
  const el=document.getElementById('kpi');
  const card=(k,n,sub)=>`<div class="kpi"><div class="k">${k}</div><div class="n">${n}</div><div class="s">${sub||''}</div></div>`;
  el.innerHTML=
    card(L('New-debt quota','新增债务限额'),fmt(q),year+' · '+d.length+L(' issuers','个主体'))+
    card(L('New bonds issued','新增债券发行'),fmt(i),
         (q&&P.complete[year])?L('execution ','执行率 ')+pct(i/q*100)
           :L('execution n/a, year incomplete','执行率不适用，数据未报齐'))+
    card(L('Refinancing issued','再融资发行'),fmt(rf),L('not counted in execution','不计入执行率'))+
    card(L('Debt outstanding','债务余额'),fmt(bal),
         (gdpOK&&gdp)?L('= ','= ')+pct(balG/gdp*100)+L(' of GDP','（占GDP）'):'')+
    card(L('Below 95% execution','执行率低于95%'),under.length,
         under.slice(0,3).map(r=>name(r)+' '+pct(r.exec)).join(' · '));
}

let sortKey='quota', sortDir=-1;
const COLS=[['cn','Issuer','发行主体'],['quota','Quota','新增限额'],['issue','Issued','新增发行'],
  ['exec','Exec %','执行率'],['ns','of which special','其中专项'],['refi','Refinancing','再融资'],
  ['rep','Principal repaid','还本'],['int','Interest','付息'],['bal','Debt balance','债务余额'],
  ['dgdp','Debt/GDP','债务率'],['rev','Budget revenue','一般公共预算收入']];
function table(){
  const d=rowsOf(year).slice();
  const prov=d.filter(r=>!r.parent), sub=d.filter(r=>r.parent);
  const val=r=>r[sortKey];
  prov.sort((a,b)=>{const x=val(a),y=val(b);
    if(sortKey==='cn')return sortDir*name(a).localeCompare(name(b));
    return sortDir*((x==null?-Infinity:x)-(y==null?-Infinity:y));});
  const cell=(r,k)=>k==='cn'?name(r)
    :k==='exec'||k==='dgdp'?pct(r[k]):fmt(r[k]);
  let h='<thead><tr>'+COLS.map(c=>`<th data-k="${c[0]}">${L(c[1],c[2])}${sortKey===c[0]?(sortDir<0?' ▾':' ▴'):''}</th>`).join('')+'</tr></thead><tbody>';
  prov.forEach(r=>{
    h+='<tr>'+COLS.map(c=>`<td>${cell(r,c[0])}</td>`).join('')+'</tr>';
    sub.filter(s=>s.parent===r.cn).forEach(s=>{
      h+='<tr class="sub">'+COLS.map(c=>`<td>${cell(s,c[0])}</td>`).join('')+'</tr>';});
  });
  sub.filter(s=>!prov.some(r=>r.cn===s.parent)).forEach(s=>{
    h+='<tr class="sub">'+COLS.map(c=>`<td>${cell(s,c[0])}</td>`).join('')+'</tr>';});
  h+='</tbody>';
  const t=document.getElementById('tbl'); t.innerHTML=h;
  t.querySelectorAll('th').forEach(th=>th.onclick=()=>{
    const k=th.dataset.k;
    if(k===sortKey)sortDir=-sortDir; else {sortKey=k;sortDir=k==='cn'?1:-1;}
    table();});
}

function partialNote(){
  const el=document.getElementById('partial');
  const ok=P.complete[year];
  el.hidden=!!ok;
  if(!ok){
    const d=rowsOf(year);
    const noQ=d.filter(r=>!r.quota&&r.issue).map(name);
    el.textContent=L(
      year+' is still filling in: '+d.length+' of 37 issuers have reported'+
      (noQ.length?', and '+noQ.length+' show issuance with no quota yet ('+noQ.slice(0,6).join(', ')+')':'')+
      '. Execution rates for this year are not yet meaningful. The platform publishes what each region reports.',
      year+'年数据尚未报齐：37个发行主体中已报'+d.length+'个'+
      (noQ.length?'，其中'+noQ.length+'个已有发行但尚未报限额（'+noQ.slice(0,6).join('、')+'）':'')+
      '。该年执行率暂不具参考意义。平台数据为各地上报。');
  }
  document.getElementById('cav_comp').textContent=L(
    'The platform carries what each region reports, so recent years fill in gradually. For '+
    P.years.filter(y=>P.complete[y]).join(', ')+' the regions sum exactly to the national totals; later years are flagged above.',
    '平台数据为各地上报，近年逐步补齐。'+P.years.filter(y=>P.complete[y]).join('、')+
    '各年分地区合计与全国数一致；其后年份见上方提示。');
}

function applyL(){document.querySelectorAll('[data-l]').forEach(e=>{
  const[a,b]=e.getAttribute('data-l').split('|');e.textContent=lang==='en'?a:b;});}
function seg(id,fn){const w=document.getElementById(id);
  w.querySelectorAll('button').forEach(b=>b.onclick=()=>{
    w.querySelectorAll('button').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');fn(b.dataset.v);});}
function drawAll(){
  // one bad chart should not leave the table and the rest of the page blank
  [partialNote,kpis,drawMap,drawBar,drawScatter,drawTrend,table].forEach(fn=>{
    try{fn();}catch(e){console.error(fn.name,e);}
  });
}

const ysel=document.getElementById('year');
P.years.slice().reverse().forEach(y=>{const o=document.createElement('option');
  o.value=y;o.textContent=y+(P.complete[y]?'':' *');ysel.appendChild(o);});
ysel.value=year;
ysel.onchange=e=>{year=+e.target.value;drawAll();};
seg('metric',v=>{metric=v;drawMap();});
seg('lang',v=>{lang=v;document.body.classList.toggle('lang-en',v==='en');applyL();drawAll();});
applyL();drawAll();
addEventListener('resize',()=>Object.values(charts).forEach(c=>c.resize()));
</script>
</body>
</html>
'''

HTML = HTML.replace('__FOOTER__', footer(
    ['celma', 'npc_budget', 'geoatlas', 'echarts'], page='prov-debt.html', map_page=True))
HTML = HTML.replace('__PAYLOAD__', P)
open(BASE + 'prov-debt.html', 'w', encoding='utf-8').write(HTML)
print(f'wrote prov-debt.html {len(HTML)/1024:.1f} KB')
print(f'  years {YEARS[0]}..{YEARS[-1]}, {len(out)} region-years, '
      f'complete: {[y for y in YEARS if comp[y]["complete"]]}')
