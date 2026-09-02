#!/usr/bin/env python3
"""Refresh the CCDC bond-holder series for government bonds.

Source: 中央国债登记结算公司《统计月报》表 6「主要券种持有者结构」
  listing  https://www.chinabond.com.cn/zzsj/zzsj_tjsj/tjsj_tjyb/
  api      POST /cbiw/GetMonthReport/QueryTjybETJ   -> available range
           POST /cbiw/GetMonthReport/GetDataByte    -> the table, as xlsx

Regenerates data/chinabond/holders.json: month-end holdings (亿元) of central
government bonds (国债) and local government bonds (地方政府债), split by holder.
The same table backs the MOF local-bond report, which cites 中国债券信息网 as its
source — this reads it directly, and for central government bonds too.

Starts 2021-03: that is when table 6 became 主要券种持有者结构. Before it, code 06
is 债券托管量（按投资者）, which totals every bond type together and never crosses
holder with bond type — so no earlier month can be reconstructed from this report.
Idempotent — cached raw files are reused, so a refresh only fetches new months.
"""
import os, re, html, json, time, zipfile, urllib.parse, urllib.request

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR   = os.path.join(ROOT, 'data', 'chinabond')
RAW   = os.path.join(DIR, 'raw')
BASE  = 'https://www.chinabond.com.cn'
REFER = BASE + '/zzsj/zzsj_tjsj/tjsj_tjyb/'
UA    = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
START = '202103'                       # first month table 6 carries the 券种 split

def post(path, **data):
    req = urllib.request.Request(BASE + path, data=urllib.parse.urlencode(data).encode(),
                                 headers={'User-Agent': UA, 'Referer': REFER})
    return urllib.request.urlopen(req, timeout=60).read()

def months(end):
    y, m = int(START[:4]), int(START[4:])
    ey, em = int(end[:4]), int(end[4:])
    while (y, m) <= (ey, em):
        yield f'{y}{m:02d}'
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)

def fetch():
    os.makedirs(RAW, exist_ok=True)
    end = json.loads(post('/cbiw/GetMonthReport/QueryTjybETJ', language='CN'))[0]['etime'][:6]
    print(f'  range {START}..{end}')
    new = 0
    for ym in months(end):
        out = os.path.join(RAW, f'{ym}.xlsx')
        if os.path.exists(out) and os.path.getsize(out) > 0: continue
        try:
            b = post('/cbiw/GetMonthReport/GetDataByte', sBbly=ym, sCode='06', sWjlx='3')
            if len(b) < 512:                      # month not published yet
                print(f'    {ym}: empty'); continue
            open(out, 'wb').write(b); new += 1; time.sleep(0.3)
        except Exception as e:
            print(f'    {ym} failed: {e}')
    print(f'    {len(os.listdir(RAW))} months cached ({new} new)')
    return end

# ---- minimal xlsx reader (no third-party deps, matching the other scripts) ----
def cells(path):
    """{(row, col): value} for the first worksheet. Shared strings resolved."""
    with zipfile.ZipFile(path) as z:
        share = []
        if 'xl/sharedStrings.xml' in z.namelist():
            sx = z.read('xl/sharedStrings.xml').decode('utf-8', 'replace')
            share = [re.sub(r'<[^>]+>', '', si) for si in re.findall(r'<si>(.*?)</si>', sx, re.S)]
        name = next(n for n in z.namelist() if re.match(r'xl/worksheets/sheet\d+\.xml$', n, re.I))
        sheet = z.read(name).decode('utf-8', 'replace')
    out = {}
    for m in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*)>(.*?)</c>', sheet, re.S):
        col, row, attr, body = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        if 't="inlineStr"' in attr:            # these files inline every label
            t = re.search(r'<is>(.*?)</is>', body, re.S)
            val = re.sub(r'<[^>]+>', '', t.group(1)) if t else ''
        else:
            v = re.search(r'<v>(.*?)</v>', body, re.S)
            if not v: continue
            val = v.group(1)
            if 't="s"' in attr:
                val = share[int(val)] if int(val) < len(share) else ''
        out[(row, col)] = html.unescape(val)   # labels arrive as &#21512; entities
    return out

BOND   = {'国债': 'cgb', '地方政府债': 'lgb'}
HOLDER = {'商业银行': 'banks', '信用社': 'credit_unions', '保险机构': 'insurance',
          '证券公司': 'securities', '非法人产品': 'products', '境外机构': 'foreign',
          '其他': 'other_interbank', '柜台市场': 'counter', '其他市场': 'other_market',
          '合计': 'total'}
def clean(s): return re.sub(r'^[一二三四五六七八九十\d]+[、.．]\s*', '', (s or '').strip())

def parse():
    rows = []
    for f in sorted(os.listdir(RAW)):
        if not f.endswith('.xlsx'): continue
        ym = f[:6]
        c = cells(os.path.join(RAW, f))
        maxrow = max(r for r, _ in c)
        # locate the header row and which column holds each bond type
        cols = {}
        for r in range(1, maxrow + 1):
            hit = {clean(v): col for (rr, col), v in c.items() if rr == r and clean(v) in BOND}
            if len(hit) == len(BOND): cols = hit; break
        if not cols:
            print(f'    {ym}: no bond-type header'); continue
        rec = {'period': f'{ym[:4]}-{ym[4:]}', 'cgb': {}, 'lgb': {}}
        for r in range(1, maxrow + 1):
            label = clean(c.get((r, 'A')))
            k = HOLDER.get(label)
            if not k: continue
            for cn, col in cols.items():
                v = c.get((r, col))
                if v not in (None, ''): rec[BOND[cn]][k] = round(float(v), 2)
        if rec['cgb'].get('total') and rec['lgb'].get('total'): rows.append(rec)
    rows.sort(key=lambda r: r['period'])
    json.dump(rows, open(os.path.join(DIR, 'holders.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    bad = [r['period'] for r in rows for b in ('cgb', 'lgb')
           if abs(sum(v for k, v in r[b].items() if k != 'total') - r[b]['total']) > max(2.0, r[b]['total'] * 0.001)]
    print(f'  holders.json: {len(rows)} months {rows[0]["period"]}..{rows[-1]["period"]}'
          + (f'  [parts != total in {sorted(set(bad))}]' if bad else ''))

if __name__ == '__main__':
    print('Fetching CCDC 统计月报 表6 主要券种持有者结构 ...')
    fetch()
    parse()
