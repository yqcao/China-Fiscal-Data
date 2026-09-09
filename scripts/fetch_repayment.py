#!/usr/bin/env python3
"""Refresh local-government-bond principal-repayment series.

Source: MOF monthly 地方政府债券发行和债务余额情况
  预算司   https://yss.mof.gov.cn/zhuantilanmu/dfzgl/sjtj/   (history through 2024)
  债务管理司 https://zwgls.mof.gov.cn/tjsj/                    (2024-12 onward)

Regenerates data/mof-debt-balance/repayment_series.json: YTD principal repaid
(亿元), split into refinancing-bond-funded and fiscal-fund-funded, plus the
month's issuance (total / general / special / new / refinancing, 亿元), average
issue rate (%) and maturity (years), YTD total issuance, interest paid, and the
month-end debt balance (total / general / special / bond / non-bond, 亿元) with
remaining maturity, average coupon and the NPC debt ceiling. The issuance fields
let the monitor show a month before the China Government Debt Center's fuller
市场报告 for it is published (that report lags this release by 3-4 weeks).
Idempotent.
"""
import os, re, html, json, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'mof-debt-balance')
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
SOURCES = [
    ('yss',   'https://yss.mof.gov.cn/zhuantilanmu/dfzgl/sjtj',  'listing_yss', 'raw_yss'),
    ('zwgls', 'https://zwgls.mof.gov.cn/tjsj',                    'listing',     'raw'),
]

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')

def fetch(listbase, listdir, rawdir):
    os.makedirs(os.path.join(DIR, listdir), exist_ok=True)
    os.makedirs(os.path.join(DIR, rawdir), exist_ok=True)
    first = get(listbase + '/index.htm')
    open(os.path.join(DIR, listdir, 'index.htm'), 'w', encoding='utf-8').write(first)
    n = int(re.search(r'countPage\s*=\s*(\d+)', first).group(1))
    for i in range(1, n):
        try:
            open(os.path.join(DIR, listdir, f'index_{i}.htm'), 'w', encoding='utf-8').write(get(f'{listbase}/index_{i}.htm'))
            time.sleep(0.15)
        except Exception as e:
            print('  listing', i, 'failed:', e)
    urls, seen = [], set()
    for f in sorted(os.listdir(os.path.join(DIR, listdir))):
        t = open(os.path.join(DIR, listdir, f), encoding='utf-8', errors='replace').read()
        for rel in re.findall(r'href="\.?/?(\d{6}/t\d{8}_\d+\.htm)"', t):
            u = listbase + '/' + rel
            if u not in seen: seen.add(u); urls.append(u)
    new = 0
    for u in urls:
        name = re.search(r'(\d{6}/t\d{8}_\d+)', u).group(1).replace('/', '_') + '.htm'
        out = os.path.join(DIR, rawdir, name)
        if not os.path.exists(out):
            try:
                open(out, 'w', encoding='utf-8').write(get(u)); time.sleep(0.15); new += 1
            except Exception as e:
                print('  article failed', u, e)
    print(f'    {len(urls)} articles ({new} new)')

def clean(t):
    b = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S | re.I)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', b)))
def numg(s): return float(re.sub(r'\s', '', s))
def parse_issuance(t, yr, mo):
    """Issuance for the month (and YTD total) in 亿元. All whitespace is stripped
    first: the releases scatter spaces inside numbers ("363 5 亿元", "2.8 5 %").
    Wordings seen 2021-2026:
      全国发行地方政府债券X亿元。其中，发行一般债券X亿元，发行专项债券X亿元；按用途划分，
        发行新增债券X亿元，发行再融资债券X亿元  (or 全部为再融资债券)          [2021]
      全国发行新增(地方政府)债券X亿元，其中一般债券X亿元、专项债券X亿元。全国发行再融资债券X亿元，
        其中…。(合计，)全国发行地方政府债券(合计)X亿元，其中一般债券X亿元、专项债券X亿元 [2022+]"""
    z = re.sub(r'\s', '', t)
    N = r'([\d.]+)'
    r = {}
    m = re.search(rf'{yr}年{mo}月，(.*?)[（(]二[）)]', z)
    if not m: return r
    s = m.group(1)
    g = re.search(rf'全国发行地方政府债券(?:合计)?{N}亿元[。，]其中，?(?:发行)?一般债券{N}亿元[、，](?:发行)?专项债券{N}亿元', s)
    if g: r['issue'], r['general'], r['special'] = map(float, g.groups())
    g = re.search(rf'新增(?:地方政府)?债券{N}亿元', s)
    if g: r['new'] = float(g.group(1))
    g = re.search(rf'再融资债券{N}亿元', s)
    if g: r['refi'] = float(g.group(1))
    if 'issue' in r and 'new' not in r:
        if '全部为再融资债券' in s: r['new'], r['refi'] = 0.0, r['issue']
        elif '全部为新增债券' in s: r['new'], r['refi'] = r['issue'], 0.0
    g = re.search(rf'平均发行期限{N}年', s)
    if g: r['maturity'] = float(g.group(1))
    g = re.search(rf'平均发行利率{N}%', s)
    if g: r['rate'] = float(g.group(1))
    # YTD total issuance from the 1-N月 section (January has none: YTD = month)
    if mo > 1:
        y = re.search(rf'1-{mo}月，.*?全国发行地方政府债券(?:合计)?{N}亿元', z)
        if y: r['cum_issue'] = float(y.group(1))
        y = re.search(rf'1-{mo}月，全国发行新增(?:地方政府)?债券{N}亿元，其中一般债券{N}亿元、专项债券{N}亿元', z)
        if y: r['cum_new_special'] = float(y.group(3))
    elif 'issue' in r:
        r['cum_issue'] = r['issue']
        y = re.search(rf'新增(?:地方政府)?债券{N}亿元，其中一般债券{N}亿元、专项债券{N}亿元', z)
        if y: r['cum_new_special'] = float(y.group(3))
    return r

def parse_balance(t, yr, mo):
    """Section 二、全国地方政府债务余额情况 (亿元 / years / %), interest paid, and the
    NPC-approved debt ceiling when the release restates it (most months; not
    January or December, when the year's limit is not yet / no longer quoted)."""
    z = re.sub(r'\s', '', t)
    N = r'([\d.]+)'
    r = {}
    g = re.search(rf'截至{yr}年{mo}月末，全国地方政府债务余额{N}亿元?[，,。].*?其中，一般债务{N}亿元，专项债务{N}亿元；政府债券{N}亿元，非政府债券形式存量政府债务{N}亿元', z)
    if g: r['bal'], r['bal_gen'], r['bal_spec'], r['bal_bond'], r['bal_nonbond'] = map(float, g.groups())
    g = re.search(rf'剩余平均年限{N}年，其中一般债券{N}年[，、]专项债券{N}年；平均利率{N}%，其中一般债券{N}%[，、]专项债券{N}%', z)
    if g:
        r['rem_mat'], r['rem_mat_gen'], r['rem_mat_spec'], r['avg_rate'], r['avg_rate_gen'], r['avg_rate_spec'] = map(float, g.groups())
    g = re.search(rf'{yr}年全国地方政府债务限额为{N}亿元，其中一般债务限额{N}亿元，专项债务限额{N}亿元', z)
    if g: r['limit'], r['limit_gen'], r['limit_spec'] = map(float, g.groups())
    g = re.search(rf'地方政府债券支付利息{N}亿元', z)
    if g: r['interest_ytd'] = float(g.group(1))
    g = re.search(rf'{mo}月当月地方政府债券支付利息{N}亿元', z)
    if g: r['interest_month'] = float(g.group(1))
    elif mo == 1 and 'interest_ytd' in r: r['interest_month'] = r['interest_ytd']
    return r

def parse():
    rows = {}
    for _, _, _, rawdir in SOURCES:
        d = os.path.join(DIR, rawdir)
        if not os.path.isdir(d): continue
        for f in os.listdir(d):
            if not f.endswith('.htm'): continue
            t = clean(open(os.path.join(d, f), encoding='utf-8', errors='replace').read())
            ti = re.search(r'(\d{4})年(\d{1,2})月地方政府债券发行和债务余额情况', t)
            if not ti: continue
            yr, mo = int(ti.group(1)), int(ti.group(2))
            if yr < 2021: continue
            rec = {'year': yr, 'month': mo, 'period': f'{yr}-{mo:02d}'}
            m = re.search(r'到期偿还本金\s*([\d ]+?)\s*亿元，其中发行再融资债券偿还本金\s*([\d ]+?)\s*亿元、安排财政资金等偿还本金\s*([\d ]+?)\s*亿元', t)
            if m:
                rec['repay_ytd'], rec['repay_refi_ytd'], rec['repay_fisc_ytd'] = numg(m.group(1)), numg(m.group(2)), numg(m.group(3))
            else:
                m2 = re.search(r'到期偿还本金\s*([\d ]+?)\s*亿元', t)
                if not m2: continue
                rec['repay_ytd'] = numg(m2.group(1))
            rec.update(parse_issuance(t, yr, mo))
            rec.update(parse_balance(t, yr, mo))
            rows[(yr, mo)] = rec      # later sources (zwgls) override earlier for duplicate months
    out = sorted(rows.values(), key=lambda x: (x['year'], x['month']))
    json.dump(out, open(os.path.join(DIR, 'repayment_series.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    n_iss = sum(1 for r in out if 'issue' in r and 'rate' in r)
    n_bal = sum(1 for r in out if 'bal' in r)
    print(f'  repayment_series.json: {len(out)} months {out[0]["period"]}..{out[-1]["period"]} ({n_iss} with issuance, {n_bal} with debt balance)')

if __name__ == '__main__':
    print('Fetching MOF 地方政府债券发行和债务余额情况 ...')
    for name, base, ld, rd in SOURCES:
        print('  source:', name)
        try: fetch(base, ld, rd)
        except Exception as e: print('   ', name, 'failed:', e)
    parse()
