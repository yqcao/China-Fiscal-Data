#!/usr/bin/env python3
"""Refresh the PMI series from NBS press releases.

Source: NBS 数据发布  https://www.stats.gov.cn/sj/zxfb/
Each monthly PMI release is titled e.g. "2026年5月中国采购经理指数运行情况".
We paginate the listing, collect PMI release URLs, and extract for each month:
  mfg       (制造业采购经理指数（PMI）为 XX.X%),
  nonmfg    (非制造业商务活动指数为 XX.X%),
  composite (综合PMI产出指数为 XX.X%).
Writes data/macro/pmi_series.json. Idempotent; merges with what's on disk so
history accumulates as the live listing rolls.

Note: the RatingDog/Caixin PMI is NOT published by NBS and is not covered here.
"""
import os, re, ssl, json, time, html, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'macro')
RAW  = os.path.join(DIR, 'pmi_raw')
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

def collect_links(max_pages=24):
    """Paginate the listing; return {period: (url,title)} for PMI releases.
    Crawls a fixed number of pages (PMI releases are sparse across pages, so we
    do NOT stop at the first PMI-less page — only on a fetch error / 404)."""
    found={}
    for i in range(max_pages):
        pg='index.html' if i==0 else f'index_{i}.html'
        try:
            t=get(LIST+pg)
        except Exception:
            break
        for href,inner in re.findall(r'<a\s+[^>]*href="([^"]+?\.html)"[^>]*>(.*?)</a>', t, re.S):
            title=html.unescape(re.sub(r'\s+','', re.sub(r'<[^>]+>','',inner)))
            if '采购经理指数' not in title: continue
            m=re.search(r'(\d{4})年(\d{1,2})月.*采购经理指数', title)
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
         'mfg':None, 'nonmfg':None, 'composite':None, 'title':title, 'url':url}
    os.makedirs(RAW, exist_ok=True)
    fn=os.path.join(RAW, period+'.htm')
    raw=open(fn,encoding='utf-8').read() if os.path.exists(fn) else None
    if raw is None:
        try:
            raw=get(url); open(fn,'w',encoding='utf-8').write(raw)
        except Exception as e:
            print('  fetch failed', period, e); return rec
    txt=html.unescape(re.sub(r'\s+',' ', re.sub(r'<[^>]+>',' ', raw)))
    m=re.search(r'制造业采购经理指数（PMI）为\s*([\d.]+)\s*%', txt)
    rec['mfg']=num(m.group(1)) if m else None
    m=re.search(r'非制造业商务活动指数为\s*([\d.]+)\s*%', txt)
    rec['nonmfg']=num(m.group(1)) if m else None
    m=re.search(r'综合PMI产出指数为\s*([\d.]+)\s*%', txt)
    rec['composite']=num(m.group(1)) if m else None
    return rec

def main():
    os.makedirs(DIR, exist_ok=True)
    path=os.path.join(DIR,'pmi_series.json')
    have={r['period']:r for r in (json.load(open(path)) if os.path.exists(path) else [])}
    links=collect_links()
    print(f'  {len(links)} PMI releases found on listing')
    fetched=0
    for period,(url,title) in links.items():
        if period in have and have[period].get('mfg') is not None:
            continue
        have[period]=parse_article(period,url,title); fetched+=1
    series=[have[p] for p in sorted(have)]
    json.dump(series, open(path,'w'), ensure_ascii=False, indent=0)
    span=f'{series[0]["period"]}..{series[-1]["period"]}' if series else '-'
    print(f'  pmi_series.json: {len(series)} months {span} (+{fetched} fetched)')

if __name__=='__main__':
    print('Fetching NBS PMI ...'); main()
