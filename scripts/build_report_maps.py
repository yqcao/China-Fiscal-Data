#!/usr/bin/env python3
"""Build report-maps.html — four maps over the 31 provincial work reports.

One map per topic. Three count how often a province's own report raises a theme;
the fourth is the headline growth target. Hovering a province lists the actual
sentences behind its number, so a count is never asserted without the text that
produced it.

Counting words is a crude proxy for emphasis and the page says so. What keeps it
honest is that every figure is one hover away from its own evidence: if a count
looks wrong, the sentences are right there to check.

Inputs: data/prov-reports/text/*.txt, targets.json, sources.json,
        data/geo/china-provinces.json
"""
import json, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
TXT  = BASE + 'data/prov-reports/text/'

reg = json.load(open(BASE + 'data/prov-reports/sources.json', encoding='utf-8'))
tgs = {r['code']: r for r in json.load(open(BASE + 'data/prov-reports/targets.json'))}
geo = json.load(open(BASE + 'data/geo/china-provinces.json', encoding='utf-8'))

# Deliberately policy-specific vocabularies. Bare 消费 occurs 772 times across the
# corpus and would measure prose style rather than policy attention.
TOPICS = [
    {'key': 'debt', 'en': 'Hidden debt & LGFVs', 'zh': '隐性债务与融资平台',
     'note_en': 'Mentions of hidden debt, debt resolution, financing platforms and debt risk.',
     'note_zh': '隐性债务、化债、融资平台与债务风险的提及次数。',
     'terms': ['隐性债务', '化债', '债务化解', '融资平台', '城投', '政府债务风险', '置换债']},
    {'key': 'invest', 'en': 'Government investment funds', 'zh': '政府投资基金与股权投资',
     'note_en': 'Mentions of state investment funds, guidance funds, equity investment and patient capital.',
     'note_zh': '政府投资基金、引导基金、母基金、股权投资与耐心资本的提及次数。',
     'terms': ['政府投资基金', '引导基金', '母基金', '产业基金', '创业投资', '创投',
               '股权投资', '耐心资本', '长期资本', '天使投资', '并购基金', '拨改投']},
    {'key': 'consume', 'en': 'Consumption & domestic demand', 'zh': '消费与内需',
     'note_en': 'Mentions of demand-side policy: boosting consumption, trade-in schemes, service and inbound consumption.',
     'note_zh': '需求侧政策提及：提振消费、以旧换新、服务消费与入境消费等。',
     'terms': ['提振消费', '扩大内需', '促消费', '以旧换新', '服务消费', '首发经济',
               '入境消费', '新型消费', '消费场景', '银发经济', '育儿补贴', '消费券']},
]
MAXQ, QLEN = 6, 210

def sentences(flat, terms):
    """Sentence-level hits, deduped, in document order, with the terms matched."""
    out, seen = [], set()
    for m in re.finditer('|'.join(terms), flat):
        s = flat.rfind('。', 0, m.start()) + 1
        e = flat.find('。', m.end())
        e = e + 1 if e > 0 else min(len(flat), m.end() + 90)
        q = flat[s:e].strip()
        if len(q) < 8 or q in seen: continue
        seen.add(q)
        out.append({'q': q[:QLEN] + ('…' if len(q) > QLEN else ''),
                    't': sorted({x.group(0) for x in re.finditer('|'.join(terms), q)})})
    return out

rows = []
for p in reg['provinces']:
    code, f = p['code'], TXT + f'2026_{p["code"]}.txt'
    if not os.path.exists(f): continue
    raw = open(f, encoding='utf-8', errors='replace').read()
    # markdown rule runs survive the PDF conversion and cut through sentences
    flat = re.sub(r'-{2,}', '', re.sub(r'[\s|]+', '', raw))
    t = tgs.get(code)
    rec = {'cn': p['cn'], 'en': p['en'], 'code': code, 'domain': p['domain'],
           'url': p['reports'].get('2026', ''), 'chars': len(flat),
           'low': t['low'] if t else None, 'high': t['high'] if t else None,
           'mid': round((t['low'] + t['high']) / 2, 2) if t else None,
           'phrasing': t['phrasing'] if t else ''}
    for topic in TOPICS:
        hits = sentences(flat, topic['terms'])
        rec[topic['key']] = {'n': sum(len(re.findall('|'.join(topic['terms']), flat)) for _ in [0]),
                             'qs': hits[:MAXQ], 'more': max(0, len(hits) - MAXQ)}
    rows.append(rec)

P = json.dumps({'rows': rows, 'geo': geo,
                'topics': [{k: t[k] for k in ('key', 'en', 'zh', 'note_en', 'note_zh')} for t in TOPICS]},
               ensure_ascii=False, separators=(',', ':'))

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>What the Provinces Talk About · 各省报告主题地图</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
:root{color-scheme:light dark;--bg:#f7f7f8;--fg:#1a1a1a;--card:#fff;--bd:#e3e3e6;--mut:#666;--accent:#c00;}
@media(prefers-color-scheme:dark){:root{--bg:#16171a;--fg:#e6e6e6;--card:#1e1f23;--bd:#2c2e33;--mut:#9aa;--accent:#ff6b6b;}}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",Helvetica,Arial,sans-serif;background:var(--bg);color:var(--fg);line-height:1.5}
body.lang-en .zh{display:none}
.wrap{max-width:1180px;margin:0 auto;padding:2rem 1.1rem 4rem}
h1{font-size:1.7rem;margin:0 0 .15rem}
.zh{color:var(--mut);font-weight:400}
h1 .zh{font-size:1.05rem;display:block;margin-top:.1rem}
.sub{color:var(--mut);margin:.2rem 0 1.2rem;font-size:.9rem}.sub a{color:var(--accent)}
.controls{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin-bottom:1.2rem}
.seg{display:inline-flex;border:1px solid var(--bd);border-radius:9px;overflow:hidden;background:var(--card)}
.seg button{border:0;background:transparent;color:var(--fg);padding:.45rem .8rem;font-size:.85rem;cursor:pointer}
.seg button.on{background:var(--accent);color:#fff}
.lbl{font-size:.78rem;color:var(--mut);margin-right:.1rem}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem}
@media(max-width:940px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:.9rem .95rem .7rem}
.card h3{font-size:1rem;margin:.1rem 0 .1rem;font-weight:660}
.card h3 .zh{font-size:.84rem}
.card .note{font-size:.76rem;color:var(--mut);margin:.15rem 0 .4rem;min-height:2.3em}
.map{width:100%;height:330px}
.panel{border-top:1px solid var(--bd);margin-top:.5rem;padding-top:.5rem;height:206px;overflow-y:auto}
.panel .ph{font-size:.8rem;font-weight:660;margin-bottom:.3rem}
.panel .ph span{font-weight:400;color:var(--mut)}
.panel .hint{font-size:.78rem;color:var(--mut);padding:.6rem 0}
.panel ul{margin:.1rem 0;padding-left:1rem}
.panel li{font-size:.775rem;margin:.34rem 0;line-height:1.5}
.panel mark{background:rgba(204,0,0,.14);color:inherit;border-radius:3px;padding:0 .1em}
@media(prefers-color-scheme:dark){.panel mark{background:rgba(255,107,107,.22)}}
.panel .src{font-size:.72rem;color:var(--mut);margin-top:.45rem}
.panel .src a{color:var(--accent);word-break:break-all}
.caveat{font-size:.79rem;color:var(--mut);background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:.85rem 1rem;margin-top:1.4rem}
.caveat li{margin:.35rem 0}.caveat b{color:var(--fg)}
footer{margin-top:1.5rem;font-size:.78rem;color:var(--mut)}footer a{color:var(--mut)}
</style>
</head>
<body class="lang-en">
<div class="wrap">

<h1>What the Provinces Talk About <span class="zh">各省政府工作报告主题地图</span></h1>
<p class="sub">
  <span data-l="Four themes across all 31 provincial government work reports for 2026. Hover a province to read the sentences behind its number.|2026年31份省级政府工作报告的四个主题。将光标移至某省即可查看其对应原文。"></span> ·
  <a href="index.html" data-l="&larr; all data|&larr; 全部数据"></a> ·
  <a href="growth-targets.html" data-l="Growth Targets|增长目标"></a> ·
  <a href="fiscal-monitor.html" data-l="Fiscal Monitor|财政运行监测"></a>
</p>

<div class="controls">
  <span class="lbl" data-l="language|语言"></span>
  <div class="seg" id="lang"><button data-v="en" class="on">EN</button><button data-v="zh">中文</button></div>
  <span class="lbl" data-l="hover a province · click to pin|移入查看 · 点击固定"></span>
</div>

<div class="grid" id="grid"></div>

<div class="caveat">
  <ul>
    <li><b data-l="A count is a proxy, not a measurement.|计数只是代理指标。"></b>
      <span data-l="How often a report raises a theme is a rough stand-in for how much weight it puts on it. It is sensitive to report length, drafting habit and vocabulary. That is exactly why every province&rsquo;s number is one hover away from the sentences that produced it — read those before drawing a conclusion from a colour.|报告提及某主题的频次，只是其重视程度的粗略代理，受报告长度、行文习惯与用词影响。因此每一数值均可悬停查看其原文出处——在依据颜色下结论前，请先读原文。"></span></li>
    <li><b data-l="The vocabularies are policy-specific on purpose.|词表刻意限定为政策用语。"></b>
      <span data-l="Bare 消费 appears 772 times across the corpus and would measure prose style, not policy attention, so the consumption map counts only demand-side policy terms. The same applies to the other two maps; the exact term lists are in scripts/build_report_maps.py.|语料中仅&ldquo;消费&rdquo;二字即出现772次，计入将测量行文风格而非政策关注度，故消费地图仅统计需求侧政策用语。其余主题同理，完整词表见 scripts/build_report_maps.py。"></span></li>
    <li><b data-l="One report reads awkwardly.|一份报告文本较为破碎。"></b>
      <span data-l="Jiangsu&rsquo;s only reachable source is the congress gazette PDF, whose two-column layout interleaves lines when converted to text. Its sentences are legible but occasionally jumbled; the figures in them are intact.|江苏唯一可取得的来源为人大公报 PDF，其双栏排版在转换为文本时会交错换行。句子可读但偶有错位，其中数据完整。"></span></li>
    <li><b data-l="Targets are not forecasts.|目标不是预测。"></b>
      <span data-l="The growth map shows what each provincial government set for itself and put to its own people&rsquo;s congress, plotted at the midpoint where a range was published.|增长地图显示各省政府自行设定并提交本级人大的目标，公布区间者按中值绘制。"></span></li>
  </ul>
</div>

<footer>
  <span data-l="Source: each province&rsquo;s own 2026 government work report. Boundaries: DataV.GeoAtlas.|来源：各省2026年政府工作报告。行政区划边界：DataV.GeoAtlas。"></span><br>
  built for <a href="https://github.com/yqcao/China-Fiscal-Data">github.com/yqcao/China-Fiscal-Data</a>
</footer>
</div>

<script>
const P = __PAYLOAD__;
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
const AX = dark ? '#9aa' : '#666', FG = dark ? '#e6e6e6' : '#1a1a1a',
      CARD = dark ? '#1e1f23' : '#fff', BD = dark ? '#2c2e33' : '#e3e3e6';
/* One sequential hue, light to dark — these are magnitudes, not identities. The
   same ramp on all four maps: they measure different things, and giving each its
   own hue would imply a relationship between them that does not exist. */
const RAMP = dark ? ['#184f95','#256abf','#2a78d6','#3987e5','#6da7ec','#9ec5f4']
                  : ['#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95'];
const NODATA = dark ? '#3a3d43' : '#dcdde0';
let lang = 'en', pinned = {};
const L = (e, z) => lang === 'en' ? e : z;
const nm = r => lang === 'en' ? r.en : r.cn;
const byCn = {}; P.rows.forEach(r => byCn[r.cn] = r);

const MAPS = P.topics.map(t => ({...t, kind:'count'}))
  .concat([{key:'growth', en:'2026 growth target', zh:'2026年增长目标',
            note_en:'The GDP growth target each province set for itself, midpoint where a range was published.',
            note_zh:'各省自行设定的地区生产总值增长目标，区间按中值绘制。', kind:'target'}]);

function val(r, m){ return m.kind === 'target' ? r.mid : (r[m.key] ? r[m.key].n : 0); }
function shownTarget(r){
  if (r.low == null) return '–';
  const base = r.high !== r.low ? r.low + '–' + r.high + '%' : r.low + '%';
  return base + ({'左右':L(' (around)','左右'),'以上':L(' (or more)','以上'),
                  '以内':L(' (or less)','以内'),'区间':''}[r.phrasing] || '');
}
function applyL(){
  document.querySelectorAll('[data-l]').forEach(e=>{
    const a=e.getAttribute('data-l'), i=a.indexOf('|');
    e.innerHTML = lang==='en' ? a.slice(0,i) : a.slice(i+1);
  });
}
function esc(s){ return s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
/* Highlight the matched terms inside the quote so the reader can see instantly
   why a sentence was counted. */
function hl(q, terms){
  let out = esc(q);
  terms.slice().sort((a,b)=>b.length-a.length).forEach(t=>{
    out = out.split(esc(t)).join('<mark>' + esc(t) + '</mark>');
  });
  return out;
}

function renderPanel(m, cn){
  const el = document.getElementById('panel_' + m.key);
  if (!cn){ el.innerHTML = `<div class="hint">${L('Hover a province to see its sentences.','将光标移至某省以查看原文。')}</div>`; return; }
  const r = byCn[cn];
  if (!r){ el.innerHTML = `<div class="hint">${cn} — ${L('not in the dataset','不在数据集内')}</div>`; return; }
  if (m.kind === 'target'){
    el.innerHTML = `<div class="ph">${nm(r)} <span>${shownTarget(r)}</span></div>` +
      `<div class="src">${L('Source','出处')}: <a href="${r.url}" target="_blank" rel="noopener">${r.domain}</a></div>`;
    return;
  }
  const d = r[m.key] || {n:0, qs:[], more:0};
  let h = `<div class="ph">${nm(r)} <span>${d.n} ${L('mentions','次提及')}</span></div>`;
  h += d.qs.length
     ? '<ul>' + d.qs.map(x=>`<li>${hl(x.q, x.t)}</li>`).join('') + '</ul>' +
       (d.more ? `<div class="src">${L('+'+d.more+' more sentence(s) not shown','另有 '+d.more+' 句未显示')}</div>` : '')
     : `<div class="hint">${L('This report does not mention the theme.','该报告未提及此主题。')}</div>`;
  h += `<div class="src">${L('Source','出处')}: <a href="${r.url}" target="_blank" rel="noopener">${r.domain}</a></div>`;
  el.innerHTML = h;
}

const charts = {};
echarts.registerMap('china', P.geo);

function build(){
  document.getElementById('grid').innerHTML = MAPS.map(m=>`
    <div class="card">
      <h3>${L(m.en, m.zh)}</h3>
      <p class="note">${L(m.note_en, m.note_zh)}</p>
      <div class="map" id="map_${m.key}"></div>
      <div class="panel" id="panel_${m.key}"></div>
    </div>`).join('');
  MAPS.forEach(m=>{
    const c = echarts.init(document.getElementById('map_' + m.key));
    charts[m.key] = c;
    const vals = P.rows.map(r=>val(r,m)).filter(v=>v!=null);
    c.setOption({
      textStyle:{color:FG},
      tooltip:{trigger:'item', formatter:p=>{
        const r = byCn[p.name]; if(!r) return p.name;
        return m.kind==='target' ? `<b>${nm(r)}</b><br>${shownTarget(r)}`
             : `<b>${nm(r)}</b><br>${(r[m.key]||{n:0}).n} ${L('mentions','次提及')}`;
      }},
      visualMap:{type:'continuous', min:Math.min(...vals), max:Math.max(...vals),
        left:6, bottom:6, itemHeight:78, inRange:{color:RAMP}, calculable:true,
        textStyle:{color:AX, fontSize:10}},
      series:[{type:'map', map:'china', roam:false,
        data:P.rows.map(r=>({name:r.cn, value:val(r,m)})),
        itemStyle:{areaColor:NODATA, borderColor:BD, borderWidth:.5},
        emphasis:{label:{show:false}, itemStyle:{borderColor:FG, borderWidth:1.2}},
        select:{disabled:true}}]
    }, true);
    c.on('mouseover', e => { if(!pinned[m.key]) renderPanel(m, e.name); });
    c.on('mouseout',  () => { if(!pinned[m.key]) renderPanel(m, null); });
    c.on('click', e => {
      pinned[m.key] = (pinned[m.key] === e.name) ? null : e.name;
      renderPanel(m, pinned[m.key] || e.name);
    });
    renderPanel(m, pinned[m.key] || null);
  });
}

document.getElementById('lang').onclick = e => {
  if (e.target.tagName !== 'BUTTON') return;
  lang = e.target.dataset.v;
  [...e.currentTarget.children].forEach(b => b.classList.toggle('on', b === e.target));
  document.body.classList.toggle('lang-en', lang === 'en');
  applyL(); build();
};
addEventListener('resize', () => Object.values(charts).forEach(c => c.resize()));
applyL(); build();
</script>
</body>
</html>
'''

HTML = HTML.replace('__PAYLOAD__', P)
open(BASE + 'report-maps.html', 'w', encoding='utf-8').write(HTML)
print(f'wrote report-maps.html {round(len(HTML)/1024,1)} KB')
for t in TOPICS:
    n = sum(1 for r in rows if r[t['key']]['n'])
    tot = sum(r[t['key']]['n'] for r in rows)
    q = sum(len(r[t['key']]['qs']) for r in rows)
    print(f"  {t['en']:32} {n:>2}/{len(rows)} provinces, {tot:>3} mentions, {q} quotes shown")
