#!/usr/bin/env python3
"""Refresh the fixed-asset-investment (FAI) series from NBS press releases.

Source: NBS 数据发布  https://www.stats.gov.cn/sj/zxfb/
Each release is titled e.g. "2026年1—5月份全国固定资产投资(不含农户)增长X.X%".
FAI is reported YTD (cumulative) only. We paginate the listing, collect FAI
release URLs, and extract for each month:
  ytd_yoy        (固定资产投资(不含农户) 同比, %, cumulative),
  realestate_yoy (房地产开发投资 同比, %, cumulative; optional).
Writes data/macro/fai_series.json. Idempotent; merges with what's on disk so
history accumulates as the live listing rolls.
"""
import os, re, ssl, json, time, html, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'macro')
RAW  = os.path.join(DIR, 'fai_raw')
LIST = 'https://www.stats.gov.cn/sj/zxfb/'
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
CTX  = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE

def get(url, tries=3):
    for i in range(tries):
        try:
            req=urllib.request.Request(url, headers={'User-Agent':UA,'Referer':LIST})
            return urllib.request.urlopen(req, timeout=60, context=CTX).read().decode('utf-8','replace')
        except Exception as e:
            if i==tries-1: raise
            time.sleep(1.5*(i+1))

def num(s):
    return float(s) if s not in (None,'') else None

def signed(direction, val):
    v=num(val)
    if v is None: return 0.0 if direction=='持平' else None
    return -v if direction=='下降' else v

def collect_links(max_pages=24):
    """Paginate the listing; return {period: (url,title)} for FAI releases.
    Crawls a fixed number of pages (FAI releases are sparse across pages, so we
    do NOT stop at the first FAI-less page — only on a fetch error / 404)."""
    found={}
    for i in range(max_pages):
        pg='index.html' if i==0 else f'index_{i}.html'
        try:
            t=get(LIST+pg)
        except Exception:
            break
        for href,inner in re.findall(r'<a\s+[^>]*href="([^"]+?\.html)"[^>]*>(.*?)</a>', t, re.S):
            title=html.unescape(re.sub(r'\s+','', re.sub(r'<[^>]+>','',inner)))
            if '固定资产投资' not in title: continue
            # cumulative window "1—M月份"; fall back to a single ending month
            m=re.search(r'(\d{4})年(?:\d{1,2}[—\-－~至])?(\d{1,2})月份?', title)
            if not m: continue
            period=f'{m.group(1)}-{int(m.group(2)):02d}'
            if href.startswith('http'): url=href
            elif href.startswith('./'): url=LIST+href[2:]
            elif href.startswith('/'): url='https://www.stats.gov.cn'+href
            else: url=LIST+href
            found.setdefault(period,(url,title))
        time.sleep(0.2)
    return found

def parse_article(period, url, title):
    rec={'period':period, 'year':int(period[:4]), 'month':int(period[5:]),
         'ytd_yoy':None, 'realestate_yoy':None, 'title':title, 'url':url}
    os.makedirs(RAW, exist_ok=True)
    fn=os.path.join(RAW, period+'.htm')
    raw=open(fn,encoding='utf-8').read() if os.path.exists(fn) else None
    if raw is None:
        try:
            raw=get(url); open(fn,'w',encoding='utf-8').write(raw)
        except Exception as e:
            print('  fetch failed', period, e); return rec
    txt=html.unescape(re.sub(r'\s+',' ', re.sub(r'<[^>]+>',' ', raw)))
    # FAI YTD YoY — "固定资产投资(不含农户) ... 同比(增长|下降|持平)X.X%"
    m=re.search(r'固定资产投资[^。]{0,60}?同比(增长|下降|持平)\s*([\d.]*)', txt)
    rec['ytd_yoy']=signed(m.group(1), m.group(2)) if m else None
    if rec['ytd_yoy'] is None:  # fall back to the title figure
        m=re.search(r'固定资产投资[^增下持]*?(?:同比)?(增长|下降|持平)\s*([\d.]*)', title)
        rec['ytd_yoy']=signed(m.group(1), m.group(2)) if m else None
    # real-estate development investment YTD YoY (optional)
    m=re.search(r'房地产开发投资[^。]{0,60}?同比(增长|下降|持平)\s*([\d.]*)', txt)
    rec['realestate_yoy']=signed(m.group(1), m.group(2)) if m else None
    return rec

def main():
    os.makedirs(DIR, exist_ok=True)
    path=os.path.join(DIR,'fai_series.json')
    have={r['period']:r for r in (json.load(open(path)) if os.path.exists(path) else [])}
    links=collect_links()
    print(f'  {len(links)} FAI releases found on listing')
    fetched=0
    for period,(url,title) in links.items():
        if period in have and have[period].get('ytd_yoy') is not None:
            continue
        have[period]=parse_article(period,url,title); fetched+=1
    series=[have[p] for p in sorted(have)]
    json.dump(series, open(path,'w'), ensure_ascii=False, indent=0)
    span=f'{series[0]["period"]}..{series[-1]["period"]}' if series else '-'
    print(f'  fai_series.json: {len(series)} months {span} (+{fetched} fetched)')

if __name__=='__main__':
    print('Fetching NBS fixed-asset investment ...'); main()
