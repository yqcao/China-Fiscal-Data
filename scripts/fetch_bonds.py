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


def per_cn(t):
    m = re.search(r'(\d{4})年(\d{1,2})月', t); return (int(m.group(1)), int(m.group(2))) if m else None

# ---- parse the Chinese market report -> same fields as the English one ----
# The Chinese edition lands 3-4 weeks before its English translation. Parsing it
# too means a month gets its secondary-market turnover and use-of-proceeds as
# soon as the Debt Center publishes, instead of waiting for the translation.
# Chinese tables are in 亿元; the English report (and this series) use RMB bn.
CN_USE = [
 ('市政建设和产业园区基础设施', 'municipal construction and industrial park infrastructure'),
 ('交通基础设施', 'transportation infrastructure'),
 ('保障性安居工程及城市更新', 'government-subsidized housing projects and urban renewal'),
 ('保障性安居工程', 'government-subsidized housing projects'),
 ('社会事业', 'social undertaking'),
 ('农林水利', 'agriculture, forestry and water conservancy'),
 ('土地储备', 'land reserve'),
 ('生态环保', 'ecological construction and environmental protection'),
 ('城乡冷链等物流基础设施', 'infrastructure of urban and rural cold chain logistics'),
 ('仓储物流基础设施', 'infrastructure of warehouse logistics'),
 ('新型基础设施', 'new infrastructure'),
 ('新能源', 'new energy'),
 ('能源', 'energy'),
 ('收购存量商品房用作保障性住房', 'Purchase existing commercial housing for use as affordable housing'),
 ('前瞻性、战略性新兴产业基础设施', 'infrastructure for forward-looking and strategic emerging industries'),
 ('支持中小银行发展', 'supporting small and medium-sized banks development'),
 ('其他', 'others'),
]
def _sq(t):
    return re.sub(r'\s+', '', re.sub(r'-{3,}', '', t.replace('|', '')))
def _bn(v):
    return None if v is None else round(v / 10, 2)
def _f(line):
    return [float(x) for x in re.findall(r'\d[\d,]*\.\d+', line.replace(',', ''))]

def parse_cn_report(md):
    """One month's row from the Chinese 地方政府债券市场报告 markdown."""
    raw = open(md).read()
    z = _sq(raw)
    # the opening summary is monthly; a second paragraph repeats it year-to-date
    m = re.search(r'\d{1,2}[-–—]\d{1,2}月，地方政府债券发行规模', z)
    head = z[:m.start()] if m else z
    def n(pat, s):
        mm = re.search(pat, s)
        return float(mm.group(1)) if mm else None

    lines = raw.splitlines()
    try:
        a = next(i for i, l in enumerate(lines) if '地方政府债券发行额合计' in l)
        blk = lines[a:a + 16]
    except StopIteration:
        return None
    def tbl(label):
        for i, l in enumerate(blk):
            if label in l:
                f = _f(l)
                if len(f) >= 2: return f[0], f[1]
                if len(f) == 1:
                    nxt = _f(blk[i + 1]) if i + 1 < len(blk) else []
                    return f[0], (nxt[0] if nxt else None)
        return None, None
    issue_m, issue_c = tbl('地方政府债券发行额合计')
    new_m, _  = tbl('新增债券发行额小计')
    refi_m, _ = tbl('再融资债券发行额小计')
    gen_m = spec_m = None
    for i, l in enumerate(blk):
        if '地方政府债券发行额合计' in l:
            for b in blk[i + 1:i + 4]:
                f = _f(b)
                if '一般债券' in b and f: gen_m = f[0]
                if '专项债券' in b and f: spec_m = f[0]
            break
    use = []
    seg = re.search(r'新增债券资金用于(.*?)（见图', z)
    if seg:
        for part in seg.group(1).split('；'):
            mm = re.search(r'^(.*?)([\d.]+)亿元$', part)
            if not mm: continue
            cn, v = mm.group(1), float(mm.group(2))
            use.append({'field': next((en for k, en in CN_USE if k in cn), cn), 'v': round(v / 10, 2)})
    return {'issue': _bn(issue_m), 'general': _bn(gen_m), 'special': _bn(spec_m),
            'new': _bn(new_m), 'refi': _bn(refi_m),
            'rate': n(r'平均发行利率([\d.]+)%', head),
            'maturity': n(r'平均发行期限([\d.]+)年', head),
            'secondary': _bn(n(r'债券二级市场现券交易([\d.]+)亿元', head)),
            'cum_issue': _bn(issue_c), 'use': use}

def cn_rows(catalog):
    """period -> row, from every Chinese market report on disk."""
    out = {}
    for c in catalog:
        if '地方政府债券市场报告' not in c['title']: continue
        p = per_cn(c['title']); md = md_for(c)
        if not p or p[0] < 2021 or not md or not os.path.exists(md): continue
        try:
            r = parse_cn_report(md)
        except Exception:
            continue
        if not r or r['issue'] is None: continue
        r.update(year=p[0], month=p[1], period=f'{p[0]}-{p[1]:02d}', src='cn')
        out[r['period']] = r
    return out

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
    # The English translation trails the Chinese edition by 3-4 weeks. Use the
    # Chinese report for any month the translation has not reached, and to fill
    # individual fields a translated report left blank.
    cn = cn_rows(catalog)
    added = []
    for per, c in sorted(cn.items()):
        if per not in rows:
            rows[per] = c; added.append(per)
        else:
            r = rows[per]
            for k in FIELDS:
                if r.get(k) is None and c.get(k) is not None: r[k] = c[k]
            if not r.get('use') and c.get('use'): r['use'] = c['use']
    out = sorted(rows.values(), key=lambda x: (x['year'], x['month']))
    json.dump(out, open(os.path.join(DIR, 'lgb_series.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'  lgb_series.json: {len(out)} months {out[0]["period"]}..{out[-1]["period"]}')
    if added: print(f'    from the Chinese report (translation pending): {", ".join(added)}')

# ---- parse Chinese tables -> new_special_ytd.json (RMB bn) ----
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
