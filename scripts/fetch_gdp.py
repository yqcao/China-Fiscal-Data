#!/usr/bin/env python3
"""Refresh the quarterly GDP series from NBS press releases.

Source: NBS 数据发布  https://www.stats.gov.cn/sj/zxfb/
GDP is reported QUARTERLY inside the "国民经济运行情况" releases, titled e.g.
  "2026年一季度国民经济运行情况" / "上半年" / "前三季度" / "全年" 国民经济运行情况.
We paginate the listing, collect release URLs whose title contains
  国民经济运行  OR  国内生产总值,
map the Chinese period to a quarter, and extract from the article the headline
real GDP growth:  国内生产总值 ... 同比增长X.X%  (cumulative YTD real YoY %).

Period -> quarter mapping (cumulative, year-to-date):
  一季度   -> Q1
  上半年   -> Q2   (H1 cumulative)
  前三季度 -> Q3
  全年/年度 -> Q4

Writes data/macro/gdp_series.json. Idempotent; merges with what's on disk so
history accumulates as the live listing rolls.
"""
import os, re, ssl, json, time, html, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'macro')
RAW  = os.path.join(DIR, 'gdp_raw')
LIST = 'https://www.stats.gov.cn/sj/zxfb/'
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
CTX  = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE

# Chinese period token -> quarter number
PERIOD_Q = [
    ('一季度',   1), ('第一季度', 1), ('1季度', 1),
    ('上半年',   2), ('二季度',   2), ('第二季度', 2), ('1—2季度', 2), ('1-2季度', 2),
    ('前三季度', 3), ('三季度',   3), ('第三季度', 3), ('1—3季度', 3), ('1-3季度', 3),
    ('全年',     4), ('年度',     4), ('四季度',   4), ('第四季度', 4),
]

def get(url, tries=3):
    for i in range(tries):
        try:
            req=urllib.request.Request(url, headers={'User-Agent':UA,'Referer':LIST})
            return urllib.request.urlopen(req, timeout=60, context=CTX).read().decode('utf-8','replace')
        except Exception as e:
            if i==tries-1: raise
            time.sleep(1.5*(i+1))

def quarter_from_title(title):
    """Return (quarter, matched_token) or (None, None). Longest token first so
    '前三季度' wins over '三季度', '上半年' over 'X季度' etc."""
    for tok, q in sorted(PERIOD_Q, key=lambda x:-len(x[0])):
        if tok in title:
            return q, tok
    return None, None

def parse_article(period, url, title, quarter, token):
    year=int(period[:4])
    rec={'period':period, 'year':year, 'quarter':quarter,
         'gdp_yoy':None, 'title':title, 'url':url}
    os.makedirs(RAW, exist_ok=True)
    fn=os.path.join(RAW, period+'.htm')
    raw=open(fn,encoding='utf-8').read() if os.path.exists(fn) else None
    if raw is None:
        try:
            raw=get(url); open(fn,'w',encoding='utf-8').write(raw)
        except Exception as e:
            print('  fetch failed', period, e); return rec
    txt=html.unescape(re.sub(r'\s+',' ', re.sub(r'<[^>]+>',' ', raw)))
    # (1) GDP-specific "初步核算结果" release: figure lives in Table 1, e.g.
    #     "表1 ...GDP初步核算数据 绝对额（亿元） 比上年同期增长（%） [子表头] GDP 341778 660536 5.2 5.3 第一产业 ..."
    # The GDP row lists absolute value(s) then growth rate(s); for the combined
    # Q2/Q3/Q4 releases it is [单季绝对额 累计绝对额 单季增速 累计增速] so the
    # LAST number is the cumulative YTD real YoY. For Q1 it is [绝对额 增速].
    m=re.search(r'绝对额.*?\bGDP\s+([\d.\s-]+?)第一产业', txt)
    if m:
        nums=re.findall(r'-?\d+\.?\d*', m.group(1))
        if nums:
            rec['gdp_yoy']=float(nums[-1])   # cumulative YTD real YoY
    # (2) fallback for 国民经济运行情况-style prose: 国内生产总值 ... 同比增长X.X%
    if rec['gdp_yoy'] is None:
        m=re.search(r'国内生产总值.{0,120}?同比(增长|下降|持平)\s*([\d.]+)?\s*%?', txt)
        if m:
            val=float(m.group(2)) if m.group(2) else 0.0
            rec['gdp_yoy']= -val if m.group(1)=='下降' else val
    if rec['gdp_yoy'] is None:
        print('  no GDP figure parsed for', period, '-', title)
    return rec

def collect_links(max_pages=int(os.environ.get("MACRO_MAX_PAGES","24"))):
    """Paginate the listing; return {period: (url,title,quarter,token)} for GDP
    releases. GDP releases are quarterly and sparse across pages, so we do NOT
    stop at the first GDP-less page — only on a fetch error / 404."""
    found={}
    for i in range(max_pages):
        pg='index.html' if i==0 else f'index_{i}.html'
        try:
            t=get(LIST+pg)
        except Exception:
            break
        for href,inner in re.findall(r'<a\s+[^>]*href="([^"]+?\.html)"[^>]*>(.*?)</a>', t, re.S):
            title=html.unescape(re.sub(r'\s+','', re.sub(r'<[^>]+>','',inner)))
            if ('国民经济运行' not in title) and ('国内生产总值' not in title):
                continue
            ym=re.search(r'(\d{4})年', title)
            if not ym: continue
            year=int(ym.group(1))
            q,tok=quarter_from_title(title)
            if q is None:
                print('  ambiguous quarter (skipped):', title)
                continue
            period=f'{year}-Q{q}'
            if href.startswith('http'): url=href
            elif href.startswith('./'): url=LIST+href[2:]
            elif href.startswith('/'): url='https://www.stats.gov.cn'+href
            else: url=LIST+href
            found.setdefault(period,(url,title,q,tok))
        time.sleep(0.2)
    return found

def main():
    os.makedirs(DIR, exist_ok=True)
    path=os.path.join(DIR,'gdp_series.json')
    have={r['period']:r for r in (json.load(open(path)) if os.path.exists(path) else [])}
    links=collect_links()
    print(f'  {len(links)} GDP releases found on listing')
    fetched=0
    for period,(url,title,q,tok) in links.items():
        if period in have and have[period].get('gdp_yoy') is not None:
            continue
        have[period]=parse_article(period,url,title,q,tok); fetched+=1
    series=[have[p] for p in sorted(have)]
    json.dump(series, open(path,'w'), ensure_ascii=False, indent=0)
    span=f'{series[0]["period"]}..{series[-1]["period"]}' if series else '-'
    print(f'  gdp_series.json: {len(series)} quarters {span} (+{fetched} fetched)')

if __name__=='__main__':
    print('Fetching NBS GDP ...'); main()
