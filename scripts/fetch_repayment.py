#!/usr/bin/env python3
"""Refresh local-government-bond principal-repayment series.

Source: MOF monthly 地方政府债券发行和债务余额情况
  预算司   https://yss.mof.gov.cn/zhuantilanmu/dfzgl/sjtj/   (history through 2024)
  债务管理司 https://zwgls.mof.gov.cn/tjsj/                    (2024-12 onward)

Regenerates data/mof-debt-balance/repayment_series.json: YTD principal repaid
(亿元), split into refinancing-bond-funded and fiscal-fund-funded. Idempotent.
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
            rows[(yr, mo)] = rec      # later sources (zwgls) override earlier for duplicate months
    out = sorted(rows.values(), key=lambda x: (x['year'], x['month']))
    json.dump(out, open(os.path.join(DIR, 'repayment_series.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'  repayment_series.json: {len(out)} months {out[0]["period"]}..{out[-1]["period"]}')

if __name__ == '__main__':
    print('Fetching MOF 地方政府债券发行和债务余额情况 ...')
    for name, base, ld, rd in SOURCES:
        print('  source:', name)
        try: fetch(base, ld, rd)
        except Exception as e: print('   ', name, 'failed:', e)
    parse()
