#!/usr/bin/env python3
"""Refresh the China goods-trade (货物进出口) YoY series.

SOURCE SELECTION
----------------
Primary attempt: China Customs (customs.gov.cn). From this environment that host
returns HTTP 412 from a JS-challenge anti-bot WAF even with fully browser-like
headers AND cookie replay (verified), so we cannot read it without a JS engine.
We therefore FALL BACK to NBS.

Source actually used: NBS 数据发布  https://www.stats.gov.cn/sj/zxfb/ (REACHABLE).
NBS does NOT publish a standalone 货物进出口 release on this listing; instead the
goods-trade numbers live inside the monthly macro report "…国民经济运行…"
(e.g. "5月份国民经济运行总体平稳、向新向优", "1—4月份国民经济保持稳中有进…",
"一季度国民经济实现良好开局"). Each report contains, verbatim, e.g.:
  "5月份，货物进出口总额44516亿元，同比增长16.9%…其中，出口25878亿元，
   增长13.8%；进口18638亿元，增长21.5%。1—5月份，货物进出口总额206827亿元，
   同比增长15.3%。其中，出口…增长11.8%；进口…"
We extract the SINGLE-MONTH YoY when the report states it ("N月份，货物进出口…",
cumulative=false); otherwise the YEAR-TO-DATE cumulative figure
("1—M月份/一季度/上半年/前三季度/全年，货物进出口…", cumulative=true).
All figures are RMB-denominated (亿元).

We paginate the listing (index.html + index_1.html .. up to 24 pages) like the
CPI fetcher and do NOT stop at the first report-less page. Idempotent: merges
with data/macro/trade_series.json on disk. Raw HTML cached under trade_raw/.

Record schema:
  {period, year, month, exports_yoy, imports_yoy, total_yoy,
   basis:'RMB', cumulative:bool, title, url}
"""
import os, re, ssl, json, time, html, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'macro')
RAW  = os.path.join(DIR, 'trade_raw')
LIST = 'https://www.stats.gov.cn/sj/zxfb/'
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
CTX  = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE

# --- Customs anti-bot probe (real attempt, then fall back) ------------------
CUSTOMS_URL = 'http://www.customs.gov.cn/customs/302249/zfxxgk/2799825/302274/302277/302276/index.html'
CUSTOMS_HDR = {
    'User-Agent': UA,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'identity',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def try_customs():
    """True if customs.gov.cn served real content. First GET grabs any
    Set-Cookie, then we retry with it (still 412 in practice: JS challenge)."""
    cookie = None
    for attempt in range(2):
        hdr = dict(CUSTOMS_HDR)
        if cookie: hdr['Cookie'] = cookie
        try:
            req = urllib.request.Request(CUSTOMS_URL, headers=hdr)
            r = urllib.request.urlopen(req, timeout=20, context=CTX)  # fail fast; this host blocks us anyway
            body = r.read()
            print(f'  customs attempt {attempt}: HTTP {r.status}, {len(body)} bytes')
            return len(body) > 3000
        except urllib.error.HTTPError as e:
            sc = e.headers.get('Set-Cookie')
            print(f'  customs attempt {attempt}: HTTP {e.code} (anti-bot)'
                  + ('; Set-Cookie captured, replaying' if sc else ''))
            if sc: cookie = sc.split(';')[0]
        except Exception as e:
            print(f'  customs attempt {attempt}: {type(e).__name__}: {e}')
            return False
    return False

# --- HTTP -------------------------------------------------------------------
def get(url, tries=3, timeout=45):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': LIST})
            return urllib.request.urlopen(req, timeout=timeout, context=CTX).read().decode('utf-8', 'replace')
        except Exception as e:
            if i == tries-1: raise
            time.sleep(1.5*(i+1))

def signed(direction, val):
    v = float(val) if val not in (None, '') else None
    if v is None:
        return 0.0 if direction == '持平' else None
    return -v if direction == '下降' else v

# --- Listing: collect NBS monthly macro reports (国民经济运行) --------------
def collect_reports(max_pages=int(os.environ.get('TRADE_MAX_PAGES', '24'))):
    """Paginate the listing; YIELD (url, title) for the monthly macro reports
    whose title contains 国民经济 (these carry the trade paragraph), as they are
    discovered. Crawls a fixed number of pages; only stops after 3 consecutive
    fetch errors (a single slow/timing-out page is retried, not fatal)."""
    seen, n, fails = set(), 0, 0
    for i in range(max_pages):
        pg = 'index.html' if i == 0 else f'index_{i}.html'
        try:
            t = get(LIST+pg); fails = 0
            print(f'  page {i} ok ({n} reports so far)', flush=True)
        except Exception as e:
            fails += 1
            print(f'  page {i} failed: {e}', flush=True)
            if fails >= 3: break
            continue
        for href, inner in re.findall(r'<a\s+[^>]*href="([^"]+?\.html)"[^>]*>(.*?)</a>', t, re.S):
            title = html.unescape(re.sub(r'\s+', '', re.sub(r'<[^>]+>', '', inner)))
            if '国民经济' not in title:
                continue
            if href.startswith('http'):  url = href
            elif href.startswith('./'):  url = LIST+href[2:]
            elif href.startswith('/'):   url = 'https://www.stats.gov.cn'+href
            else:                        url = LIST+href
            if url in seen: continue
            seen.add(url); n += 1
            yield url, title
        time.sleep(0.2)

# --- Article parse ----------------------------------------------------------
# Single-month lead (excluded when preceded by a range dash / digit, so the YTD
# "1—5月份" is not mistaken for a single "5月份"):
SINGLE = re.compile(r'(?<![—－\-至0-9])(\d{1,2})月份，货物进出口总额')
# YTD cumulative lead, several period spellings:
YTD    = re.compile(r'(1[—－\-]\d{1,2}月份|前\d{1,2}个月|一季度|上半年|前三季度|全年)，货物进出口总额')

TOTAL_IN = re.compile(r'货物进出口总额[\d.]+\s*万?亿元，同比(增长|下降|持平)\s*([\d.]+)?')
EXP_IN   = re.compile(r'出口[\d.]+\s*万?亿元，(?:同比)?(增长|下降|持平)\s*([\d.]+)?')
IMP_IN   = re.compile(r'进口[\d.]+\s*万?亿元，(?:同比)?(增长|下降|持平)\s*([\d.]+)?')

def _extract(block):
    t = TOTAL_IN.search(block); e = EXP_IN.search(block); m = IMP_IN.search(block)
    return (signed(t.group(1), t.group(2)) if t else None,
            signed(e.group(1), e.group(2)) if e else None,
            signed(m.group(1), m.group(2)) if m else None)

def _ytd_cutoff(s):
    if '一季度' in s:  return 3
    if '上半年' in s:  return 6
    if '前三季度' in s: return 9
    if '全年' in s:    return 12
    nums = re.findall(r'(\d{1,2})', s)
    return int(nums[-1]) if nums else None

def parse_report(url, title):
    os.makedirs(RAW, exist_ok=True)
    key = re.search(r'(t\d+_\d+)\.html', url)
    fn = os.path.join(RAW, (key.group(1) if key else re.sub(r'\W+', '_', url)) + '.htm')
    raw = open(fn, encoding='utf-8').read() if os.path.exists(fn) else None
    if raw is None:
        try:
            raw = get(url); open(fn, 'w', encoding='utf-8').write(raw)
        except Exception as e:
            print('  fetch failed', title, e); return None
    txt = html.unescape(re.sub(r'\s+', '', re.sub(r'<[^>]+>', '', raw)))

    # publication year/month from the URL folder (…/YYYYMM/t…)
    d = re.search(r'/(\d{4})(\d{2})/t\d+', url)
    pub_y = int(d.group(1)) if d else None
    pub_m = int(d.group(2)) if d else None

    sm = SINGLE.search(txt)
    ym = YTD.search(txt)
    if sm:
        month = int(sm.group(1)); cumulative = False; start = sm.start()
    elif ym:
        month = _ytd_cutoff(ym.group(1)); cumulative = True; start = ym.start()
    else:
        print('  no trade paragraph in', title); return None
    if month is None:
        return None

    # data year: reports are published the following month, so if the data
    # month is later in the year than the publication month it belongs to the
    # previous calendar year (e.g. Dec/annual data published in January).
    if pub_y is not None:
        year = pub_y - 1 if month > pub_m else pub_y
    else:
        m2 = re.search(r'(\d{4})年', title)
        year = int(m2.group(1)) if m2 else None

    total, exp, imp = _extract(txt[start:start+240])
    return {'period': f'{year}-{month:02d}', 'year': year, 'month': month,
            'exports_yoy': exp, 'imports_yoy': imp, 'total_yoy': total,
            'basis': 'RMB', 'cumulative': cumulative, 'title': title, 'url': url}

def main():
    os.makedirs(DIR, exist_ok=True)
    print('Probing customs.gov.cn ...')
    if try_customs():
        print('  customs served content (unexpected); this parser targets NBS, using NBS.')
    else:
        print('  customs blocked (HTTP 412 JS-challenge) -> falling back to NBS.')

    print('Fetching NBS 国民经济运行 monthly reports ...')
    path = os.path.join(DIR, 'trade_series.json')
    have = {r['period']: r for r in (json.load(open(path)) if os.path.exists(path) else [])}
    done_urls = {r['url'] for r in have.values() if r.get('total_yoy') is not None}

    def flush():
        series = [have[p] for p in sorted(have)]
        json.dump(series, open(path, 'w'), ensure_ascii=False, indent=0)
        return series

    fetched = 0
    # Parse and persist reports as they are discovered, so a slow/killed crawl
    # still leaves a valid, up-to-date trade_series.json on disk.
    for url, title in collect_reports():
        if url in done_urls:
            continue
        rec = parse_report(url, title)
        if rec and rec['year'] is not None:
            have[rec['period']] = rec; fetched += 1
            flush()
        time.sleep(0.2)
    series = flush()
    span = f'{series[0]["period"]}..{series[-1]["period"]}' if series else '-'
    print(f'  trade_series.json: {len(series)} months {span} (+{fetched} fetched)')
    for r in series[-4:]:
        tag = 'YTD' if r['cumulative'] else 'mo'
        print(f'    {r["period"]}: total {r["total_yoy"]}  exp {r["exports_yoy"]}  '
              f'imp {r["imports_yoy"]}  [RMB,{tag}]')

if __name__ == '__main__':
    main()
