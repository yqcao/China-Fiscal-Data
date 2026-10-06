#!/usr/bin/env python3
"""
Province debt-limit tables from the MOF disclosure platform's 预决算公开 channel.

Each region files statutory tables there after its people's congress approves a
budget or an adjustment — 表1-5《…债务限额提前下达情况表》 and 表1-6《…债务限额调整
情况表》 — and those tables carry the one figure the platform's data API does not
publish until the following year: that region's 新增一般/专项债务限额 for the current
year. That is why the current year's quota is otherwise missing.

The channel has no listing endpoint, but its article ids are sequential and map
monotonically to publication month, and each article names its attachment, so a
bounded scan over the months of interest finds the tables without downloading
every PDF. Pages and PDFs are cached, so re-runs cost almost nothing.

    python3 scripts/fetch_celma_limits.py 2026 [first_id] [last_id]
      -> data/celma/limit_tables.json

Figures are read from the 本地区 column, which is 本级 + 下级, i.e. the whole
region. For a province with a 计划单列市 the city files its own table separately,
matching how the platform treats them as separate issuers.
"""
import json, os, re, subprocess, sys, time, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
OUT = BASE + 'data/celma/'
CACHE = BASE + 'data/celma/_cache/'
ART = 'https://www.celma.org.cn/yjsxxgk/%d.jhtml'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/140.0 Safari/537.36')
PAUSE = 0.4

# the attachment names that carry a 新增限额 figure
WANT = ('限额调整', '限额提前下达', '提前下达')


def get(url, cache_name, binary=False):
    path = CACHE + cache_name
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return open(path, 'rb').read() if binary else open(path, encoding='utf-8', errors='replace').read()
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': 'https://www.celma.org.cn/'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
    except Exception:
        raw = b''
    os.makedirs(CACHE, exist_ok=True)
    open(path, 'wb').write(raw)
    time.sleep(PAUSE)
    return raw if binary else raw.decode('utf-8', 'replace')


def scan_article(i):
    """-> (adcode, yyyymm, pdf_url, attachment name, published) or None"""
    html = get(ART % i, f'art_{i}.html')
    if not html:
        return None
    m = re.search(r'(https?://[^"\']*uploadFiles/(\d+)/attachFiles/(\d{6})/[^"\']+\.pdf)', html)
    if not m:
        return None
    name = re.search(r'>\s*([^<>]{2,60}\.pdf)\s*<', html)
    pub = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', html)
    return {'id': i, 'url': m.group(1), 'adcode': m.group(2), 'month': m.group(3),
            'file': (name.group(1).strip() if name else ''),
            'published': (pub.group(1)[:10] if pub else '')}


NUM = r'-?[\d,]+\.\d{2}'


def parse_limits(text, year):
    """
    Read 新增一般/专项债务限额 for `year` out of a 表1-5 or 表1-6, 本地区 column.

    The tables are laid out as `label  formula  本地区  本级  下级`, so the first
    number after a label is the whole-region figure. 表1-6 states the year's total
    新增限额 and, separately, the 提前下达 subset; take the total. 表1-5 carries only
    the advance batch, so it is reported as such and never mixed in.
    """
    flat = re.sub(r'[ \t]+', ' ', text)
    out = {}

    def after(label_pat, within):
        m = re.search(label_pat, within)
        if not m:
            return None
        seg = within[m.end():m.end() + 160]
        n = re.search(NUM, seg)
        return float(n.group(0).replace(',', '')) if n else None

    # 表1-6: "二、<year>年新增地方政府债务限额" then the two 其中 rows before 附/三、
    m = re.search(r'[二2][、.]\s*%d\s*年新增地方政府债务限额' % year, flat)
    if m:
        blk = flat[m.start():m.start() + 700]
        stop = re.search(r'(附[：:]|[三3][、.])', blk[40:])
        head = blk[:40 + stop.start()] if stop else blk
        out['stage'] = 'cumulative'
        out['total'] = after(r'年新增地方政府债务限额', head)
        out['general'] = after(r'一般债务限额', head)
        out['special'] = after(r'专项债务限额', head)
    else:
        # 表1-5: only the advance batch exists
        m = re.search(r'提前下达的\s*%d\s*年(?:地方政府债务新增限额|新增地方政府债务限额)' % year, flat)
        if not m:
            return None
        blk = flat[m.start():m.start() + 700]
        stop = re.search(r'([三3][、.])', blk[40:])
        head = blk[:40 + stop.start()] if stop else blk
        out['stage'] = 'advance'
        out['total'] = after(r'限额', head)
        out['general'] = after(r'一般债务限额', head)
        out['special'] = after(r'专项债务限额', head)
    if out.get('general') is None or out.get('special') is None:
        return None
    return out


def main(year=2026, first=None, last=None):
    # ids map monotonically to publication month; these bracket the year's filings
    first = first or 67600
    last = last or 70700
    os.makedirs(CACHE, exist_ok=True)
    found, scanned = [], 0
    for i in range(first, last + 1):
        a = scan_article(i)
        scanned += 1
        if not a:
            continue
        if not any(w in a['file'] for w in WANT):
            continue
        pdf = get(a['url'], f"pdf_{a['adcode']}_{i}.pdf", binary=True)
        if not pdf[:4] == b'%PDF':
            continue
        txt = subprocess.run(['pdftotext', '-layout', '-', '-'], input=pdf,
                             capture_output=True).stdout.decode('utf-8', 'replace')
        got = parse_limits(txt, year)
        if not got:
            continue
        name = re.search(r'\n\s*%s\s*([^\n]{2,20}?)%d\s*年' % (a['adcode'], year), txt)
        got.update(adcode=a['adcode'], year=year, article=ART % i,
                   pdf=a['url'], published=a['published'], file=a['file'],
                   region=(name.group(1).strip() if name else ''))
        found.append(got)
        print(f"  {a['adcode']:>4} {got.get('region',''):10s} {got['stage']:10s} "
              f"gen {got['general']:>9,.2f}  spec {got['special']:>10,.2f}  (id {i})")
        if scanned % 200 == 0:
            print(f'   … scanned {scanned}, found {len(found)}')
    json.dump({'year': year, 'unit': '亿元', 'scanned': [first, last],
               'source': 'celma.org.cn 预决算公开 (MOF disclosure platform)',
               'tables': found},
              open(OUT + f'limit_tables_{year}.json', 'w'), ensure_ascii=False, indent=1)
    cum = [t for t in found if t['stage'] == 'cumulative']
    print(f'\n  limit_tables_{year}.json: {len(found)} tables '
          f'({len(cum)} cumulative) across {len({t["adcode"] for t in found})} regions')


if __name__ == '__main__':
    a = sys.argv[1:]
    main(int(a[0]) if a else 2026,
         int(a[1]) if len(a) > 1 else None,
         int(a[2]) if len(a) > 2 else None)
