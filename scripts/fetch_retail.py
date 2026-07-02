#!/usr/bin/env python3
"""Refresh the retail-sales series from NBS press releases.

Source: NBS 数据发布  https://www.stats.gov.cn/sj/zxfb/
Each monthly retail release is titled e.g. "2026年5月份社会消费品零售总额增长X.X%"
(Jan/Feb are combined: "2026年1—2月份社会消费品零售总额增长X.X%").
We paginate the listing, collect retail release URLs, and extract for each month:
  yoy  (社会消费品零售总额 同比, %, single-month),
  ytd  (1—M月份 社会消费品零售总额 同比, %, cumulative).
Writes data/macro/retail_series.json. Idempotent; merges with what's on disk so
history accumulates as the live listing rolls.
"""
import os, re, ssl, json, time, html, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'macro')
RAW  = os.path.join(DIR, 'retail_raw')
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

def collect_links(max_pages=int(os.environ.get("MACRO_MAX_PAGES","24"))):
    """Paginate the listing; return {period: (url,title)} for retail releases.
    Crawls a fixed number of pages (retail releases are sparse across pages, so we
    do NOT stop at the first retail-less page — only on a fetch error / 404)."""
    found={}
    for i in range(max_pages):
        pg='index.html' if i==0 else f'index_{i}.html'
        try:
            t=get(LIST+pg)
        except Exception:
            break
        for href,inner in re.findall(r'<a\s+[^>]*href="([^"]+?\.html)"[^>]*>(.*?)</a>', t, re.S):
            title=html.unescape(re.sub(r'\s+','', re.sub(r'<[^>]+>','',inner)))
            # year + ending month (Jan/Feb combined releases carry a "1—2月" range)
            m=re.search(r'(\d{4})年(?:\d{1,2}[—\-－~至])?(\d{1,2})月份?社会消费品零售总额', title)
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
         'yoy':None, 'ytd':None, 'title':title, 'url':url}
    # fetch (or reuse cached) article
    os.makedirs(RAW, exist_ok=True)
    fn=os.path.join(RAW, period+'.htm')
    raw=open(fn,encoding='utf-8').read() if os.path.exists(fn) else None
    if raw is None:
        try:
            raw=get(url); open(fn,'w',encoding='utf-8').write(raw)
        except Exception as e:
            print('  fetch failed', period, e); return rec
    txt=html.unescape(re.sub(r'\s+',' ', re.sub(r'<[^>]+>',' ', raw)))
    # each "<month-token>月份，社会消费品零售总额<金额>亿元，[同比](增长|下降|持平)X.X%".
    # Tokens with a dash ("1—9月") are cumulative (YTD); bare tokens the single
    # month. The month figure carries 同比; the cumulative one often drops it, so
    # 同比 is optional. NBS whitespace is irregular, hence the \s* padding.
    pat=(r'((?:\d{1,2}\s*[—\-－~至]\s*)?\d{1,2})\s*月份[，,]?\s*社会消费品零售总额'
         r'[^。]{0,30}?(?:同比)?\s*(增长|下降|持平)\s*([\d.]+)')
    for tok,d,v in re.findall(pat, txt):
        val=signed(d,v)
        if re.search(r'[—\-－~至]', tok):
            if rec['ytd'] is None: rec['ytd']=val
        else:
            if rec['yoy'] is None: rec['yoy']=val
    # December releases report the full year as "YYYY年，社会消费品零售总额…比上年增长X.X%"
    # (not "1—12月份"); that annual figure is the year-to-date value.
    if rec['month']==12 and rec['ytd'] is None:
        m=re.search(r'\d{4}\s*年[，,]\s*社会消费品零售总额[^。]{0,30}?(?:比上年|同比)?\s*(增长|下降|持平)\s*([\d.]+)', txt)
        if m: rec['ytd']=signed(m.group(1), m.group(2))
    # fallbacks from the title if the body pattern missed a field
    m=re.search(r'社会消费品零售总额(?:同比)?\s*(增长|下降|持平)\s*([\d.]+)', title)
    if m:
        val=signed(m.group(1), m.group(2))
        cumulative=bool(re.search(r'\d{1,2}\s*[—\-－~至]\s*\d{1,2}月', title))
        if cumulative and rec['ytd'] is None: rec['ytd']=val
        elif not cumulative and rec['yoy'] is None: rec['yoy']=val
    return rec

def main():
    os.makedirs(DIR, exist_ok=True)
    path=os.path.join(DIR,'retail_series.json')
    have={r['period']:r for r in (json.load(open(path)) if os.path.exists(path) else [])}
    links=collect_links()
    print(f'  {len(links)} retail releases found on listing')
    fetched=0
    for period,(url,title) in links.items():
        if period in have and have[period].get('ytd') is not None:
            continue
        have[period]=parse_article(period,url,title); fetched+=1
    series=[have[p] for p in sorted(have)]
    json.dump(series, open(path,'w'), ensure_ascii=False, indent=0)
    span=f'{series[0]["period"]}..{series[-1]["period"]}' if series else '-'
    print(f'  retail_series.json: {len(series)} months {span} (+{fetched} fetched)')

if __name__=='__main__':
    print('Fetching NBS retail sales ...'); main()
