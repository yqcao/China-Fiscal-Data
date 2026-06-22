import json, os
# repo root = parent of this scripts/ directory
base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
DATA = json.dumps(json.load(open(base+'data/mof-reports/fiscal_series.json')), ensure_ascii=False, separators=(',',':'))
LGB  = json.dumps(json.load(open(base+'data/mof-research-reports/lgb_series.json')), ensure_ascii=False, separators=(',',':'))
NSB  = json.dumps(json.load(open(base+'data/mof-research-reports/new_special_ytd.json')), separators=(',',':'))
REP  = json.dumps(json.load(open(base+'data/mof-debt-balance/repayment_series.json')), separators=(',',':'))
TGT  = json.dumps(json.load(open(base+'data/budget-targets.json'))['targets'], separators=(',',':'))

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
.exec{margin:-.1rem 0 1.4rem}
.exec .ehead{font-size:.84rem;font-weight:600;margin:.1rem 0 .55rem}
.exec .ehead .emut{color:var(--mut);font-weight:400;font-size:.76rem}
.erow{display:flex;align-items:center;gap:.7rem;margin:.34rem 0;font-size:.8rem}
.elab{width:160px}.elab b{font-weight:600}
.ebar{flex:1;height:13px;background:var(--bd);border-radius:7px;position:relative}
.efill{height:100%;border-radius:7px;opacity:.85}
.epace{position:absolute;top:-3px;height:19px;width:2px;background:var(--fg);opacity:.6}
.eval{width:215px;text-align:right;font-variant-numeric:tabular-nums;color:var(--mut)}
@media(max-width:760px){.elab{width:104px}.eval{width:158px;font-size:.74rem}}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1rem .4rem;margin-bottom:1.1rem}
.card h3{font-size:.98rem;margin:.1rem 0 .15rem;font-weight:600}
.card h3 .zh{font-size:.82rem}
.card .note{font-size:.76rem;color:var(--mut);margin:0 0 .3rem}
.subhead{display:flex;align-items:center;gap:.5rem;margin:.4rem 0 .5rem;font-weight:600}
.chart{width:100%;height:330px}.chart.sm{height:300px}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem}
@media(max-width:760px){.row2{grid-template-columns:1fr}}
select{background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:8px;padding:.35rem .5rem;font-size:.82rem}
footer{margin-top:1.6rem;font-size:.78rem;color:var(--mut)}footer a{color:var(--mut)}
</style>
</head>
<body class="lang-en">
<div class="wrap">
  <h1>China Fiscal Monitor <span class="zh">中国月度财政运行监测</span></h1>
  <p class="sub">Monthly fiscal operations, 2021–<span id="lastyr"></span> · Sources:
    <a href="https://www.mof.gov.cn/zhengwuxinxi/redianzhuanti/quanguocaizhengshouzhiqingkuang/">MOF 全国财政收支情况</a> ·
    <a href="https://kjhx.mof.gov.cn/yjbg/">China Government Debt Center 地方政府债券市场报告</a></p>

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
    <div class="exec" id="exec_gen"></div>
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
    <div class="exec" id="exec_fund"></div>
    <div class="card"><h3>Fund Revenue, Expenditure & Land-Sale Revenue <span class="zh">基金收入·支出与土地出让收入</span></h3>
      <p class="note" id="note_fund"></p><div id="c_fund" class="chart"></div></div>
    <div class="card"><h3>Cumulative YoY Growth <span class="zh">累计同比增速</span></h3>
      <p class="note" data-l="Official year-on-year growth, % (cumulative basis)|官方累计同比增速 %"></p><div id="c_fund_yoy" class="chart sm"></div></div>
  </section>

  <!-- SECTION 3 -->
  <section>
    <div class="shead"><h2>3 · Local Government Bond Issuance <span class="zh">地方政府债券发行</span></h2>
      <p>Monthly LGB issuance from the China Government Debt Center reports. Figures in RMB billion; natively monthly.</p></div>
    <div class="kpis" id="kpi_lgb"></div>
    <div class="card"><h3>Monthly Issuance by Type & Average Rate <span class="zh">当月发行（按类型）与平均利率</span></h3>
      <p class="note" data-l="Bars: general vs special bonds (RMB bn, left) · Line: average issue rate (%, right)|柱：一般债与专项债（十亿元，左）· 线：平均发行利率（%，右）"></p><div id="c_lgb" class="chart"></div></div>
    <div class="card"><h3 data-l="Refinancing Issuance vs Principal Repayment|再融资发行 vs 到期偿还本金"></h3>
      <p class="note" data-l="Monthly principal repaid, split by funding source (bars), vs refinancing-bond issuance (line), RMB bn|当月到期偿还本金（按资金来源堆叠）与再融资债券发行（线），十亿元"></p><div id="c_lgb_refi" class="chart"></div></div>
    <div class="card"><h3 data-l="New Special-Bond Issuance, YTD by Year|新增专项债发行（年初至今，分年度）"></h3>
      <p class="note" data-l="Cumulative new special-bond issuance through each month; one line per year (RMB bn)|累计新增专项债发行，每年一条线（十亿元）"></p><div id="c_lgb_ytd" class="chart"></div></div>
    <div class="subhead"><span data-l="Use of New-Bond Proceeds (investment targets)|新增债券资金投向"></span> <select id="lgbsel"></select></div>
    <div class="card"><p class="note" data-l="New special-bond proceeds by investment field for the selected month, RMB bn|所选月份新增专项债券按投向分布，十亿元"></p><div id="c_lgb_use" class="chart"></div></div>
    <div class="row2">
      <div class="card"><h3 data-l="Average Maturity & Secondary-Market Turnover|平均期限与二级市场现券交易"></h3>
        <p class="note" data-l="Line: average maturity (years, left) · Bars: secondary-market spot turnover (RMB bn, right)|线：平均期限（年，左）· 柱：二级市场现券交易（十亿元，右）"></p><div id="c_lgb2" class="chart sm"></div></div>
      <div class="card"><h3 data-l="Issuance YoY Growth|发行额同比增速"></h3>
        <p class="note" data-l="Monthly total issuance vs same month prior year, %|当月发行额同比 %"></p><div id="c_lgb_yoy" class="chart sm"></div></div>
    </div>
  </section>

  <footer>
    Basis note: MOF publishes cumulative (year-to-date) figures; "Monthly" values are derived by differencing consecutive reports within a year, and each year's first report covers Jan–Feb combined (no standalone January). LGB figures are reported monthly in RMB billion.<br>
    Data © Ministry of Finance, PRC · built for <a href="https://github.com/yqcao/China-Fiscal-Data">github.com/yqcao/China-Fiscal-Data</a>
  </footer>
</div>

<script>
const DATA = __DATA__;
const LGB  = __LGB__;
const NSB  = __NSB__;
const REP  = __REP__;
const TGT  = __TGT__;
// Unify units: MOF fiscal figures are in 亿元 — convert to RMB billion (十亿元, ÷10).
const MFIELDS=['pub_rev','tax','nontax','pub_rev_central','pub_rev_local','pub_exp','pub_exp_central','pub_exp_local','fund_rev','land_rev','fund_exp'];
DATA.forEach(r=>{MFIELDS.forEach(k=>{if(r[k]&&r[k].v!=null)r[k].v=+(r[k].v/10).toFixed(2);});
  (r.tax_items||[]).forEach(i=>i.v=+(i.v/10).toFixed(2));
  (r.exp_items||[]).forEach(i=>i.v=+(i.v/10).toFixed(2));});

const dark=matchMedia('(prefers-color-scheme: dark)').matches;
const AX=dark?'#9aa':'#666',GRID=dark?'#2c2e33':'#eee',FG=dark?'#e6e6e6':'#1a1a1a';
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
function lgbYoY(){const by={};LGB.forEach(r=>by[r.year+'-'+r.month]=r.issue);
  return LGB.map(r=>{const py=by[(r.year-1)+'-'+r.month];return py?+((r.issue/py-1)*100).toFixed(1):null;});}
function drawLGB(){
  charts.c_lgb.setOption({grid:{left:56,right:56,top:30,bottom:48},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('General','一般债'),L('Special','专项债'),L('Avg Rate','平均利率')]},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},xAxis:{type:'category',data:lgbP,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    yAxis:[{type:'value',name:'RMB bn',axisLabel:{color:AX},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
           {type:'value',name:'%',axisLabel:{color:AX,formatter:'{value}%'},splitLine:{show:false},nameTextStyle:{color:AX}}],
    series:[{name:L('General','一般债'),type:'bar',stack:'b',itemStyle:{color:C.gen},data:LGB.map(r=>r.general)},
      {name:L('Special','专项债'),type:'bar',stack:'b',itemStyle:{color:C.spec},data:LGB.map(r=>r.special)},
      {name:L('Avg Rate','平均利率'),type:'line',yAxisIndex:1,smooth:true,showSymbol:false,lineStyle:{width:2.4,color:C.rate},itemStyle:{color:C.rate},data:LGB.map(r=>r.rate)}]},true);
  charts.c_lgb2.setOption({grid:{left:54,right:56,top:30,bottom:48},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('Avg Maturity','平均期限'),L('Secondary Turnover','二级市场交易')]},tooltip:{trigger:'axis'},
    xAxis:{type:'category',data:lgbP,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    yAxis:[{type:'value',name:L('years','年'),axisLabel:{color:AX},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
           {type:'value',name:'RMB bn',axisLabel:{color:AX},splitLine:{show:false},nameTextStyle:{color:AX}}],
    series:[{name:L('Secondary Turnover','二级市场交易'),type:'bar',yAxisIndex:1,itemStyle:{color:'#8ab4ff',opacity:.75},data:LGB.map(r=>r.secondary)},
      {name:L('Avg Maturity','平均期限'),type:'line',smooth:true,showSymbol:false,lineStyle:{width:2.4,color:C.mat},itemStyle:{color:C.mat},data:LGB.map(r=>r.maturity)}]},true);
  const yo=lgbYoY();
  charts.c_lgb_yoy.setOption({grid:{left:48,right:18,top:18,bottom:48},textStyle:{color:FG},tooltip:{trigger:'axis',valueFormatter:v=>v==null?'–':v+'%'},
    xAxis:{type:'category',data:lgbP,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',name:'%',axisLabel:{color:AX,formatter:'{value}%'},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    series:[{type:'line',smooth:true,showSymbol:false,lineStyle:{width:2,color:C.spec},itemStyle:{color:C.spec},data:yo,areaStyle:{opacity:.06,color:C.spec}}]},true);
  drawRefiRepay();
}
function drawRefiRepay(){
  // monthly principal repayment derived from YTD (亿 -> RMB bn); only diff consecutive months
  const ytdRefi={},ytdFisc={};
  REP.forEach(r=>{ytdRefi[r.period]=r.repay_refi_ytd; ytdFisc[r.period]=r.repay_fisc_ytd;});
  const pk=r=>r.year+'-'+String(r.month-1).padStart(2,'0');
  const mdiff=(map,r)=>{const c=map[r.period]; if(c==null)return null; if(r.month===1)return c; const p=map[pk(r)]; return p==null?null:+(c-p).toFixed(0);};
  const P=REP.map(r=>r.period), toB=v=>v==null?null:+(v/10).toFixed(1);
  const repRefi=REP.map(r=>toB(mdiff(ytdRefi,r))), repFisc=REP.map(r=>toB(mdiff(ytdFisc,r)));
  const refiIss=P.map(p=>{const r=LGB.find(x=>x.period===p);return r?r.refi:null;});
  charts.c_lgb_refi.setOption({grid:{left:56,right:18,top:30,bottom:48},textStyle:{color:FG},
    legend:{top:0,textStyle:{color:AX},data:[L('Repaid via refinancing','再融资偿还'),L('Repaid via fiscal funds','财政资金偿还'),L('Refinancing issuance','再融资发行')]},
    tooltip:{trigger:'axis',valueFormatter:v=>v==null?'–':'RMB '+v+'bn'},
    xAxis:{type:'category',data:P,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',name:'RMB bn',axisLabel:{color:AX,formatter:v=>v>=1000?(v/1000)+'tn':v},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    series:[
      {name:L('Repaid via refinancing','再融资偿还'),type:'bar',stack:'rp',itemStyle:{color:'#7c4dff'},data:repRefi},
      {name:L('Repaid via fiscal funds','财政资金偿还'),type:'bar',stack:'rp',itemStyle:{color:'#c9a96b'},data:repFisc},
      {name:L('Refinancing issuance','再融资发行'),type:'line',smooth:true,showSymbol:false,lineStyle:{width:2.4,color:'#0a9d6b'},itemStyle:{color:'#0a9d6b'},data:refiIss}]},true);
}
const USESHORT=[[/municipal.*industrial park/i,'Municipal & industrial-park infra'],[/transportation/i,'Transportation infra'],
 [/land reserve/i,'Land reserve'],[/social undertaking/i,'Social undertaking'],
 [/housing.*urban renewal|subsidized housing/i,'Affordable housing & urban renewal'],[/ecolog/i,'Ecology & environment'],
 [/forward-looking|strategic emerging/i,'Strategic emerging industries'],[/warehouse logistic/i,'Warehouse logistics'],
 [/new infrastructure/i,'New infrastructure'],[/^energy$/i,'Energy'],[/purchase existing|existing commercial housing/i,'Buy existing housing'],
 [/agricultur|forestry|water/i,'Agriculture, forestry & water'],[/health/i,'Healthcare'],[/educat/i,'Education'],
 [/^others?$/i,'Others']];
function useShort(f){for(const[re,s]of USESHORT)if(re.test(f))return s; return f.charAt(0).toUpperCase()+f.slice(1);}
function fillLgbSel(){const s=document.getElementById('lgbsel');const cur=s.value;s.innerHTML='';
  LGB.filter(r=>r.use&&r.use.length).slice().reverse().forEach(r=>{const o=document.createElement('option');o.value=r.period;o.textContent=r.period;s.appendChild(o);});
  if(cur)s.value=cur;}
function drawUse(period){
  const r=LGB.find(x=>x.period===period&&x.use&&x.use.length)||[...LGB].reverse().find(x=>x.use&&x.use.length);
  const u=r.use.slice().sort((a,b)=>a.v-b.v);
  charts.c_lgb_use.setOption({grid:{left:210,right:60,top:8,bottom:24},textStyle:{color:FG},
    tooltip:{trigger:'item',formatter:p=>useShort(u[p.dataIndex].field)+'：RMB '+p.value+'bn'},
    xAxis:{type:'value',name:'RMB bn',axisLabel:{color:AX},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}},
    yAxis:{type:'category',data:u.map(i=>useShort(i.field)),axisLabel:{color:AX,fontSize:11}},
    series:[{type:'bar',data:u.map(i=>i.v),itemStyle:{color:C.spec},
      label:{show:true,position:'right',color:AX,fontSize:10,formatter:p=>'RMB '+p.value+'bn'}}]},true);
}

// Budget execution vs annual target (current year, cumulative YTD ÷ annual budget).
// Targets are in 亿元; DATA values were converted to RMB bn (÷10), so divide the target by 10 to match.
function execRows(elId,fields){
  const el=document.getElementById(elId); if(!el)return;
  const Lt=DATA[DATA.length-1], t=TGT[Lt.year];
  if(!t){el.innerHTML='';return;}
  const elapsed=+(Lt.month/12*100).toFixed(1);
  el.innerHTML=`<div class="ehead">${L('Execution vs Annual Budget','预算执行进度')} `
    +`<span class="emut">${L(Lt.year+' budget · marker ▏= '+elapsed+'% of year elapsed',Lt.year+'年预算 · 竖线▏＝时间进度 '+elapsed+'%')}</span></div>`
    +fields.map(([k,en,zh,col])=>{
      const a=Lt[k]?Lt[k].v:null, tg=t[k]!=null?t[k]/10:null;
      if(a==null||tg==null) return '';
      const pct=+(a/tg*100).toFixed(1), diff=+(pct-elapsed).toFixed(1), sign=diff>=0?'+':'';
      return `<div class="erow"><div class="elab"><b>${en}</b> <span class="zh">${zh}</span></div>`
        +`<div class="ebar"><div class="efill" style="width:${Math.min(pct,100)}%;background:${col}"></div>`
        +`<div class="epace" style="left:${Math.min(elapsed,100)}%"></div></div>`
        +`<div class="eval">${pct}% <small>${L('of target','预算')}</small> · `
        +`<span class="${diff>=0?'up':'down'}">${sign}${diff}pp</span></div></div>`;
    }).join('');
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
  execRows('exec_gen',[['pub_rev','Revenue','收入','#c00'],['pub_exp','Expenditure','支出','#1463ff']]);
  execRows('exec_fund',[['fund_rev','Fund Revenue','基金收入','#e07b00'],['fund_exp','Fund Expenditure','基金支出','#6b7280']]);
  const G=LGB[LGB.length-1],yo=lgbYoY()[LGB.length-1];
  kpi('kpi_lgb',[
    [L('Monthly Issuance','Monthly Issuance'),'当月发行',fmtB(G.issue),G.period,yo],
    [L('Avg Issue Rate','Avg Issue Rate'),'平均利率',G.rate+'%','',null],
    [L('Avg Maturity','Avg Maturity'),'平均期限',G.maturity+' <small>yr</small>','',null],
    [L('YTD Issuance','YTD Issuance'),'年初至今发行',G.cum_issue?fmtB(G.cum_issue):'–','',null]]);
}

function applyDataL(){document.querySelectorAll('[data-l]').forEach(e=>{const[en,zh]=e.getAttribute('data-l').split('|');e.textContent=lang==='en'?en:zh;});}

['c_gen_rev','c_gen_exp','c_tax_pie','c_tax_grow','c_exp_pie','c_exp_grow','c_fund','c_fund_yoy','c_lgb','c_lgb_refi','c_lgb_ytd','c_lgb2','c_lgb_yoy','c_lgb_use'].forEach(mk);
document.getElementById('taxsel').onchange=e=>drawComposition('c_tax_pie','c_tax_grow','tax_items',e.target.value);
document.getElementById('expsel').onchange=e=>drawComposition('c_exp_pie','c_exp_grow','exp_items',e.target.value);
document.getElementById('lgbsel').onchange=e=>drawUse(e.target.value);
function seg(id,cb){document.querySelectorAll('#'+id+' button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#'+id+' button').forEach(x=>x.classList.remove('on'));b.classList.add('on');cb(b.dataset.v);});}
seg('basis',v=>{basis=v;drawGen();drawFund();});
seg('split',v=>{split=v;drawGen();});
seg('lang',v=>{lang=v;document.body.classList.toggle('lang-en',v==='en');document.body.classList.toggle('lang-zh',v==='zh');applyDataL();fillSel('taxsel');fillSel('expsel');drawAll();});

function drawAll(){applyDataL();renderKPIs();drawGen();drawFund();
  yoyChart('c_fund_yoy',[['fund_rev','Fund Revenue','基金收入',C.fund],['fund_exp','Fund Expenditure','基金支出',C.exp],['land_rev','Land-Sale','土地出让',C.land]]);
  drawComposition('c_tax_pie','c_tax_grow','tax_items',document.getElementById('taxsel').value);
  drawComposition('c_exp_pie','c_exp_grow','exp_items',document.getElementById('expsel').value);
  drawLGB();drawNSB();drawUse(document.getElementById('lgbsel').value);}
addEventListener('resize',()=>Object.values(charts).forEach(c=>c.resize()));
fillSel('taxsel');fillSel('expsel');fillLgbSel();applyDataL();drawAll();
</script>
</body>
</html>
'''
HTML=HTML.replace('__DATA__',DATA).replace('__LGB__',LGB).replace('__NSB__',NSB).replace('__REP__',REP).replace('__TGT__',TGT)
open(base+'fiscal-monitor.html','w',encoding='utf-8').write(HTML)
print('wrote fiscal-monitor.html',round(len(HTML)/1024,1),'KB')
