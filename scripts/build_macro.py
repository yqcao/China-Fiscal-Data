#!/usr/bin/env python3
"""Generate one interactive page per macro indicator from data/macro/<id>_series.json.

Config-driven: PAGES lists each indicator and which series to plot. Indicators
whose JSON is missing or empty are skipped (with a note), so this is safe to run
before every fetcher has been validated. Styling matches the fiscal monitor.
"""
import json, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
MDIR = BASE+'data/macro/'

# type: 'line'|'bar'; axis: 0 (left) | 1 (right). ref: horizontal reference line value.
PAGES = [
 {'id':'cpi','title':'China CPI Monitor','zh':'中国CPI月度监测','sub':('Consumer Price Index, monthly','居民消费价格指数，月度'),
  'src':('NBS 国家统计局','https://www.stats.gov.cn/sj/zxfb/'),'ref':0,'y0':'YoY %','y1':'MoM %',
  'series':[{'k':'mom','en':'MoM %','zh':'环比 %','type':'bar','axis':1,'c':'#8ab4ff'},
            {'k':'yoy','en':'YoY %','zh':'同比 %','type':'line','axis':0,'c':'#c00','area':True}]},
 {'id':'retail','title':'China Retail Sales','zh':'社会消费品零售总额','sub':('Retail sales growth','社会消费品零售总额增速'),
  'src':('NBS 国家统计局','https://www.stats.gov.cn/sj/zxfb/'),'ref':0,'y0':'%','y1':'%',
  'series':[{'k':'ytd','en':'YTD YoY %','zh':'累计同比 %','type':'line','axis':0,'c':'#c00','area':True},
            {'k':'yoy','en':'Monthly YoY %','zh':'当月同比 %','type':'bar','axis':0,'c':'#8ab4ff'}]},
 {'id':'fai','title':'Fixed-Asset Investment','zh':'固定资产投资','sub':('FAI, YTD YoY','固定资产投资累计同比'),
  'src':('NBS 国家统计局','https://www.stats.gov.cn/sj/zxfb/'),'ref':0,'y0':'%','y1':'%',
  'series':[{'k':'ytd_yoy','en':'FAI YTD %','zh':'固投累计 %','type':'line','axis':0,'c':'#1463ff','area':True},
            {'k':'realestate_yoy','en':'Real estate %','zh':'房地产 %','type':'line','axis':0,'c':'#e07b00'}]},
 {'id':'pmi','title':'China PMI','zh':'采购经理指数','sub':('Purchasing Managers Index','采购经理指数'),
  'src':('NBS 国家统计局','https://www.stats.gov.cn/sj/zxfb/'),'ref':50,'y0':'index','y1':'index',
  'series':[{'k':'mfg','en':'Manufacturing','zh':'制造业','type':'line','axis':0,'c':'#c00'},
            {'k':'nonmfg','en':'Non-manufacturing','zh':'非制造业','type':'line','axis':0,'c':'#1463ff'},
            {'k':'composite','en':'Composite','zh':'综合','type':'line','axis':0,'c':'#0a9d6b'}]},
 {'id':'gdp','title':'China GDP','zh':'国内生产总值','sub':('Real GDP growth, quarterly (cumulative YoY)','GDP累计实际同比，季度'),
  'src':('NBS 国家统计局','https://www.stats.gov.cn/sj/zxfb/'),'ref':0,'y0':'%','y1':'%',
  'series':[{'k':'gdp_yoy','en':'Real GDP YoY %','zh':'实际同比 %','type':'bar','axis':0,'c':'#c00'}]},
 {'id':'trade','title':'China Trade','zh':'货物进出口','sub':('Exports & imports growth','进出口增速'),
  'src':('NBS / Customs','https://www.stats.gov.cn/sj/zxfb/'),'ref':0,'y0':'%','y1':'%',
  'series':[{'k':'exports_yoy','en':'Exports %','zh':'出口 %','type':'line','axis':0,'c':'#c00'},
            {'k':'imports_yoy','en':'Imports %','zh':'进口 %','type':'line','axis':0,'c':'#1463ff'},
            {'k':'total_yoy','en':'Total %','zh':'合计 %','type':'line','axis':0,'c':'#0a9d6b'}]},
 {'id':'pboc','title':'China Money & Financing','zh':'货币与社会融资','sub':('PBOC monetary & financing indicators','人民银行货币金融指标'),
  'src':('PBOC 中国人民银行','http://www.pbc.gov.cn/'),'ref':0,'y0':'%','y1':'RMB bn',
  'series':[{'k':'m2_yoy','en':'M2 YoY %','zh':'M2同比 %','type':'line','axis':0,'c':'#c00'},
            {'k':'tsf_stock_yoy','en':'TSF stock YoY %','zh':'社融存量同比 %','type':'line','axis':0,'c':'#1463ff'},
            {'k':'new_loans','en':'New loans (¥bn)','zh':'新增贷款(十亿)','type':'bar','axis':1,'c':'#8ab4ff'}]},
]

TMPL = r'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{color-scheme:light dark;--bg:#f7f7f8;--fg:#1a1a1a;--card:#fff;--bd:#e3e3e6;--mut:#666;--accent:#c00;--up:#16a34a;--down:#dc2626;}
@media(prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#e6e6e6;--card:#1e1f23;--bd:#2c2e33;--mut:#9aa;--accent:#ff6b6b;}}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",Helvetica,Arial,sans-serif;background:var(--bg);color:var(--fg);line-height:1.5}
body.lang-en .zh{display:none}.wrap{max-width:1000px;margin:0 auto;padding:2rem 1.1rem 4rem}
h1{font-size:1.6rem;margin:0 0 .15rem}h1 .zh{font-size:1rem;color:var(--mut);font-weight:400;display:block;margin-top:.1rem}
.sub{color:var(--mut);margin:.2rem 0 1.3rem;font-size:.9rem}.sub a{color:var(--accent)}
.controls{margin-bottom:1.2rem}.seg{display:inline-flex;border:1px solid var(--bd);border-radius:9px;overflow:hidden;background:var(--card)}
.seg button{border:0;background:transparent;color:var(--fg);padding:.45rem .8rem;font-size:.85rem;cursor:pointer}.seg button.on{background:var(--accent);color:#fff}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.8rem;margin-bottom:1.3rem}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:.85rem .95rem}
.kpi .t{font-size:.76rem;color:var(--mut)}.kpi .v{font-size:1.4rem;font-weight:650;margin-top:.1rem}
.up{color:var(--up)}.down{color:var(--down)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:1rem 1rem .5rem}
.card h3{font-size:1rem;margin:.1rem 0 .1rem}.card .note{font-size:.78rem;color:var(--mut);margin:0 0 .4rem}
.chart{width:100%;height:420px}footer{margin-top:1.5rem;font-size:.78rem;color:var(--mut)}footer a{color:var(--mut)}
</style></head><body class="lang-en"><div class="wrap">
<h1>__H1__ <span class="zh">__ZH__</span></h1>
<p class="sub"><span data-l="__SUB__"></span> · <a href="index.html">&larr; all data</a> · <a href="fiscal-monitor.html" data-l="Fiscal Monitor|财政运行监测"></a> · <span data-l="Source|来源"></span>: <a href="__SRCURL__">__SRC__</a></p>
<div class="controls"><span class="seg" id="lang"><button data-v="en" class="on">EN</button><button data-v="zh">中文</button></span></div>
<div class="kpis" id="kpi"></div>
<div class="card"><div id="c" class="chart"></div></div>
<footer><span data-l="Data source as noted · built for|数据来源见上 · 构建于"></span> <a href="https://github.com/yqcao/China-Fiscal-Data">github.com/yqcao/China-Fiscal-Data</a></footer>
</div><script>
const D=__DATA__,SER=__SER__,REF=__REF__,Y0=__Y0__,Y1=__Y1__;
const dark=matchMedia('(prefers-color-scheme: dark)').matches;
const AX=dark?'#9aa':'#666',GRID=dark?'#2c2e33':'#eee',FG=dark?'#e6e6e6':'#1a1a1a';
let lang='en';const L=(e,z)=>lang==='en'?e:z;const P=D.map(r=>r.period);
const chart=echarts.init(document.getElementById('c'));
function applyL(){document.querySelectorAll('[data-l]').forEach(e=>{const[a,b]=e.getAttribute('data-l').split('|');e.textContent=lang==='en'?a:b;});}
function kpis(){const last=D[D.length-1];document.getElementById('kpi').innerHTML=SER.map(s=>{const v=last[s.k];const col=(typeof v==='number'&&REF!=null)?(v>=REF?'up':'down'):'';return v==null?'':`<div class="kpi"><div class="t">${L(s.en,s.zh)} · ${last.period}</div><div class="v ${col}">${v}</div></div>`;}).join('');}
function draw(){const useR=SER.some(s=>s.axis===1);
 const series=SER.map(s=>{const o={name:L(s.en,s.zh),type:s.type,data:D.map(r=>r[s.k]==null?null:r[s.k])};
   if(s.axis===1)o.yAxisIndex=1; if(s.type==='line'){o.smooth=true;o.showSymbol=false;o.lineStyle={width:2.4,color:s.c};o.itemStyle={color:s.c};if(s.area)o.areaStyle={opacity:.05,color:s.c};}
   else{o.itemStyle={color:s.c,opacity:.7};} return o;});
 if(REF!=null&&series.length)series[series.length-1].markLine={silent:true,symbol:'none',lineStyle:{color:AX,type:'dashed',opacity:.4},data:[{yAxis:REF}]};
 const yA=[{type:'value',name:Y0,axisLabel:{color:AX},splitLine:{lineStyle:{color:GRID}},nameTextStyle:{color:AX}}];
 if(useR)yA.push({type:'value',name:Y1,axisLabel:{color:AX},splitLine:{show:false},nameTextStyle:{color:AX}});
 chart.setOption({grid:{left:48,right:useR?48:16,top:30,bottom:52},textStyle:{color:FG},
  legend:{top:0,textStyle:{color:AX},data:SER.map(s=>L(s.en,s.zh))},tooltip:{trigger:'axis'},
  xAxis:{type:'category',data:P,axisLabel:{color:AX,rotate:45,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
  yAxis:yA,series:series},true);}
function render(){applyL();kpis();draw();}
document.querySelectorAll('#lang button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#lang button').forEach(x=>x.classList.remove('on'));b.classList.add('on');lang=b.dataset.v;document.body.classList.toggle('lang-en',lang==='en');render();});
addEventListener('resize',()=>chart.resize());render();
</script></body></html>'''

def build(cfg):
    path=MDIR+cfg['id']+'_series.json'
    if not os.path.exists(path): return None,'no data file'
    data=json.load(open(path))
    if not data: return None,'empty'
    # keep only series whose key appears with at least one non-null value
    ser=[s for s in cfg['series'] if any(r.get(s['k']) is not None for r in data)]
    if not ser: return None,'no populated series'
    html=(TMPL
      .replace('__TITLE__',f"{cfg['title']} · {cfg['zh']}")
      .replace('__H1__',cfg['title']).replace('__ZH__',cfg['zh'])
      .replace('__SUB__',f"{cfg['sub'][0]}|{cfg['sub'][1]}")
      .replace('__SRC__',cfg['src'][0]).replace('__SRCURL__',cfg['src'][1])
      .replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')))
      .replace('__SER__',json.dumps(ser,ensure_ascii=False,separators=(',',':')))
      .replace('__REF__','null' if cfg.get('ref') is None else str(cfg['ref']))
      .replace('__Y0__',json.dumps(cfg['y0'])).replace('__Y1__',json.dumps(cfg['y1'])))
    open(BASE+cfg['id']+'.html','w',encoding='utf-8').write(html)
    return len(data),'ok'

if __name__=='__main__':
    for cfg in PAGES:
        n,msg=build(cfg)
        print(f"  {cfg['id']:8} {'-> '+cfg['id']+'.html ('+str(n)+' pts)' if n else 'skipped ('+msg+')'}")
