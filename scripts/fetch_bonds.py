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
import os, re, json, time, shutil, difflib, subprocess, urllib.request

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
MONTHS = [m.lower() for m in ('January','February','March','April','May','June',
                              'July','August','September','October','November','December')]
def month_no(name):
    """MOF's own titles carry typos ('Novbember 2023'): exact match, else nearest."""
    n = name.lower()
    if n in MONTHS: return MONTHS.index(n) + 1
    hit = difflib.get_close_matches(n, MONTHS, n=1, cutoff=0.8)
    return MONTHS.index(hit[0]) + 1 if hit else None
def per_en(t):
    """(Month, YYYY) from the title; brackets and commas may be full-width."""
    m = re.search(r'[(（]\s*([A-Za-z]+)\s*[,，]?\s*(\d{4})\s*[)）]', t)
    if not m: return None
    mo = month_no(m.group(1))
    return (int(m.group(2)), mo) if mo else None

# bounded: the boilerplate runs ~300 chars, and an unbounded .*? has swallowed
# whole paragraphs when the closing phrase only reappears much later in a report
FOOT = re.compile(r'\d?Dalianisnotincluded.{0,400}?Thefollowings?arethesame\.?\d?', re.I)
def squeeze(t):
    """The PDF->markdown step drops word spacing erratically ('bondswereRMB444.38
    billion') and a footnote can cut a sentence in half. Strip all whitespace,
    table pipes and rules, and the footnote boilerplate; match space-free below."""
    z = re.sub(r'-{3,}', '', re.sub(r'\s+', '', t.replace('|', '')))
    return FOOT.sub('', z)
def num(p, t):
    m = re.search(p, t, re.I); return float(m.group(1)) if m else None
def pair(p, t):
    m = re.search(p, t, re.I)
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)
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

FIELDS = ('issue','general','special','new','refi','rate','maturity','secondary','cum_issue')
def parse_lgb(catalog):
    rows = {}
    for c in catalog:
        if 'China Local Government Bond Market Report' not in c['title']: continue
        p = per_en(c['title']); md = md_for(c)
        if not p or not md or not os.path.exists(md): continue
        raw = open(md).read()
        t = re.sub(r'\s+', ' ', raw.replace('|', ' '))   # spaced, for use-of-proceeds
        z = squeeze(raw)                                 # space-free, for the numbers
        # Anchor each split to its own sentence: the year-to-date paragraph carries a
        # second "general/special bonds were RMB..." that used to be matched instead.
        g, s = pair(r'issuanceofgeneralbondswereRMB([\d.]+)billionandthatofspecialbondswereRMB([\d.]+)', z)
        n, f = pair(r'issuanceofnewbondswereRMB([\d.]+)billionandthatofrefinancingbondswereRMB([\d.]+)', z)
        if g is None: g = num(r'issuanceofgeneralbondswereRMB([\d.]+)', z)
        if s is None: s = num(r'specialbondswereRMB([\d.]+)', z)
        if n is None: n = num(r'newbondswereRMB([\d.]+)', z)
        if f is None: f = num(r'refinancingbondswereRMB([\d.]+)', z)
        row = {'year': p[0], 'month': p[1], 'period': f'{p[0]}-{p[1]:02d}',
            'issue': round(g + s, 2) if (g is not None and s is not None) else None,
            'general': g, 'special': s, 'new': n, 'refi': f,
            'rate': num(r'interestrateofissuedLGBswas([\d.]+)%', z),
            'maturity': num(r'maturityofissuedLGBswas([\d.]+)years', z),
            'secondary': num(r'spottransactionofLGBsinthesecondarymarketwasRMB([\d.]+)', z),
            'cum_issue': num(r'totalissuanceofLGBswereRMB([\d.]+)', z),
            'use': uses(t)}
        prev = rows.get(row['period'])                   # keep the more complete report
        if prev is None or sum(row[k] is not None for k in FIELDS) > sum(prev[k] is not None for k in FIELDS):
            rows[row['period']] = row
    out = sorted(rows.values(), key=lambda x: (x['year'], x['month']))
    json.dump(out, open(os.path.join(DIR, 'lgb_series.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'  lgb_series.json: {len(out)} months {out[0]["period"]}..{out[-1]["period"]}')

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

# ---- parse Chinese investor paragraph -> lgb_holders.json ----
# Every Chinese report carries "（二）投资者结构": one sentence splitting the LGB
# stock across markets, then one splitting the interbank share by holder type.
# All shares are of the TOTAL stock, so the buckets below sum to 100%.
HOLDER = {'商业银行': 'banks', '政策性银行': 'policy_banks', '保险机构': 'insurance',
          '非法人产品': 'products', '其他境内机构': 'other_domestic', '境外机构': 'foreign',
          '柜台市场投资者': 'counter', '其他市场投资者': 'other_market',
          '交易所市场投资者': 'other_market',            # renamed "其他市场" from 2021-03 on
          '银行间债券市场投资者': 'interbank'}            # market subtotal, not a bucket
PAIR = re.compile(r'(?:^|[；;。，,中：])([^；;。，,：]{2,12}?)持有(?:地方政府债券)?([\d,.]+)亿元[，,]?占比([\d.]+)%')
def amount(s):
    """'7,651.84' and the 2021-03 typo '7.651.84' both mean 7651.84."""
    s = s.replace(',', '')
    return float(s.replace('.', '', s.count('.') - 1)) if s.count('.') > 1 else float(s)

def table_val(z, cn):
    """Table 8 repeats the same split and outranks the sentence: MOF has twice
    mis-stated a share in the prose (2025-01 insurance, 2026-01 banks) while the
    table stayed right. Column glyphs of the vertical '银行间市场' label are
    interleaved before the row names, so anchor on the name and take two decimals."""
    j = z.find('投资者持有结构情况见')
    m = re.search(cn + r'(\d+\.\d{2})(\d+\.\d{2})', z[j:j + 1000]) if j >= 0 else None
    return (float(m.group(1)), float(m.group(2))) if m else None

def parse_holders(catalog):
    rows = {}
    for c in catalog:
        if '地方政府债券市场报告' not in c['title']: continue
        p = per_cn(c['title']); md = md_for(c)
        if not p or not md or not os.path.exists(md): continue
        z = squeeze(open(md, encoding='utf-8', errors='replace').read())
        i = z.find('银行间债券市场投资者持有地方政府债券')
        if i < 0: continue
        seg = z[i:i + 600].split('投资者持有结构情况见')[0]
        rec = {'year': p[0], 'month': p[1], 'period': f'{p[0]}-{p[1]:02d}'}
        for name, amt, pct in PAIR.findall(seg):
            k = HOLDER.get(name)
            if k: rec[k] = {'amt': amount(amt), 'pct': float(pct)}
        share = lambda: sum(v['pct'] for k, v in rec.items() if k not in ('year','month','period','interbank'))
        if abs(share() - 100) > 0.15:                    # prose disagrees with the table
            for cn, k in HOLDER.items():
                if k in rec and (tv := table_val(z, cn)):
                    if abs(tv[1] - rec[k]['pct']) > 0.05: rec[k] = {'amt': tv[0], 'pct': tv[1]}
        if len(rec) > 3: rows[(p[0], p[1])] = rec
    out = sorted(rows.values(), key=lambda x: (x['year'], x['month']))
    json.dump(out, open(os.path.join(DIR, 'lgb_holders.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    bad = [r['period'] for r in out
           if abs(sum(v['pct'] for k, v in r.items() if k not in ('year','month','period','interbank')) - 100) > 0.15]
    print(f'  lgb_holders.json: {len(out)} months {out[0]["period"]}..{out[-1]["period"]}'
          + (f'  [shares off 100% in {bad}]' if bad else ''))

if __name__ == '__main__':
    print('Fetching China Government Debt Center 地方政府债券市场报告 ...')
    fetch_listings()
    cat = download(article_urls())
    parse_lgb(cat)
    parse_nsb(cat)
    parse_holders(cat)
