#!/usr/bin/env python3
"""Refresh the General Public Budget / Government Fund series.

Source: MOF 全国财政收支情况
  https://www.mof.gov.cn/zhengwuxinxi/redianzhuanti/quanguocaizhengshouzhiqingkuang/

Re-downloads the listing pages, fetches any new monthly report (skips ones
already on disk), extracts clean text, and regenerates data/mof-reports/
fiscal_series.json (2021+). Idempotent — safe to run monthly.
"""
import os, re, html, time, json, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'mof-reports')
LIST = 'https://www.mof.gov.cn/zhengwuxinxi/redianzhuanti/quanguocaizhengshouzhiqingkuang'
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')

def fetch_listings():
    os.makedirs(os.path.join(DIR, 'listing'), exist_ok=True)
    first = get(LIST + '/index.html')
    open(os.path.join(DIR, 'listing', 'index.html'), 'w', encoding='utf-8').write(first)
    n = int(re.search(r'countPage\s*=\s*(\d+)', first).group(1))
    print(f'  {n} listing pages')
    for i in range(1, n):
        try:
            t = get(f'{LIST}/index_{i}.html')
            open(os.path.join(DIR, 'listing', f'index_{i}.html'), 'w', encoding='utf-8').write(t)
            time.sleep(0.2)
        except Exception as e:
            print('  listing', i, 'failed:', e)

def article_urls():
    # merge with the existing record: the live listing rolls (old reports scroll
    # off), so never drop URLs we have already archived.
    path = os.path.join(DIR, 'article_urls.txt')
    urls = open(path).read().split() if os.path.exists(path) else []
    seen = set(urls)
    for f in sorted(os.listdir(os.path.join(DIR, 'listing'))):
        t = open(os.path.join(DIR, 'listing', f), encoding='utf-8', errors='replace').read()
        for u in re.findall(r'href="(https?://gks\.mof\.gov\.cn/tongjishuju/[^"]+\.htm)"', t):
            if u not in seen:
                seen.add(u); urls.append(u)
    open(path, 'w').write('\n'.join(urls) + '\n')
    return urls

def inner_div(t, cls):
    m = re.search(r'<div[^>]*class="[^"]*\b' + re.escape(cls) + r'\b[^"]*"[^>]*>', t)
    if not m: return None
    i = m.end(); depth = 1; pos = i
    for mm in re.finditer(r'<(/?)div\b[^>]*>', t[i:]):
        depth += -1 if mm.group(1) else 1
        if depth == 0: pos = i + mm.start(); break
    return t[i:pos]

def to_text(frag):
    frag = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', frag, flags=re.S | re.I)
    frag = re.sub(r'<br\s*/?>', '\n', frag, flags=re.I)
    frag = re.sub(r'</(p|div|tr|table|li|h[1-6])>', '\n', frag, flags=re.I)
    txt = html.unescape(re.sub(r'<[^>]+>', '', frag))
    return '\n'.join(l.strip() for l in txt.splitlines() if l.strip())

def download_and_extract(urls):
    os.makedirs(os.path.join(DIR, 'raw'), exist_ok=True)
    os.makedirs(os.path.join(DIR, 'text'), exist_ok=True)
    new = 0
    for url in urls:
        name = url.rsplit('/', 1)[-1]                 # tYYYYMMDD_id.htm
        raw = os.path.join(DIR, 'raw', name)
        if not os.path.exists(raw):
            try:
                open(raw, 'w', encoding='utf-8').write(get(url)); time.sleep(0.3); new += 1
            except Exception as e:
                print('  fetch failed', url, e); continue
        t = open(raw, encoding='utf-8', errors='replace').read()
        mt = re.search(r'<title>(.*?)</title>', t, re.S)
        title = html.unescape(re.sub(r'<[^>]+>', '', mt.group(1))).strip() if mt else name
        frag = inner_div(t, 'my_doccontent')
        body = to_text(frag) if frag else ''
        if len(body) < 60:
            b2 = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S | re.I)
            ps = [html.unescape(re.sub(r'<[^>]+>', '', p)).strip() for p in re.findall(r'<p\b[^>]*>(.*?)</p>', b2, re.S)]
            body = '\n'.join(p for p in ps if len(p) >= 12)
        open(os.path.join(DIR, 'text', name.replace('.htm', '.txt')), 'w', encoding='utf-8').write(title + '\n\n' + body)
    print(f'  {new} new reports downloaded')

# ---- parsing into fiscal_series.json ----
TAX = [('国内增值税', r'国内增值税'), ('国内消费税', r'国内消费税'), ('企业所得税', r'企业所得税'),
       ('个人所得税', r'个人所得税'), ('进口货物增值税、消费税', r'进口货物增值税、?消费税'), ('关税', r'关税'),
       ('出口退税', r'出口(?:货物退增值税、?消费税|退税)'), ('城市维护建设税', r'城市维护建设税'),
       ('车辆购置税', r'车辆购置税'), ('印花税', r'印花税'), ('资源税', r'资源税'), ('契税', r'契税'),
       ('房产税', r'房产税'), ('城镇土地使用税', r'城镇土地使用税'), ('土地增值税', r'土地增值税'),
       ('耕地占用税', r'耕地占用税'), ('环境保护税', r'环境保护税'),
       ('其他税收', r'(?:车船税[^。]*?合计|其他各项税收收入合?计?)')]
EXP = [('教育支出', r'教育支出'), ('科学技术支出', r'科学技术支出'), ('文化旅游体育与传媒支出', r'文化[^。，]*?传媒支出'),
       ('社会保障和就业支出', r'社会保障和就业支出'), ('卫生健康支出', r'(?:卫生健康|医疗卫生)支出'),
       ('节能环保支出', r'节能环保支出'), ('城乡社区支出', r'城乡社区支出'), ('农林水支出', r'农林水支出'),
       ('交通运输支出', r'交通运输支出'), ('债务付息支出', r'债务付息支出')]

def period(title, fdate):
    y = re.search(r'(\d{4})年', title); year = int(y.group(1)) if y else int(fdate[:4])
    m = re.search(r'1[-—](\d{1,2})月', title)
    if m: return year, int(m.group(1))
    if '一季度' in title: return year, 3
    if '上半年' in title: return year, 6
    if '前三季度' in title: return year, 9
    if re.search(r'\d{4}年财政收支情况', title): return year, 12
    mm = re.search(r'(\d{1,2})月', title)
    return (year, int(mm.group(1))) if mm else (year, 12)

def gval(s):
    m = re.search(r'(增长|下降)\s*([\d.]+)\s*%', s)
    return (float(m.group(2)) if m.group(1) == '增长' else -float(m.group(2))) if m else None

def metric(t, kw):
    m = re.search(kw + r'\s*([\d.]+)\s*亿元([^。]*)', t)
    return {'v': float(m.group(1)), 'g': gval(m.group(2))} if m else None

def items(t, cats):
    out = []
    for cn, kw in cats:
        mt = metric(t, kw)
        if mt: out.append({'name': cn, 'v': mt['v'], 'g': mt['g']})
    return out

def parse():
    rows = []
    for f in sorted(os.listdir(os.path.join(DIR, 'text'))):
        t = open(os.path.join(DIR, 'text', f), encoding='utf-8').read().replace('—', '-')
        fd = re.search(r't(\d{8})_', f).group(1); title = t.split('\n', 1)[0]
        yr, mo = period(title, fd)
        if yr < 2021: continue
        ei = t.find('一般公共预算支出'); fi = t.find('政府性基金')
        gen_rev = t[:ei]; gen_exp = t[ei:fi if fi > 0 else len(t)]
        rows.append({'date': fd, 'year': yr, 'month': mo, 'period': f'{yr}-{mo:02d}', 'title': title,
            'pub_rev': metric(t, r'全国一般公共预算收入'), 'tax': metric(t, r'全国税收收入') or metric(t, r'税收收入'),
            'nontax': metric(t, r'非税收入'), 'pub_rev_central': metric(t, r'中央一般公共预算收入'),
            'pub_rev_local': metric(t, r'地方一般公共预算本级收入'), 'pub_exp': metric(t, r'全国一般公共预算支出'),
            'pub_exp_central': metric(t, r'中央一般公共预算本级支出'), 'pub_exp_local': metric(t, r'地方一般公共预算支出'),
            'fund_rev': metric(t, r'全国政府性基金预算收入'), 'land_rev': metric(t, r'国有土地使用权出让收入'),
            'fund_exp': metric(t, r'全国政府性基金预算支出'),
            'tax_items': items(gen_rev, TAX), 'exp_items': items(gen_exp, EXP)})
    rows.sort(key=lambda r: (r['year'], r['month']))
    json.dump(rows, open(os.path.join(DIR, 'fiscal_series.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'  fiscal_series.json: {len(rows)} reports {rows[0]["period"]}..{rows[-1]["period"]}')

if __name__ == '__main__':
    print('Fetching MOF 全国财政收支情况 ...')
    fetch_listings()
    download_and_extract(article_urls())
    parse()
