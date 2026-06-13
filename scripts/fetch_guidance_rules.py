#!/usr/bin/env python3
"""Collect local 政府投资基金/引导基金「管理办法」 documents.

For any region the single richest first-party document is its guidance-fund
管理办法 (structure, target size, investment direction, decision/exit rules).
These live on each 财政厅(局) / government portal in a different place, so this
crawler is **config-driven**: you list source pages in
data/govt-guidance-funds/rules/sources.json and extend it province by province
(the automated form of the SOURCES.md "collection recipe").

Each source is either:
  {"region": "...", "type": "listing", "url": "<column/index page>"}
  {"region": "...", "type": "search",  "url": "<site-search URL with {kw}[&{page}]>"}

From each page the crawler keeps links whose anchor text names a guidance fund
AND looks like a rule (办法/规定/细则…) or is a document attachment, opens those
articles, and downloads any PDF/DOC attachments. Writes into
data/govt-guidance-funds/rules/:
  raw/         cached article HTML
  files/       downloaded attachments        (LOCAL ONLY — gitignored, re-downloadable)
  markdown/    markitdown conversions          (committed, for searchability; optional)
  catalog.json per-document: region, title, date, article, attachments, local files
  INDEX.md     human-readable, region-sorted table

Idempotent / incremental: skips articles and attachments already on disk.

NETWORK: needs outbound access to each source host. In Claude Code web sessions
the egress allowlist may block them — run locally where outbound access is open.
markitdown is optional:  uv tool install 'markitdown[pdf,docx]'

Usage:
  python3 scripts/fetch_guidance_rules.py
"""
import os, re, html, json, time, shutil, subprocess, urllib.request
from urllib.parse import urljoin, urlparse, quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'govt-guidance-funds', 'rules')
SRC  = os.path.join(DIR, 'sources.json')
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
MD   = shutil.which('markitdown') or os.path.expanduser('~/.local/bin/markitdown')
DELAY = 0.4

# Anchor must name a guidance fund …
FUND_KW = ['引导基金', '政府投资基金', '政府引导', '产业引导', '创业投资引导',
           '创投引导', '产业投资基金', '政府出资']
# … and look like a rule document (or be an attachment, handled separately).
RULE_KW = ['办法', '规定', '细则', '规程', '指引', '暂行', '通知', '意见']
ATT_EXT = ('.pdf', '.doc', '.docx', '.wps', '.xls', '.xlsx', '.et', '.ofd')

# Search keywords expanded into {kw} for type=search sources.
SEARCH_KW = ['政府投资基金 管理办法', '政府引导基金 管理办法', '产业引导基金 管理办法']

SEED = {
    "_how_to_extend": "Add objects to \"sources\". type=listing: a column/index page "
                      "to scan. type=search: a site-search results URL with {kw} (and "
                      "optional {page}). Verify each URL in a browser first, then run "
                      "python3 scripts/fetch_guidance_rules.py. Examples below are "
                      "STARTER TEMPLATES — confirm/replace them for your target regions.",
    "sources": [
        {"region": "中央·财政部", "type": "listing",
         "url": "https://www.mof.gov.cn/gkml/", "note": "MOF 公开目录；按关键词过滤"},
        {"region": "示例·省财政厅检索", "type": "search",
         "url": "https://example.gov.cn/search?q={kw}&page={page}",
         "note": "把 host/路径换成目标省份财政厅站内搜索接口"}
    ]
}


def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    d = urllib.request.urlopen(req, timeout=90).read()
    return d if binary else d.decode('utf-8', 'replace')


def load_sources():
    if not os.path.exists(SRC):
        os.makedirs(DIR, exist_ok=True)
        json.dump(SEED, open(SRC, 'w'), ensure_ascii=False, indent=2)
        print(f'  wrote starter {SRC} — edit it with real source pages, then re-run')
    return json.load(open(SRC, encoding='utf-8')).get('sources', [])


def anchors(page, base):
    """Return [(abs_url, text)] for every <a href> on the page."""
    out = []
    for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.S | re.I):
        href = m.group(1).strip()
        if not href or href.startswith(('#', 'javascript:', 'mailto:')):
            continue
        text = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
        out.append((urljoin(base, href), text))
    return out


def is_attachment(url):
    return urlparse(url).path.lower().endswith(ATT_EXT)


def candidate(url, text):
    fund = any(k in text for k in FUND_KW)
    if not fund:
        return False
    return is_attachment(url) or any(k in text for k in RULE_KW)


def page_urls(source):
    url = source['url']
    if source.get('type') == 'search':
        for kw in SEARCH_KW:
            for p in range(int(source.get('pages', 1))):
                yield url.replace('{kw}', quote(kw)).replace('{page}', str(p))
    else:
        yield url
        # gov listings often paginate as index_1.html …; honour an explicit count
        for i in range(1, int(source.get('pages', 1))):
            yield re.sub(r'(index)(\.\w+)$', rf'\g<1>_{i}\g<2>', url)


def article_meta(t, fallback):
    mt = re.search(r'<title>(.*?)</title>', t, re.S)
    title = html.unescape(re.sub(r'<[^>]+>', '', mt.group(1))).strip() if mt else fallback
    md = re.search(r'(20\d{2})[-/年.](\d{1,2})[-/月.](\d{1,2})', t)
    date = f'{md.group(1)}-{int(md.group(2)):02d}-{int(md.group(3)):02d}' if md else ''
    return title, date


def safe(name):
    return re.sub(r'[^\w.\-]+', '_', name)[:120]


def to_md(local, region):
    if not os.path.exists(MD):
        return None
    md = os.path.join(DIR, 'markdown', safe(region) + '_' + os.path.basename(local).rsplit('.', 1)[0] + '.md')
    if not os.path.exists(md):
        try:
            subprocess.run([MD, local, '-o', md], check=True, capture_output=True)
        except Exception as e:
            print('  markitdown failed', local, e); return None
    return os.path.relpath(md, DIR)


def crawl():
    for d in ('raw', 'files', 'markdown'):
        os.makedirs(os.path.join(DIR, d), exist_ok=True)
    catalog = {c['article']: c for c in (json.load(open(os.path.join(DIR, 'catalog.json'), encoding='utf-8'))
                                         if os.path.exists(os.path.join(DIR, 'catalog.json')) else [])}
    new_art = new_file = 0
    for source in load_sources():
        region = source.get('region', '?')
        found = []
        for purl in page_urls(source):
            try:
                page = get(purl)
            except Exception as e:
                print(f'  [{region}] source page failed {purl}: {e}'); continue
            base = purl
            for url, text in anchors(page, base):
                if candidate(url, text):
                    found.append((url, text))
            time.sleep(DELAY)
        # dedupe candidate links, then resolve each into an article + attachments
        seen = set()
        for url, text in found:
            if url in seen:
                continue
            seen.add(url)
            if is_attachment(url):                       # direct attachment link
                article_url, atts, title, date = url, [url], text, ''
            else:                                        # article page → find attachments
                if url in catalog:
                    continue
                raw = os.path.join(DIR, 'raw', safe(region) + '_' + safe(url.rsplit('/', 1)[-1] or 'index') + '.htm')
                if not os.path.exists(raw):
                    try:
                        open(raw, 'w', encoding='utf-8').write(get(url)); time.sleep(DELAY); new_art += 1
                    except Exception as e:
                        print(f'  [{region}] article failed {url}: {e}'); continue
                t = open(raw, encoding='utf-8', errors='replace').read()
                title, date = article_meta(t, text)
                atts = [u for u, _tx in anchors(t, url) if is_attachment(u)]
                article_url = url
            files, mds = [], []
            for a in atts:
                local = os.path.join(DIR, 'files', safe(region) + '_' + safe(a.rsplit('/', 1)[-1]))
                if not os.path.exists(local):
                    try:
                        open(local, 'wb').write(get(a, binary=True)); time.sleep(DELAY); new_file += 1
                    except Exception as e:
                        print(f'  [{region}] attachment failed {a}: {e}'); continue
                files.append(os.path.relpath(local, DIR))
                m = to_md(local, region)
                if m:
                    mds.append(m)
            catalog[article_url] = {'region': region, 'title': title or text, 'date': date,
                                    'article': article_url, 'attachments': atts,
                                    'files': files, 'markdown': mds}
    rows = sorted(catalog.values(), key=lambda c: (c['region'], c.get('date', ''), c['title']))
    json.dump(rows, open(os.path.join(DIR, 'catalog.json'), 'w'), ensure_ascii=False, indent=1)
    write_index(rows)
    print(f'  new: {new_art} articles, {new_file} attachments · catalog {len(rows)} documents')


def write_index(rows):
    with open(os.path.join(DIR, 'INDEX.md'), 'w', encoding='utf-8') as fh:
        fh.write('# 政府投资基金/引导基金「管理办法」 — local first-party documents\n\n')
        fh.write('Guidance-fund rule documents crawled from region source pages listed in '
                 '`sources.json`. Extend that file province by province. See '
                 '[`../SOURCES.md`](../SOURCES.md) for the method and the rest of the official channels.\n\n')
        fh.write(f'**Documents:** {len(rows)} · attachments under `files/` are gitignored '
                 '(re-downloadable via `catalog.json`); `markdown/` conversions are committed.\n\n')
        fh.write('| 地区 region | 日期 date | 文件 document | 附件 attachments |\n')
        fh.write('|------------|----------|---------------|------------------|\n')
        for c in rows:
            link = f"[{c['title']}]({c['article']})" if c['article'] else c['title']
            fh.write(f"| {c['region']} | {c.get('date') or ''} | {link} | {len(c.get('attachments', []))} |\n")


if __name__ == '__main__':
    print('Crawling local 政府投资基金/引导基金 管理办法 ...')
    crawl()
