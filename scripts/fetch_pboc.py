#!/usr/bin/env python3
"""Refresh China monetary / financing series from PBOC press releases.

Source: PBOC 调查统计司 · 金融统计数据报告 (financial statistics data report)
  Listing: http://www.pbc.gov.cn/diaochatongjisi/116219/116225/index.html
  Pagination: 11871-2.html, 11871-3.html, ... (module id 11871; index.html == page 1).

Each monthly "金融统计数据报告" carries, in numbered sections:
  一、社会融资规模存量 ... 同比增长X%        -> tsf_stock_yoy
  二、<period>社会融资规模增量 ... 为 X 万亿元  -> YTD cumulative TSF increment
  三、广义货币(M2)余额 ... 同比增长X%          -> m2_yoy
  五、<period>人民币贷款增加 X 万亿元           -> YTD cumulative new RMB loans

PBOC only prints YEAR-TO-DATE CUMULATIVE loan / TSF-increment figures (e.g.
"前五个月人民币贷款增加9.11万亿元"); January's figure equals the month itself.
We therefore derive the per-MONTH `new_loans` and `tsf_flow` by differencing the
within-year cumulative of consecutive periods (monthly = cum[t] - cum[t-1];
monthly = cum for January). Quarterly / half-year / annual reports substitute for
the missing months: 一季度->3, 上半年/二季度->6, 前三季度->9, 全年(annual)->12.

Output: data/macro/pboc_series.json — list sorted by period, each record:
  {period 'YYYY-MM', year, month, m2_yoy, new_loans(亿元), tsf_stock_yoy,
   tsf_flow(亿元), title, url}. Unparseable fields -> null.
Raw article HTML is cached under data/macro/pboc_raw/. Idempotent: rebuilds from
cache on rerun, merges with anything already on disk so history accumulates.
"""
import os, re, ssl, json, time, html, socket, urllib.request

socket.setdefaulttimeout(45)   # backstop: pbc.gov.cn sometimes holds sockets open

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'macro')
RAW  = os.path.join(DIR, 'pboc_raw')
BASE = 'http://www.pbc.gov.cn'
COL  = BASE + '/diaochatongjisi/116219/116225/'   # 金融统计数据报告 column
MODULE = '11871'                                   # pagination module id of COL
MAX_PAGES = int(os.environ.get('PBOC_MAX_PAGES', '12'))
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
CTX  = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE

def get(url, tries=3):
    for i in range(tries):
        try:
            req=urllib.request.Request(url, headers={'User-Agent':UA,'Referer':COL})
            return urllib.request.urlopen(req, timeout=45, context=CTX).read().decode('utf-8','replace')
        except Exception:
            if i==tries-1: raise
            time.sleep(1.5*(i+1))

def clean(raw):
    """Strip scripts/styles/tags -> single-spaced plain text."""
    raw=re.sub(r'(?is)<script.*?</script>',' ',raw)
    raw=re.sub(r'(?is)<style.*?</style>',' ',raw)
    return html.unescape(re.sub(r'\s+',' ', re.sub(r'<[^>]+>',' ', raw)))

def abs_url(href):
    if href.startswith('http'): return href
    if href.startswith('/'):    return BASE+href
    if href.startswith('./'):   return COL+href[2:]
    return COL+href

def period_of(title):
    """Map a 金融统计数据报告 title to (year, month) it reports on; else None.
    Monthly -> that month; quarter/half/annual -> 3/6/9/12."""
    m=re.search(r'(\d{4})年\s*(\d{1,2})月', title)
    if m: return int(m.group(1)), int(m.group(2))
    y=re.search(r'(\d{4})年', title)
    if not y: return None
    yr=int(y.group(1))
    if '一季度' in title: return yr,3
    if '上半年' in title or '二季度' in title: return yr,6
    if '前三季度' in title or '三季度' in title: return yr,9
    if '全年' in title or re.search(r'(\d{4})年金融统计数据报告', title): return yr,12
    return None

def to_yi(val, unit):
    """万亿元 -> 亿元 (*10000); 亿元 -> 亿元 (*1)."""
    v=float(val)
    return round(v*10000.0, 2) if unit=='万亿' else round(v, 2)

def signed(direction, val):
    v=float(val)
    return -v if direction=='下降' else v

# --- field extractors on cleaned article text -------------------------------
RE_M2   = re.compile(r'广义货币\s*[\(（]\s*M2\s*[\)）]\s*余额[\d.]+\s*万亿元\s*[，,]\s*同比(增长|下降)\s*([\d.]+)%')
RE_M2_H = re.compile(r'广义货币(?:\s*[\(（]\s*M2\s*[\)）])?\s*(?:余额[\d.]+万亿元[，,])?\s*同比?(增长|下降)?\s*([\d.]+)%')
RE_TSFS = re.compile(r'社会融资规模存量\s*(?:为)?\s*[\d.]+\s*万亿元\s*[，,]\s*同比(增长|下降)\s*([\d.]+)%')
RE_TSFS_H = re.compile(r'社会融资规模存量\s*同比(增长|下降)\s*([\d.]+)%')
RE_LOAN = re.compile(r'(?:\d{1,2}月份|前[\d一二两三四五六七八九十]+个月|一季度|二季度|上半年|前三季度|三季度|全年)'
                     r'人民币贷款增加\s*([\d.]+)\s*(万亿|亿)元')
RE_TSFI = re.compile(r'社会融资规模增量\s*(?:累计)?\s*为\s*([\d.]+)\s*(万亿|亿)元')

def parse_article(period, url, title):
    year, month = int(period[:4]), int(period[5:])
    rec={'period':period,'year':year,'month':month,'m2_yoy':None,'new_loans':None,
         'tsf_stock_yoy':None,'tsf_flow':None,'title':title,'url':url}
    os.makedirs(RAW, exist_ok=True)
    fn=os.path.join(RAW, period+'.htm')
    raw=open(fn,encoding='utf-8').read() if os.path.exists(fn) else None
    if raw is None:
        try:
            raw=get(url); open(fn,'w',encoding='utf-8').write(raw)
        except Exception as e:
            print('  fetch failed', period, e); return rec, None, None
    txt=clean(raw)

    m=RE_M2.search(txt) or RE_M2_H.search(txt)
    if m: rec['m2_yoy']=signed(m.group(1) or '增长', m.group(2))
    m=RE_TSFS.search(txt) or RE_TSFS_H.search(txt)
    if m: rec['tsf_stock_yoy']=signed(m.group(1), m.group(2))

    m=RE_LOAN.search(txt);  cum_loans=to_yi(m.group(1), m.group(2)) if m else None
    m=RE_TSFI.search(txt);  cum_tsf  =to_yi(m.group(1), m.group(2)) if m else None
    return rec, cum_loans, cum_tsf

def collect_links(max_pages=MAX_PAGES):
    """Crawl the paginated column; return {period:(url,title)} keeping the newest
    (first-seen) article for any period."""
    found={}
    for i in range(max_pages):
        pg='index.html' if i==0 else f'{MODULE}-{i+1}.html'
        try:
            t=get(COL+pg)
        except Exception as e:
            print('  listing stop at', pg, e); break
        n=0
        for href,inner in re.findall(r'<a\s+[^>]*href="([^"]+?\.html)"[^>]*>(.*?)</a>', t, re.S):
            title=html.unescape(re.sub(r'\s+','', re.sub(r'<[^>]+>','',inner)))
            if '金融统计数据报告' not in title: continue
            pm=period_of(title)
            if not pm: continue
            period=f'{pm[0]}-{pm[1]:02d}'
            found.setdefault(period,(abs_url(href), title)); n+=1
        print(f'  page {i+1}: +{n} reports (total {len(found)})')
        time.sleep(0.2)
    return found

def derive_monthly(records, cum_loans, cum_tsf):
    """Fill new_loans / tsf_flow (亿元, per-month) by within-year differencing of
    YTD cumulative. monthly = cum for Jan (cum==month); else cum[t]-cum[t-1], but
    ONLY when the previous captured period is the contiguous prior month/quarter-step
    (prev_month == month-1). A gap (e.g. a partially-crawled boundary year) yields
    null rather than a bogus difference."""
    by_year={}
    for r in records: by_year.setdefault(r['year'],[]).append(r)
    for yr, recs in by_year.items():
        recs.sort(key=lambda r:r['month'])
        prev_l=prev_t=None; prev_m=0
        for r in recs:
            p=r['period']; cl=cum_loans.get(p); ct=cum_tsf.get(p)
            if r['month']==1:
                r['new_loans']=cl; r['tsf_flow']=ct
            elif prev_m == r['month']-1:            # contiguous within the year
                if cl is not None and prev_l is not None:
                    r['new_loans']=round(cl-prev_l, 2)
                if ct is not None and prev_t is not None:
                    r['tsf_flow']=round(ct-prev_t, 2)
            prev_l = cl if cl is not None else prev_l
            prev_t = ct if ct is not None else prev_t
            prev_m = r['month']

def main():
    os.makedirs(DIR, exist_ok=True)
    path=os.path.join(DIR,'pboc_series.json')
    have={r['period']:r for r in (json.load(open(path)) if os.path.exists(path) else [])}
    links=collect_links()
    print(f'  {len(links)} monthly reports collected from listing')
    records=[]; cum_loans={}; cum_tsf={}; fetched=0
    for period,(url,title) in sorted(links.items()):
        cached=os.path.exists(os.path.join(RAW, period+'.htm'))
        rec, cl, ct = parse_article(period, url, title)
        if not cached: fetched+=1; time.sleep(0.4)   # be polite to avoid throttling
        records.append(rec)
        if cl is not None: cum_loans[period]=cl
        if ct is not None: cum_tsf[period]=ct
    derive_monthly(records, cum_loans, cum_tsf)
    for rec in records: have[rec['period']]=rec      # crawled overrides disk
    series=[have[p] for p in sorted(have)]
    json.dump(series, open(path,'w'), ensure_ascii=False, indent=0)
    span=f'{series[0]["period"]}..{series[-1]["period"]}' if series else '-'
    print(f'  pboc_series.json: {len(series)} months {span} (+{fetched} fetched)')

if __name__=='__main__':
    print('Fetching PBOC monetary/financing data ...'); main()
