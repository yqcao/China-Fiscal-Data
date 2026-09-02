#!/usr/bin/env python3
"""Build spending.html — expenditure composition across all four budget accounts.

What each account can actually show, and why:

  1 一般公共预算      10 functional categories, monthly. The MOF release itemises
                     exactly ten; they cover ~70% of the account, the rest unitemised.
  2 政府性基金        explicit 3-way split (central own-level / local land-related /
                     local other), monthly. Plus, as a finer proxy, the use of
                     proceeds of newly issued special bonds by field.
  3 国有资本经营      annual only, and only a central/local split — no functional
                     breakdown is published at any frequency.
  4 社会保险基金      by scheme, monthly, from MOHRSS. Excludes basic medical
                     insurance, which moved to 国家医保局 in 2018.

Inputs: fiscal_series.json, accounts_annual.json, lgb_series.json, mohrss_series.json.
"""
import json, os, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
YI2BN = 0.1          # 亿元 -> RMB bn

fis = json.load(open(BASE + 'data/mof-reports/fiscal_series.json'))
ann = json.load(open(BASE + 'data/mof-reports/accounts_annual.json'))
lgb = json.load(open(BASE + 'data/mof-research-reports/lgb_series.json'))
moh = json.load(open(BASE + 'data/mohrss/mohrss_series.json'))

def v(r, k):
    d = r.get(k)
    return d.get('v') if isinstance(d, dict) else None

# ---------------------------------------------------------------- 1. GPB
GPB_CATS = [
    ('教育支出', 'Education'), ('社会保障和就业支出', 'Social security & employment'),
    ('卫生健康支出', 'Health'), ('农林水支出', 'Agriculture, forestry & water'),
    ('城乡社区支出', 'Urban & rural community'), ('债务付息支出', 'Debt interest'),
    ('交通运输支出', 'Transport'), ('科学技术支出', 'Science & technology'),
    ('节能环保支出', 'Energy saving & environment'),
    ('文化旅游体育与传媒支出', 'Culture, tourism, sport & media'),
]
gpb_periods, gpb_data, gpb_total = [], {zh: [] for zh, _ in GPB_CATS}, []
for r in fis:
    it = {i['name']: i['v'] for i in r.get('exp_items', [])}
    if not it:
        continue
    gpb_periods.append(r['period'])
    for zh, _ in GPB_CATS:
        gpb_data[zh].append(round(it.get(zh, 0) * YI2BN, 1) if zh in it else None)
    gpb_total.append(round((v(r, 'pub_exp') or 0) * YI2BN, 1))

# ---------------------------------------------------------------- 2. GMF explicit
gmf_periods, gmf_central, gmf_land, gmf_other, gmf_total = [], [], [], [], []
for r in fis:
    tot, cen, land = v(r, 'fund_exp'), v(r, 'fund_exp_central'), v(r, 'land_exp')
    loc = v(r, 'fund_exp_local')
    if tot is None:
        continue
    if loc is None and cen is not None:
        loc = tot - cen                     # local is the residual when not stated
    gmf_periods.append(r['period'])
    gmf_total.append(round(tot * YI2BN, 1))
    gmf_central.append(round(cen * YI2BN, 1) if cen is not None else None)
    gmf_land.append(round(land * YI2BN, 1) if land is not None else None)
    gmf_other.append(round((loc - land) * YI2BN, 1)
                     if (loc is not None and land is not None) else None)

# ---------------------------------------------------------------- 2b. bond use
# The PDF tables wrap long labels across lines, so the raw field names include
# fragments ("protection", "industries", "chain logistics"). Each maps to the
# bucket its parent label belongs to; fragments therefore sum back into place.
BUCKETS = [
    ('municipal',  'Municipal & industrial park', '市政和产业园区基础设施',
     ['municipal construction and industrial park infrastructure']),
    ('transport',  'Transport infrastructure', '交通基础设施',
     ['transportation infrastructure']),
    ('social',     'Social undertakings', '社会事业',
     ['social undertaking', 'education, science, culture, health and social undertaking']),
    ('housing',    'Affordable housing & urban renewal', '保障性住房与城市更新',
     ['government-subsidized housing projects', 'government- subsidized housing projects',
      'government-subsidized housing projects and urban renewal',
      'government-subsidized housing projects of shanty areas and old community renovation',
      'government- subsidized housing projects of shanty areas and old community renovation',
      'Purchase existing commercial housing for use as affordable housing',
      'commercial housing for use as affordable housing']),
    ('agri',       'Agriculture, forestry & water', '农林水利',
     ['agriculture, forestry and water conservancy', 'agriculture,forestry and water conservancy',
      'forestry and water conservancy', 'water conservancy',
      'rural revitalization, agriculture, forestry and water conservancy']),
    ('eco',        'Ecology & environment', '生态环保',
     ['ecological construction and environmental protection', 'environmental protection',
      'protection']),
    ('land',       'Land reserve', '土地储备', ['land reserve']),
    ('logistics',  'Logistics, energy & reserves', '物流、能源与储备',
     ['infrastructure of warehouse logistics',
      'infrastructure of urban and rural cold chain logistics', 'chain logistics',
      'energy', 'new energy', 'energy, infrastructure of urban and rural cold chain logistics',
      'and oil reserves, logistics and energy',
      'infrastructure of grain and oil reserves, logistics and energy']),
    ('newinfra',   'New infra & emerging industries', '新基建与新兴产业',
     ['new infrastructure',
      'infrastructure for forward-looking and strategic emerging industries',
      'forward-looking and strategic emerging industries', 'emerging industries', 'industries']),
    ('banks',      'Small & medium bank capital', '中小银行补充资本',
     ['supporting small and medium-sized banks development',
      'supporting small and medium-sizedbanks development',
      'supporting development of small and medium-sized banks',
      'supporting smalland medium-sized banks development']),
    ('other',      'Other / unallocated', '其他',
     ['others', 'and others', 'and other fields', 'other fields']),
]
FIELD2KEY = {f: k for k, _, _, fs in BUCKETS for f in fs}
use_periods, use_data, use_total, unmapped = [], {k: [] for k, *_ in BUCKETS}, [], collections.Counter()
for r in lgb:
    u = r.get('use')
    if not u:
        continue
    acc = collections.Counter()
    for x in u:
        k = FIELD2KEY.get(x['field'])
        if k is None:
            unmapped[x['field']] += x['v']; k = 'other'
        acc[k] += x['v']
    use_periods.append(r['period'])
    for k, *_ in BUCKETS:
        use_data[k].append(round(acc.get(k, 0), 2))
    use_total.append(round(sum(acc.values()), 2))

# ---------------------------------------------------------------- 4. SIF
SIF = [('pension_urban', 'Urban employee pension', '城镇职工基本养老保险'),
       ('pension_rural', 'Rural & non-working pension', '城乡居民基本养老保险'),
       ('medical', 'Medical insurance', '医疗保险'),
       ('ui', 'Unemployment insurance', '失业保险'),
       ('injury', 'Work-injury insurance', '工伤保险'),
       ('maternity', 'Maternity insurance', '生育保险')]
sif_periods, sif_data = [], {k: [] for k, _, _ in SIF}
for r in moh:
    sif_periods.append(r['period'])
    for k, _, _ in SIF:
        x = r.get(k + '_exp')
        sif_data[k].append(round(x * YI2BN, 1) if x is not None else None)

# ---------------------------------------------------------------- 3. SCO + overview
sco = [{'year': r['year'], 'exp': round(r['sco_exp']['v'] * YI2BN, 1),
        'g': r['sco_exp']['g'],
        'central': round(r['sco_exp_central']['v'] * YI2BN, 1) if r.get('sco_exp_central') else None,
        'local': round(r['sco_exp_local']['v'] * YI2BN, 1) if r.get('sco_exp_local') else None}
       for r in ann if r.get('sco_exp')]

def moh_year(y):
    r = next((x for x in moh if x['year'] == y and x['month'] == 12), None)
    if not r:
        return None
    s = [r.get(k + '_exp') for k, _, _ in SIF]
    s = [x for x in s if x is not None]
    return round(sum(s) * YI2BN, 1) if s else None

overview = []
for r in ann:
    y = r['year']
    overview.append({'year': y,
                     'gpb': round(r['gpb_exp']['v'] * YI2BN, 1) if r.get('gpb_exp') else None,
                     'gmf': round(r['gmf_exp']['v'] * YI2BN, 1) if r.get('gmf_exp') else None,
                     'sco': round(r['sco_exp']['v'] * YI2BN, 1) if r.get('sco_exp') else None,
                     'sif': moh_year(y)})
overview = [o for o in overview if o['gpb']]

# ---------------------------------------------------------------- rebalancing
# Economic-type classification. This is analytical, NOT official: MOF's monthly
# release uses the functional classification (支出功能分类), not the economic one
# (支出经济分类), which is not published monthly. Categories that are genuinely
# mixed (S&T, which is part current R&D and part capital) or neither (debt
# interest) are kept in a separate bucket rather than forced into one side.
GPB_CLASS = {
    '社会保障和就业支出': 'cons', '教育支出': 'cons',
    '卫生健康支出': 'cons', '文化旅游体育与传媒支出': 'cons',
    '城乡社区支出': 'inv', '交通运输支出': 'inv',
    '农林水支出': 'inv', '节能环保支出': 'inv',
    '科学技术支出': 'other', '债务付息支出': 'other',
}
# Bond use-of-proceeds, same idea. Land reserve is a land-market operation rather
# than construction, so it is kept separate from hard infrastructure.
USE_CLASS = {'municipal': 'infra', 'transport': 'infra', 'agri': 'infra',
             'eco': 'infra', 'logistics': 'infra', 'newinfra': 'infra',
             'social': 'social', 'housing': 'social',
             'land': 'land', 'banks': 'fin', 'other': 'resid'}

# GPB: identical cumulative window (Jan-M) in every year, so years are comparable.
cur_m = fis[-1]['month']
years_gpb = [y for y in sorted({r['year'] for r in fis})
             if any(r['year'] == y and r['month'] == cur_m and r.get('exp_items') for r in fis)]
reb_gpb = []
for y in years_gpb:
    r = next(x for x in fis if x['year'] == y and x['month'] == cur_m)
    it = {i['name']: i['v'] for i in r['exp_items']}
    agg = collections.Counter()
    for n, val in it.items():
        agg[GPB_CLASS[n]] += val
    tot = sum(agg.values())
    reb_gpb.append({'year': y, 'tot': round(tot * YI2BN, 1),
                    **{k: round(agg[k] / tot * 100, 2) for k in ('cons', 'inv', 'other')},
                    'ratio': round(agg['cons'] / agg['inv'], 3),
                    'cat': {n: round(val / tot * 100, 3) for n, val in it.items()}})

# Bonds: shares of *itemised* proceeds. The residual "others" line jumps from
# ~2-5% of the total before 2024 to 21-26% after, with no drop in the number of
# fields reported — a disclosure change, not a reallocation. Excluding it is the
# only basis on which the named categories compare across that break.
reb_use = []
for y in sorted({r['year'] for r in lgb if r.get('use')}):
    agg, resid, gross, months = collections.Counter(), 0.0, 0.0, 0
    for r in lgb:
        if r['year'] != y or not r.get('use'):
            continue
        months += 1
        for x in r['use']:
            k = USE_CLASS.get(FIELD2KEY.get(x['field'], 'other'), 'resid')
            gross += x['v']
            if k == 'resid':
                resid += x['v']
            else:
                agg[k] += x['v']
    tot = sum(agg.values())
    if not tot:
        continue
    reb_use.append({'year': y, 'months': months,
                    'itemised': round(tot, 1), 'residual_pct': round(resid / gross * 100, 1),
                    **{k: round(agg[k] / tot * 100, 2) for k in ('infra', 'social', 'land', 'fin')},
                    'ratio': round(agg['infra'] / agg['social'], 3) if agg['social'] else None,
                    'buckets': {k: round(v / tot * 100, 3) for k, v in agg.items()}})

reb = {'gpb': reb_gpb, 'use': reb_use, 'window_month': cur_m,
       'gpb_class': GPB_CLASS,
       'use_class': {k: USE_CLASS[k] for k, *_ in BUCKETS}}

PAYLOAD = {
    'reb': reb,
    'gpb': {'periods': gpb_periods, 'cats': [{'zh': z, 'en': e} for z, e in GPB_CATS],
            'data': gpb_data, 'total': gpb_total},
    'gmf': {'periods': gmf_periods, 'central': gmf_central, 'land': gmf_land,
            'other': gmf_other, 'total': gmf_total},
    'use': {'periods': use_periods, 'buckets': [{'k': k, 'en': e, 'zh': z} for k, e, z, _ in BUCKETS],
            'data': use_data, 'total': use_total},
    'sif': {'periods': sif_periods, 'schemes': [{'k': k, 'en': e, 'zh': z} for k, e, z in SIF],
            'data': sif_data},
    'sco': sco, 'overview': overview,
    'latest': {'gpb': gpb_periods[-1] if gpb_periods else None,
               'gmf': gmf_periods[-1] if gmf_periods else None,
               'use': use_periods[-1] if use_periods else None,
               'sif': sif_periods[-1] if sif_periods else None,
               'sco': sco[-1]['year'] if sco else None},
}

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Spending Composition · 四本账支出构成</title>
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
.chart{width:100%;height:400px}.chart.sm{height:330px}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem}
@media(max-width:820px){.row2{grid-template-columns:1fr}}
.flag{font-size:.78rem;background:rgba(204,0,0,.06);border-radius:7px;padding:.45rem .6rem;margin:.1rem 0 .5rem}
@media(prefers-color-scheme:dark){.flag{background:rgba(255,107,107,.09)}}
footer{margin-top:1.6rem;font-size:.78rem;color:var(--mut)}footer a{color:var(--mut)}
.caveat{font-size:.79rem;color:var(--mut);background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:.85rem 1rem;margin-top:1.5rem}
.caveat li{margin:.3rem 0}.caveat b{color:var(--fg)}
</style>
</head>
<body class="lang-en">
<div class="wrap">

<h1>Spending Composition <span class="zh">四本账支出构成</span></h1>
<p class="sub">
  <span data-l="Where the money actually goes, across all four budget accounts|四本账的钱究竟花在哪里"></span> ·
  <a href="index.html" data-l="&larr; all data|&larr; 全部数据"></a> ·
  <a href="fiscal-drag.html" data-l="Fiscal Drag|财政拖累监测"></a> ·
  <a href="fiscal-monitor.html" data-l="Fiscal Monitor|财政运行监测"></a>
</p>

<div class="controls">
  <span class="seg" id="lang"><button data-v="en" class="on">EN</button><button data-v="zh">中文</button></span>
  <span class="lbl" data-l="basis|口径"></span>
  <span class="seg" id="basis">
    <button data-v="ytd" class="on" data-l="Cumulative YTD|年初累计"></button>
    <button data-v="mom" data-l="Single month|当月"></button>
  </span>
  <span class="lbl" data-l="scale|坐标"></span>
  <span class="seg" id="mode">
    <button data-v="lvl" class="on" data-l="Level|绝对额"></button>
    <button data-v="shr" data-l="Share %|占比 %"></button>
  </span>
</div>

<section>
  <div class="shead"><h2>The four accounts <span class="zh">四本账</span></h2>
    <p data-l="Annual expenditure by account. The general public budget and the government-managed fund dominate; state capital operations is small enough to be a rounding error.|分账户全年支出。一般公共预算与政府性基金占绝对多数；国有资本经营预算小到近似可忽略。"></p></div>
  <div class="card">
    <h3><span data-l="Annual expenditure by account|分账户全年支出"></span></h3>
    <p class="note" data-l="Social insurance covers only the schemes MOHRSS reports; basic medical insurance moved to 国家医保局 in 2018 and is not included.|社会保险仅含人社部公布的险种；基本医疗保险2018年划归国家医保局，未包含在内。"></p>
    <div id="c_ov" class="chart"></div>
  </div>
</section>

<section>
  <div class="shead"><h2>Rebalancing: consumption vs investment <span class="zh">再平衡：消费型 vs 投资型</span></h2>
    <p data-l="Is the spending mix tilting toward households or toward capital? Shown on an identical window in every year, so the comparison is like-for-like.|支出结构是在向居民倾斜还是向资本倾斜？各年采用完全相同的口径窗口，确保可比。"></p></div>
  <div class="flag" id="reb_flag"></div>
  <div class="row2">
    <div class="card">
      <h3><span data-l="General public budget mix|一般公共预算结构"></span></h3>
      <p class="note" id="reb_gpb_note"></p>
      <div id="c_reb_gpb" class="chart sm"></div>
    </div>
    <div class="card">
      <h3><span data-l="Which categories moved|哪些科目在变"></span></h3>
      <p class="note" id="reb_cat_note"></p>
      <div id="c_reb_cat" class="chart sm"></div>
    </div>
  </div>
  <div class="flag" id="use_flag"></div>
  <div class="row2">
    <div class="card">
      <h3><span data-l="New special bond proceeds mix|新增专项债资金投向结构"></span></h3>
      <p class="note" id="reb_use_note"></p>
      <div id="c_reb_use" class="chart sm"></div>
    </div>
    <div class="card">
      <h3><span data-l="Which uses moved|哪些投向在变"></span></h3>
      <p class="note" id="reb_ub_note"></p>
      <div id="c_reb_ub" class="chart sm"></div>
    </div>
  </div>
  <p class="note" data-l="Classification is analytical, not official. MOF publishes the functional classification (支出功能分类), not the economic one, so consumption/investment is assigned by category: consumption = social security &amp; employment, education, health, culture/tourism/sport/media; investment = urban &amp; rural community, transport, agriculture/forestry/water, energy saving &amp; environment; science &amp; technology and debt interest are neither and are shown separately.|分类为分析性口径，非官方。财政部公布的是支出功能分类而非经济分类，故消费/投资由科目归并：消费型＝社会保障和就业、教育、卫生健康、文化旅游体育与传媒；投资型＝城乡社区、交通运输、农林水、节能环保；科学技术与债务付息两者皆非，单独列示。"></p>
</section>

<section>
  <div class="shead"><h2>1 · General public budget <span class="zh">一般公共预算</span></h2>
    <p data-l="The ten functional categories the monthly MOF release itemises.|财政部月度公布的十个主要支出科目。"></p></div>
  <div class="flag" id="gpb_flag"></div>
  <div class="card">
    <h3><span data-l="Composition over time|支出构成走势"></span></h3>
    <p class="note" data-l="Stacked. Use the basis and scale toggles above to switch between cumulative/single-month and level/share.|堆叠图。可用上方口径与坐标开关切换累计/当月、绝对额/占比。"></p>
    <div id="c_gpb" class="chart"></div>
  </div>
  <div class="row2">
    <div class="card"><h3><span data-l="Latest composition|最新构成"></span></h3>
      <p class="note" id="gpb_pie_note"></p><div id="c_gpb_pie" class="chart sm"></div></div>
    <div class="card"><h3><span data-l="Growth by category|分项同比"></span></h3>
      <p class="note" data-l="Year-on-year, cumulative basis, latest reported period.|累计同比，最新公布期。"></p>
      <div id="c_gpb_yoy" class="chart sm"></div></div>
  </div>
</section>

<section>
  <div class="shead"><h2>2 · Government-managed fund <span class="zh">政府性基金预算</span></h2>
    <p data-l="Two views: the split MOF publishes explicitly, and — as a finer proxy — what newly issued special bonds are actually spent on.|两个视角：财政部明确公布的分项，以及作为更细颗粒度的替代口径——新增专项债的资金投向。"></p></div>
  <div class="card">
    <h3><span data-l="Published split|公布口径"></span> <span class="zh">中央本级 / 地方土地相关 / 地方其他</span></h3>
    <p class="note" data-l="The only breakdown MOF gives monthly: central own-level spending, local land-sale-related spending, and local other as the residual.|财政部按月公布的唯一拆分：中央本级支出、地方国有土地出让收入相关支出，地方其他为残差。"></p>
    <div id="c_gmf" class="chart"></div>
  </div>
  <div class="card">
    <h3><span data-l="Proxy: use of new special bond proceeds|替代口径：新增专项债资金投向"></span></h3>
    <p class="note" data-l="Reported by the China Government Debt Center for newly issued special bonds. This is a proxy — it covers only bond-funded spending, not the whole account — but it is the only fine-grained view of what the fund account buys.|数据来自中国政府债务研究和评估中心，仅覆盖新增专项债。属替代口径——只反映债券资金部分，但这是该账户支出投向唯一的细颗粒度视角。"></p>
    <div id="c_use" class="chart"></div>
  </div>
</section>

<section>
  <div class="shead"><h2>3 · State capital operations <span class="zh">国有资本经营预算</span></h2>
    <p data-l="Annual only, and only a central/local split — no functional breakdown is published at any frequency.|仅有年度数据，且只有中央/地方拆分——任何频度均未公布功能分类。"></p></div>
  <div class="card">
    <h3><span data-l="Annual expenditure, central vs local|全年支出，中央与地方"></span></h3>
    <p class="note" data-l="The smallest of the four accounts. Most of it is recapitalising state enterprises; a large share of its revenue is transferred out to the general public budget rather than spent here.|四本账中最小的一本。主要用于国有企业注资；其收入的很大一部分调入一般公共预算，而非在本账户支出。"></p>
    <div id="c_sco" class="chart sm"></div>
  </div>
</section>

<section>
  <div class="shead"><h2>4 · Social insurance funds <span class="zh">社会保险基金预算</span></h2>
    <p data-l="By scheme, from the MOHRSS monthly release.|分险种，来自人社部月度统计快报。"></p></div>
  <div class="flag" id="sif_flag"></div>
  <div class="card">
    <h3><span data-l="Fund expenditure by scheme|分险种基金支出"></span></h3>
    <p class="note" data-l="Medical and maternity insurance leave the series after 2018 — administration moved to the new 国家医保局. The series stops rather than falling to zero.|医疗与生育保险2018年后退出本序列——划归国家医保局。序列到此终止，而非归零。"></p>
    <div id="c_sif" class="chart"></div>
  </div>
</section>

<div class="caveat">
  <b data-l="How to read this / caveats|读法与说明"></b>
  <ul>
    <li data-l="All monetary values in RMB billion. MOF and MOHRSS publish cumulative year-to-date figures; the single-month basis differences consecutive releases within a year.|货币单位均为十亿元。财政部与人社部公布年初累计数；当月口径由同年相邻期差分得到。"></li>
    <li data-l="The MOF monthly release itemises ten general-public-budget categories covering roughly 70% of the account. The remaining ~30% (general public services, defense, public security, housing support and others) is not itemised monthly, so the stack does not sum to the account total.|财政部月报仅列示十个一般公共预算科目，约占该账户70%。其余约30%（一般公共服务、国防、公共安全、住房保障等）月度不单独列示，故堆叠合计不等于账户总额。"></li>
    <li data-l="Bond use-of-proceeds is a proxy for the government-fund account, not a substitute: it covers only newly issued special bonds, and the source tables wrap long labels across lines, so fragmentary field names are folded back into their parent category.|专项债资金投向为政府性基金账户的替代口径，并非等同：仅覆盖新增专项债，且原始表格长标签跨行断裂，碎片化字段已归并回其所属类别。"></li>
    <li data-l="Social insurance excludes basic medical insurance from 2018 onward, which is administered by 国家医保局 and absent from the MOHRSS table. For 2025 the schemes shown total ¥8.09tn against a full social-insurance account of about ¥11.14tn.|社会保险自2018年起不含基本医疗保险（由国家医保局管理，人社部表中无此项）。2025年所示险种合计约8.09万亿元，而社保基金账户全口径约11.14万亿元。"></li>
    <li data-l="State capital operations has no published functional breakdown, so only its total and central/local split can be shown.|国有资本经营预算未公布功能分类，故仅能展示总额与中央/地方拆分。"></li>
    <li data-l="The 2021 annual report has rolled off both MOF listings and is not recoverable from the live site, so 2021 is missing from the annual charts. Monthly 2021 data is unaffected.|2021年度报告已从财政部两个列表页滚落，无法从现网获取，故年度图表缺2021年。月度数据不受影响。"></li>
    <li data-l="Sources: MOF 全国财政收支情况 (monthly and annual), China Government Debt Center 地方政府债券市场报告, MOHRSS 主要统计快报数据.|数据来源：财政部《全国财政收支情况》（月度与年度）、中国政府债务研究和评估中心《地方政府债券市场报告》、人力资源和社会保障部《主要统计快报数据》。"></li>
  </ul>
</div>

<footer>
  <span data-l="Built for|构建于"></span>
  <a href="https://github.com/yqcao/China-Fiscal-Data">github.com/yqcao/China-Fiscal-Data</a>
</footer>
</div>

<script>
const P = __PAYLOAD__;
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
const AX = dark ? '#9aa' : '#666', GRID = dark ? '#2c2e33' : '#eee', FG = dark ? '#e6e6e6' : '#1a1a1a';
const PAL = ['#c0392b','#1463ff','#0a9d6b','#e07b00','#8b5cf6','#0891b2',
             '#d81b60','#7cb342','#5d4037','#f4511e','#546e7a'];
let lang='en', basis='ytd', mode='lvl';
const L=(e,z)=>lang==='en'?e:z;
const nm=o=>L(o.en,o.zh||o.cn);

function applyL(){
  document.querySelectorAll('[data-l]').forEach(e=>{
    const a=e.getAttribute('data-l'), i=a.indexOf('|');
    e.innerHTML = lang==='en' ? a.slice(0,i) : a.slice(i+1);
  });
}

/* YTD -> single month. firstM is the first month that stands alone in that source
   (MOF folds Jan into Feb; MOHRSS publishes a standalone January). */
function diff(periods, arr, firstM){
  return arr.map((val,i)=>{
    if(val==null) return null;
    const [y,m]=periods[i].split('-').map(Number);
    if(m===firstM) return val;
    if(i===0) return null;
    const [py,pm]=periods[i-1].split('-').map(Number);
    if(py!==y||pm!==m-1||arr[i-1]==null) return null;
    return Math.round((val-arr[i-1])*10)/10;
  });
}
function shares(cols){                       // cols: array of arrays -> % of column sum
  const n=cols[0].length, tot=[];
  for(let i=0;i<n;i++){ let s=0; cols.forEach(c=>{ if(c[i]!=null) s+=c[i]; }); tot.push(s); }
  return cols.map(c=>c.map((x,i)=> (x==null||!tot[i])?null:Math.round(x/tot[i]*1000)/10));
}
function prep(periods, cols, firstM){
  let out = basis==='mom' ? cols.map(c=>diff(periods,c,firstM)) : cols.map(c=>c.slice());
  if(mode==='shr') out = shares(out);
  return out;
}
const unit = ()=> mode==='shr' ? '%' : L('RMB bn','十亿元');

const C={};
const init=id=>C[id]||(C[id]=echarts.init(document.getElementById(id)));
const base=extra=>Object.assign({
  backgroundColor:'transparent',
  grid:{left:62,right:24,top:64,bottom:58},
  tooltip:{trigger:'axis',confine:true,axisPointer:{type:'shadow'}},
  legend:{top:2,type:'scroll',textStyle:{color:FG,fontSize:10},itemWidth:14,itemHeight:8},
  textStyle:{color:FG},
  dataZoom:[{type:'inside'},{type:'slider',height:15,bottom:12,textStyle:{color:AX,fontSize:9}}],
},extra||{});
const yA=()=>({type:'value',name:unit(),nameTextStyle:{color:AX,fontSize:10},
  axisLabel:{color:AX,fontSize:10},splitLine:{lineStyle:{color:GRID}},
  max: mode==='shr'?100:null});
const xA=p=>({type:'category',data:p,axisLabel:{color:AX,fontSize:10},axisLine:{lineStyle:{color:GRID}}});

function stack(id, periods, names, cols, firstM){
  const d=prep(periods,cols,firstM);
  init(id).setOption({...base(), xAxis:xA(periods), yAxis:yA(),
    series:names.map((n,i)=>({name:n,type:'line',stack:'t',areaStyle:{opacity:.85},
      showSymbol:false,lineStyle:{width:0},emphasis:{focus:'series'},
      itemStyle:{color:PAL[i%PAL.length]},data:d[i]}))},true);
}

function drawRebal(){
  const R=P.reb, G=R.gpb, U=R.use;
  const g0=G[0], g1=G[G.length-1], u0=U[0], u1=U[U.length-1];
  const MN=['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][R.window_month];

  document.getElementById('reb_flag').innerHTML = L(
    `General public budget, Jan–${MN} in every year: consumption-related spending has gone from <b>${g0.cons.toFixed(1)}%</b> of itemised spending in ${g0.year} to <b>${g1.cons.toFixed(1)}%</b> in ${g1.year} (<b>${(g1.cons-g0.cons>=0?'+':'')+(g1.cons-g0.cons).toFixed(1)}pp</b>), while investment-related fell from <b>${g0.inv.toFixed(1)}%</b> to <b>${g1.inv.toFixed(1)}%</b> (<b>${(g1.inv-g0.inv).toFixed(1)}pp</b>). The consumption-to-investment ratio moved from <b>${g0.ratio.toFixed(2)}</b> to <b>${g1.ratio.toFixed(2)}</b>.`,
    `一般公共预算，各年1—${R.window_month}月：消费型支出占列示支出的比重由 ${g0.year} 年的 <b>${g0.cons.toFixed(1)}%</b> 升至 ${g1.year} 年的 <b>${g1.cons.toFixed(1)}%</b>（<b>${(g1.cons-g0.cons>=0?'+':'')+(g1.cons-g0.cons).toFixed(1)}个百分点</b>），投资型由 <b>${g0.inv.toFixed(1)}%</b> 降至 <b>${g1.inv.toFixed(1)}%</b>（<b>${(g1.inv-g0.inv).toFixed(1)}个百分点</b>）。消费/投资比由 <b>${g0.ratio.toFixed(2)}</b> 升至 <b>${g1.ratio.toFixed(2)}</b>。`);

  document.getElementById('use_flag').innerHTML = L(
    `Bond proceeds move the other way. On the same itemised basis, social &amp; housing fell from <b>${u0.social.toFixed(1)}%</b> to <b>${u1.social.toFixed(1)}%</b> (<b>${(u1.social-u0.social).toFixed(1)}pp</b>) while hard infrastructure stayed near <b>${u1.infra.toFixed(0)}%</b> and land reserve appeared from 2025 at <b>${u1.land.toFixed(1)}%</b>. <b>Caveat:</b> the source lumps ${u0.residual_pct.toFixed(0)}% of proceeds into “others” in ${u0.year} but ${u1.residual_pct.toFixed(0)}% in ${u1.year} with no drop in fields reported — a disclosure change. Shares here therefore exclude that residual.`,
    `专项债投向方向相反。同一列示口径下，社会事业与保障房由 <b>${u0.social.toFixed(1)}%</b> 降至 <b>${u1.social.toFixed(1)}%</b>（<b>${(u1.social-u0.social).toFixed(1)}个百分点</b>），硬基建维持在 <b>${u1.infra.toFixed(0)}%</b> 左右，土地储备自2025年起出现，占 <b>${u1.land.toFixed(1)}%</b>。<b>注意：</b>原始表中“其他”占比由 ${u0.year} 年的 ${u0.residual_pct.toFixed(0)}% 升至 ${u1.year} 年的 ${u1.residual_pct.toFixed(0)}%，而列示字段数并未减少——属披露口径变化。故此处占比已剔除该残差。`);

  document.getElementById('reb_gpb_note').textContent =
    L(`Share of itemised expenditure, Jan–${MN} of each year. Line is the consumption-to-investment ratio (right axis).`,
      `占列示支出比重，各年1—${R.window_month}月。折线为消费/投资比（右轴）。`);
  document.getElementById('reb_use_note').textContent =
    L('Share of itemised proceeds, excluding the "others" residual. Line is the infrastructure-to-social ratio (right axis).',
      '占列示资金比重，已剔除“其他”残差。折线为基建/社会事业比（右轴）。');
  document.getElementById('reb_cat_note').textContent =
    L(`Change in share of itemised spending, ${g0.year} to ${g1.year}, percentage points.`,
      `占列示支出比重的变化，${g0.year} 至 ${g1.year}，百分点。`);
  document.getElementById('reb_ub_note').textContent =
    L(`Change in share of itemised proceeds, ${u0.year} to ${u1.year}, percentage points.`,
      `占列示资金比重的变化，${u0.year} 至 ${u1.year}，百分点。`);

  const mixOpt=(rows,keys,names,cols,ratioName)=>({
    backgroundColor:'transparent',textStyle:{color:FG},
    grid:{left:44,right:52,top:34,bottom:28},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},confine:true,
      valueFormatter:v=>v==null?'—':(+v).toFixed(1)},
    legend:{top:2,textStyle:{color:FG,fontSize:10},itemWidth:13,itemHeight:8},
    xAxis:{type:'category',data:rows.map(r=>r.year),axisLabel:{color:AX,fontSize:10},
           axisLine:{lineStyle:{color:GRID}}},
    yAxis:[{type:'value',max:100,axisLabel:{color:AX,fontSize:10,formatter:'{value}%'},
            splitLine:{lineStyle:{color:GRID}}},
           {type:'value',axisLabel:{color:AX,fontSize:10},splitLine:{show:false}}],
    series:keys.map((k,i)=>({name:names[i],type:'bar',stack:'m',barMaxWidth:46,
        itemStyle:{color:cols[i]},data:rows.map(r=>r[k])}))
      .concat([{name:ratioName,type:'line',yAxisIndex:1,symbol:'circle',symbolSize:6,
        lineStyle:{width:2.4,color:FG},itemStyle:{color:FG},data:rows.map(r=>r.ratio)}])});

  init('c_reb_gpb').setOption(mixOpt(G,['cons','inv','other'],
    [L('Consumption-related','消费型'),L('Investment-related','投资型'),L('Neither (S&T, interest)','两者皆非（科技、付息）')],
    ['#0a9d6b','#c0392b','#9aa3ad'], L('Consumption / investment','消费/投资比')), true);

  init('c_reb_use').setOption(mixOpt(U,['infra','social','land','fin'],
    [L('Hard infrastructure','硬基建'),L('Social & housing','社会事业与保障房'),
     L('Land reserve','土地储备'),L('Bank capital','银行补充资本')],
    ['#c0392b','#0a9d6b','#e07b00','#8b5cf6'], L('Infra / social','基建/社会事业')), true);

  const ppOpt=(items,colorOf)=>({
    backgroundColor:'transparent',textStyle:{color:FG},
    grid:{left:158,right:46,top:10,bottom:26},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},confine:true,
      valueFormatter:v=>(v>0?'+':'')+(+v).toFixed(2)+'pp'},
    xAxis:{type:'value',axisLabel:{color:AX,fontSize:10,formatter:'{value}'},
           splitLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'category',data:items.map(x=>x.n),axisLabel:{color:AX,fontSize:10},
           axisLine:{lineStyle:{color:GRID}}},
    series:[{type:'bar',barMaxWidth:13,data:items.map(x=>({value:x.v,itemStyle:{color:colorOf(x)}})),
      label:{show:true,position:'right',color:FG,fontSize:9.5,
        formatter:p=>(p.value>0?'+':'')+p.value.toFixed(1)}}]});

  const CLR={cons:'#0a9d6b',inv:'#c0392b',other:'#9aa3ad',
             infra:'#c0392b',social:'#0a9d6b',land:'#e07b00',fin:'#8b5cf6'};
  const catItems=P.gpb.cats.map(c=>({n:L(c.en,c.zh),
      v:(g1.cat[c.zh]||0)-(g0.cat[c.zh]||0), cls:R.gpb_class[c.zh]}))
    .sort((a,b)=>a.v-b.v);
  init('c_reb_cat').setOption(ppOpt(catItems,x=>CLR[x.cls]),true);

  const ubItems=P.use.buckets.filter(b=>R.use_class[b.k]!=='resid')
    .map(b=>({n:L(b.en,b.zh), v:(u1.buckets[b.k]||0)-(u0.buckets[b.k]||0), cls:R.use_class[b.k]}))
    .sort((a,b)=>a.v-b.v);
  init('c_reb_ub').setOption(ppOpt(ubItems,x=>CLR[x.cls]),true);
}

function draw(){
  drawRebal();
  // overview
  const ov=P.overview, on=[L('General public budget','一般公共预算'),
    L('Government-managed fund','政府性基金'),L('Social insurance (MOHRSS schemes)','社会保险（人社部险种）'),
    L('State capital operations','国有资本经营')];
  init('c_ov').setOption({...base({grid:{left:70,right:24,top:44,bottom:40},dataZoom:[]}),
    xAxis:{type:'category',data:ov.map(o=>o.year),axisLabel:{color:AX},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',name:L('RMB bn','十亿元'),nameTextStyle:{color:AX,fontSize:10},
           axisLabel:{color:AX,fontSize:10},splitLine:{lineStyle:{color:GRID}}},
    series:[['gpb',0],['gmf',1],['sif',2],['sco',3]].map(([k,i])=>({
      name:on[i],type:'bar',stack:'a',itemStyle:{color:PAL[i]},barMaxWidth:52,
      data:ov.map(o=>o[k])}))},true);

  // GPB
  const g=P.gpb, gn=g.cats.map(c=>L(c.en,c.zh));
  stack('c_gpb', g.periods, gn, g.cats.map(c=>g.data[c.zh]), 2);

  const li=g.periods.length-1;
  const pie=g.cats.map((c,i)=>({name:gn[i],value:g.data[c.zh][li]})).filter(x=>x.value!=null);
  const covered=pie.reduce((s,x)=>s+x.value,0), tot=g.total[li];
  document.getElementById('gpb_pie_note').textContent =
    L(`${g.periods[li]} cumulative. The ten itemised categories total ¥${(covered/1000).toFixed(2)}tn of the ¥${(tot/1000).toFixed(2)}tn account (${(covered/tot*100).toFixed(0)}%).`,
      `${g.periods[li]} 累计。十个列示科目合计 ${(covered/1000).toFixed(2)} 万亿元，占该账户 ${(tot/1000).toFixed(2)} 万亿元的 ${(covered/tot*100).toFixed(0)}%。`);
  init('c_gpb_pie').setOption({backgroundColor:'transparent',textStyle:{color:FG},
    tooltip:{trigger:'item',confine:true,valueFormatter:v=>v.toLocaleString()+' '+L('bn','十亿')},
    legend:{type:'scroll',orient:'vertical',right:4,top:10,bottom:10,width:130,
            textStyle:{color:FG,fontSize:10},itemWidth:12,itemHeight:8},
    series:[{type:'pie',radius:['38%','66%'],center:['32%','52%'],
      data:pie.map((x,i)=>({...x,itemStyle:{color:PAL[i%PAL.length]}})),
      label:{show:false},emphasis:{label:{show:true,fontSize:12,formatter:p=>p.percent+'%'}}}]},true);

  // GPB yoy vs same month last year
  const cur=g.periods[li], [cy,cm]=cur.split('-').map(Number);
  const pi=g.periods.indexOf(`${cy-1}-${String(cm).padStart(2,'0')}`);
  const yoy=g.cats.map(c=>{
    const a=g.data[c.zh][li], b=pi>=0?g.data[c.zh][pi]:null;
    return (a==null||!b)?null:Math.round((a/b-1)*1000)/10;
  });
  const ord=g.cats.map((c,i)=>({n:gn[i],v:yoy[i]})).filter(x=>x.v!=null).sort((a,b)=>a.v-b.v);
  init('c_gpb_yoy').setOption({backgroundColor:'transparent',textStyle:{color:FG},
    grid:{left:150,right:40,top:14,bottom:28},
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},confine:true,valueFormatter:v=>(v>0?'+':'')+v+'%'},
    xAxis:{type:'value',axisLabel:{color:AX,fontSize:10,formatter:'{value}%'},splitLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'category',data:ord.map(x=>x.n),axisLabel:{color:AX,fontSize:10},axisLine:{lineStyle:{color:GRID}}},
    series:[{type:'bar',data:ord.map(x=>({value:x.v,itemStyle:{color:x.v>=0?'#0a9d6b':'#c0392b'}})),
      barMaxWidth:14,label:{show:true,position:'right',color:FG,fontSize:10,
        formatter:p=>(p.value>0?'+':'')+p.value+'%'}}]},true);

  // GMF explicit
  const f=P.gmf;
  stack('c_gmf', f.periods,
        [L('Central own-level','中央本级支出'),L('Local · land-sale related','地方·土地出让相关'),
         L('Local · other','地方·其他')],
        [f.central,f.land,f.other], 2);

  // bond use
  const u=P.use, un=u.buckets.map(b=>L(b.en,b.zh));
  stack('c_use', u.periods, un, u.buckets.map(b=>u.data[b.k]), 1);

  // SCO
  const s=P.sco;
  init('c_sco').setOption({...base({grid:{left:62,right:24,top:40,bottom:38},dataZoom:[]}),
    xAxis:{type:'category',data:s.map(x=>x.year),axisLabel:{color:AX},axisLine:{lineStyle:{color:GRID}}},
    yAxis:{type:'value',name:L('RMB bn','十亿元'),nameTextStyle:{color:AX,fontSize:10},
           axisLabel:{color:AX,fontSize:10},splitLine:{lineStyle:{color:GRID}}},
    series:[{name:L('Central','中央本级'),type:'bar',stack:'b',itemStyle:{color:PAL[1]},
             barMaxWidth:40,data:s.map(x=>x.central)},
            {name:L('Local','地方'),type:'bar',stack:'b',itemStyle:{color:PAL[3]},
             data:s.map(x=>x.local)}]},true);

  // SIF
  const v=P.sif, vn=v.schemes.map(x=>L(x.en,x.zh));
  stack('c_sif', v.periods, vn, v.schemes.map(x=>v.data[x.k]), 1);
}

function flags(){
  const g=P.gpb, li=g.periods.length-1;
  const cov=g.cats.reduce((s,c)=>s+(g.data[c.zh][li]||0),0), tot=g.total[li];
  document.getElementById('gpb_flag').innerHTML = L(
    `The ten itemised categories cover <b>${(cov/tot*100).toFixed(0)}%</b> of the account. The remaining <b>¥${((tot-cov)/1000).toFixed(2)}tn</b> — general public services, defense, public security, housing support and the rest — is not broken out in the monthly release.`,
    `十个列示科目覆盖该账户 <b>${(cov/tot*100).toFixed(0)}%</b>。其余 <b>${((tot-cov)/1000).toFixed(2)} 万亿元</b>（一般公共服务、国防、公共安全、住房保障等）月报未单独列示。`);
  const s=P.sif, i=s.periods.length-1;
  const shown=s.schemes.reduce((a,x)=>a+(s.data[x.k][i]||0),0);
  document.getElementById('sif_flag').innerHTML = L(
    `Shown here: <b>¥${(shown/1000).toFixed(2)}tn</b> for ${s.periods[i]}. Basic medical insurance is administered by 国家医保局 and is not in the MOHRSS table, so the full social-insurance account is materially larger.`,
    `此处所示 ${s.periods[i]} 合计 <b>${(shown/1000).toFixed(2)} 万亿元</b>。基本医疗保险由国家医保局管理，不在人社部表中，故社保基金账户全口径显著更大。`);
}

function all(){ applyL(); flags(); draw(); }
function seg(id, set){
  document.getElementById(id).addEventListener('click', e=>{
    const b=e.target.closest('button'); if(!b) return;
    set(b.dataset.v);
    document.querySelectorAll('#'+id+' button').forEach(x=>x.classList.toggle('on',x===b));
    if(id==='lang'){ document.body.classList.toggle('lang-en', lang==='en'); all(); } else draw();
  });
}
seg('lang', v=>lang=v); seg('basis', v=>basis=v); seg('mode', v=>mode=v);
addEventListener('resize', ()=>Object.values(C).forEach(c=>c.resize()));
all();
</script>
</body>
</html>
'''

out = HTML.replace('__PAYLOAD__', json.dumps(PAYLOAD, ensure_ascii=False, separators=(',', ':')))
open(BASE + 'spending.html', 'w').write(out)
print('wrote spending.html %.1f KB' % (len(out) / 1024))
print(f'  GPB   {len(gpb_periods)} periods {gpb_periods[0]}..{gpb_periods[-1]}, {len(GPB_CATS)} categories')
print(f'  GMF   {len(gmf_periods)} periods, explicit 3-way split')
print(f'  use   {len(use_periods)} periods {use_periods[0]}..{use_periods[-1]}, {len(BUCKETS)} buckets')
print(f'  SIF   {len(sif_periods)} periods {sif_periods[0]}..{sif_periods[-1]}, {len(SIF)} schemes')
print(f'  SCO   {len(sco)} years')
if unmapped:
    print('  WARNING unmapped bond-use fields folded into Other:')
    for f, v_ in unmapped.most_common():
        print(f'    {f[:60]:62s} {v_:,.1f}')
