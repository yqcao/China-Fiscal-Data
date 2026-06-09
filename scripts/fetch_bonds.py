#!/usr/bin/env python3
"""Refresh the Local Government Bond series.

Source: China Government Debt Center 地方政府债券市场报告
  https://kjhx.mof.gov.cn/yjbg/

Downloads new monthly reports + their PDF/docx attachments, converts new
attachments to markdown via `markitdown`, then regenerates:
  data/mof-research-reports/lgb_series.json        (English reports: issuance,
        new/refi, rate, maturity, secondary turnover, use-of-proceeds)
  data/mof-research-reports/new_special_ytd.json   (Chinese tables: YTD new
        special-bond issuance, RMB bn, 2021+)
Idempotent. Needs markitdown:  uv tool install 'markitdown[pdf,docx]'
"""
import os, re, json, time, shutil, subprocess, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'mof-research-reports')
LIST = 'https://kjhx.mof.gov.cn/yjbg'
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
MD   = shutil.which('markitdown') or os.path.expanduser('~/.local/bin/markitdown')

def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    d = urllib.request.urlopen(req, timeout=120).read()
    return d if binary else d.decode('utf-8', 'replace')

def fetch_listings():
    os.makedirs(os.path.join(DIR, 'listing'), exist_ok=True)
    first = get(LIST + '/index.htm')
    open(os.path.join(DIR, 'listing', 'index.htm'), 'w', encoding='utf-8').write(first)
    n = int(re.search(r'countPage\s*=\s*(\d+)', first).group(1))
    print(f'  {n} listing pages')
    for i in range(1, n):
        try:
            open(os.path.join(DIR, 'listing', f'index_{i}.htm'), 'w', encoding='utf-8').write(get(f'{LIST}/index_{i}.htm'))
            time.sleep(0.2)
        except Exception as e:
            print('  listing', i, 'failed:', e)

def article_urls():
    # merge with existing record (live listing rolls over time)
    path = os.path.join(DIR, 'article_urls.txt')
    order = open(path).read().split() if os.path.exists(path) else []
    seen = set(order)
    for f in sorted(os.listdir(os.path.join(DIR, 'listing'))):
        t = open(os.path.join(DIR, 'listing', f), encoding='utf-8', errors='replace').read()
        for rel in re.findall(r'href="\.?/?(\d{6}/t\d{8}_\d+\.htm)"', t):
            u = LIST + '/' + rel
            if u not in seen: seen.add(u); order.append(u)
    open(path, 'w').write('\n'.join(order) + '\n')
    return order

def download(urls):
    for d in ('raw', 'files', 'markdown'):
        os.makedirs(os.path.join(DIR, d), exist_ok=True)
    new_art = new_file = new_md = 0
    catalog = []
    for url in urls:
        month = re.search(r'/(\d{6})/', url).group(1); base = month + '_' + url.rsplit('/', 1)[-1]
        raw = os.path.join(DIR, 'raw', base)
        if not os.path.exists(raw):
            try:
                open(raw, 'w', encoding='utf-8').write(get(url)); time.sleep(0.25); new_art += 1
            except Exception as e:
                print('  article failed', url, e); continue
        t = open(raw, encoding='utf-8', errors='replace').read()
        title = re.search(r'<title>(.*?)</title>', t, re.S)
        title = re.sub(r'<[^>]+>', '', title.group(1)).strip() if title else base
        pub = re.search(r'发布日期：\s*(\d{4})年(\d{1,2})月(\d{1,2})日', t)
        date = f'{pub.group(1)}-{int(pub.group(2)):02d}-{int(pub.group(3)):02d}' if pub else ''
        atts = list(dict.fromkeys(re.findall(r'href="\.?/?(?:' + month + r'/)?(W\d+\.[A-Za-z0-9]+)"', t)))
        f0 = ('files/' + month + '_' + atts[0]) if atts else ''
        kb = round(os.path.getsize(os.path.join(DIR, f0)) / 1024) if f0 and os.path.exists(os.path.join(DIR, f0)) else 0
        catalog.append({'date': date, 'title': title, 'article': base, 'month': month, 'attachments': atts, 'file': f0, 'kb': kb})
        for fn in atts:
            local = os.path.join(DIR, 'files', month + '_' + fn)
            if not os.path.exists(local):
                try:
                    open(local, 'wb').write(get(f'{LIST}/{month}/{fn}', binary=True)); time.sleep(0.25); new_file += 1
                except Exception as e:
                    print('  attach failed', fn, e); continue
            md = os.path.join(DIR, 'markdown', (month + '_' + fn).rsplit('.', 1)[0] + '.md')
            if not os.path.exists(md):
                try:
                    subprocess.run([MD, local, '-o', md], check=True, capture_output=True); new_md += 1
                except Exception as e:
                    print('  markitdown failed', fn, e)
    catalog.sort(key=lambda c: c['date'], reverse=True)
    json.dump(catalog, open(os.path.join(DIR, 'catalog.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'  new: {new_art} articles, {new_file} attachments, {new_md} markdown')
    return catalog

# ---- parse English reports -> lgb_series.json ----
MONTHS = {m: i + 1 for i, m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'])}
def per_en(t):
    m = re.search(r'\(([A-Za-z]+)\s*,?\s*(\d{4})\)', t)
    return (int(m.group(2)), MONTHS.get(m.group(1))) if m and MONTHS.get(m.group(1)) else None
def num(p, t):
    m = re.search(p, t, re.I); return float(m.group(1)) if m else None
def uses(t):
    seg = re.search(r'investment target.*?fields?:(.*?)(?:In terms of region|Figure|Note:|In terms of maturity)', t, re.I)
    if not seg: return []
    out = []
    for m in re.finditer(r'([A-Za-z][A-Za-z ,/&\-]+?)\s*\(\s*RMB\s*([\d.]+)\s*billion\s*\)', seg.group(1)):
        out.append({'field': re.sub(r'\s+', ' ', re.sub(r'^[,\s]+', '', m.group(1))).strip(), 'v': float(m.group(2))})
    return out

def md_for(c):
    """markdown file is named after the attachment (W-file), not the article."""
    if not c['attachments']: return None
    return os.path.join(DIR, 'markdown', c['month'] + '_' + c['attachments'][0].rsplit('.', 1)[0] + '.md')

def parse_lgb(catalog):
    rows = []
    for c in catalog:
        if 'China Local Government Bond Market Report' not in c['title']: continue
        p = per_en(c['title']); md = md_for(c)
        if not p or not md or not os.path.exists(md): continue
        t = re.sub(r'\s+', ' ', open(md).read().replace('|', ' '))
        g = num(r'issuance of general bonds?\s*were\s*RMB\s*([\d.]+)', t)
        s = num(r'special bonds?\s*were\s*RMB\s*([\d.]+)', t)
        rows.append({'year': p[0], 'month': p[1], 'period': f'{p[0]}-{p[1]:02d}',
            'issue': round((g or 0) + (s or 0), 2) if (g is not None and s is not None) else None,
            'general': g, 'special': s,
            'new': num(r'new bonds?\s*were\s*RMB\s*([\d.]+)', t),
            'refi': num(r'refinancing bonds?\s*were\s*RMB\s*([\d.]+)', t),
            'rate': num(r'interest rate of issued LGBs\s*was\s*([\d.]+)\s*%', t),
            'maturity': num(r'maturity of issued LGBs\s*was\s*([\d.]+)\s*years', t),
            'secondary': num(r'spot transaction of LGBs in the\s*secondary market\s*was\s*RMB\s*([\d.]+)', t),
            'cum_issue': num(r'total issuance of LGBs\s*were\s*RMB\s*([\d.]+)', t),
            'use': uses(t)})
    rows.sort(key=lambda x: (x['year'], x['month']))
    json.dump(rows, open(os.path.join(DIR, 'lgb_series.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'  lgb_series.json: {len(rows)} months {rows[0]["period"]}..{rows[-1]["period"]}')

# ---- parse Chinese tables -> new_special_ytd.json (RMB bn) ----
def per_cn(t):
    m = re.search(r'(\d{4})年(\d{1,2})月', t); return (int(m.group(1)), int(m.group(2))) if m else None
def floats(s): return [float(x) for x in re.findall(r'\d+\.\d+', s)]

def parse_nsb(catalog):
    rows = {}
    for c in catalog:
        if '地方政府债券市场报告' not in c['title']: continue
        p = per_cn(c['title']); md = md_for(c)
        if not p or p[0] < 2021 or not md or not os.path.exists(md): continue
        lines = open(md).read().splitlines()
        for i, l in enumerate(lines):
            if '新增债券发行额小计' in l:
                for b in lines[i:i + 4]:
                    if '专项债券' in b:
                        f = floats(b)
                        if len(f) >= 2: rows[p] = {'year': p[0], 'month': p[1], 'ytd': round(f[-1] / 10, 2)}
                        break
                break
    out = sorted(rows.values(), key=lambda x: (x['year'], x['month']))
    json.dump(out, open(os.path.join(DIR, 'new_special_ytd.json'), 'w'), separators=(',', ':'))
    print(f'  new_special_ytd.json: {len(out)} months')

if __name__ == '__main__':
    print('Fetching China Government Debt Center 地方政府债券市场报告 ...')
    fetch_listings()
    cat = download(article_urls())
    parse_lgb(cat)
    parse_nsb(cat)
