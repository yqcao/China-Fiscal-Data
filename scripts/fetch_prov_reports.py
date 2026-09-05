#!/usr/bin/env python3
"""Download provincial government work reports (省级政府工作报告) and read the
year's headline GDP growth target out of each one.

Every source is the province's OWN official portal — the URL registry in
data/prov-reports/sources.json carries one entry per province per year, and each
is on that province's gov.cn domain. No aggregator, news compilation or
third-party table is used anywhere in this pipeline.

  raw/{year}_{CODE}.html   the page exactly as served
  text/{year}_{CODE}.txt   tags stripped, for reading and for the extractor
  targets.json             {province, year, target, phrasing, url, retrieved}

Provincial portals are slow and several sit behind rate limits, so fetches are
retried with a long timeout and cached — a re-run only pulls what is missing.
Idempotent.
"""
import os, re, json, time, html, shutil, datetime, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'prov-reports')
RAW  = os.path.join(DIR, 'raw')
TXT  = os.path.join(DIR, 'text')
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'

def get(url, tries=2, timeout=45):
    """curl, not urllib. urlopen's timeout applies per socket operation, so a
    portal that dribbles a byte every few seconds holds the connection open
    indefinitely — nmg.gov.cn hung a run for ten minutes that way. curl's
    --max-time is a wall-clock cap on the entire transfer. -k because a few
    provincial portals serve chains these roots do not validate."""
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(
                ['curl', '-sSL', '-k', '--max-time', str(timeout),
                 '--connect-timeout', '15',
                 '-H', 'User-Agent: ' + UA,
                 '-H', 'Accept-Language: zh-CN,zh;q=0.9',
                 '-H', 'Accept: text/html,application/xhtml+xml', url],
                capture_output=True, timeout=timeout + 20)
            if r.returncode == 0 and len(r.stdout) > 2000:
                for enc in ('utf-8', 'gb18030'):
                    try: return r.stdout.decode(enc)
                    except UnicodeDecodeError: pass
                return r.stdout.decode('utf-8', 'replace')
            last = RuntimeError(f'curl exit {r.returncode}, {len(r.stdout)} bytes'
                                + (' ' + r.stderr.decode('utf-8', 'replace')[:100] if r.stderr else ''))
        except subprocess.TimeoutExpired as e:
            last = e
        time.sleep(1 + 2 * i)
    raise last

def get_bytes(url, tries=2, timeout=90):
    for i in range(tries):
        r = subprocess.run(['curl', '-sSL', '-k', '--max-time', str(timeout),
                            '--connect-timeout', '20', '-H', 'User-Agent: ' + UA, url],
                           capture_output=True, timeout=timeout + 20)
        if r.returncode == 0 and r.stdout[:5] == b'%PDF-': return r.stdout
        time.sleep(1 + 2 * i)
    raise RuntimeError('not a PDF after %d tries' % tries)

def pdf_text(path):
    """Some reports are only published inside the 人大公报, which is a PDF."""
    md = shutil.which('markitdown') or os.path.expanduser('~/.local/bin/markitdown')
    out = path.rsplit('.', 1)[0] + '.md'
    subprocess.run([md, path, '-o', out], check=True, capture_output=True, timeout=300)
    return open(out, encoding='utf-8', errors='replace').read()

def strip(raw):
    b = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', raw, flags=re.S | re.I)
    b = re.sub(r'<(br|/p|/div|/tr|/h\d)\s*/?>', '\n', b, flags=re.I)
    return re.sub(r'\n{3,}', '\n\n', html.unescape(re.sub(r'<[^>]+>', '', b)))

# ---- the growth target ---------------------------------------------------
# Anchor on the sentence that announces the year's targets, then read the growth
# figure inside it. The anchor matters: without it the prior-year outturn
# ("地区生产总值增长3.9%") and the five-year-plan average ("年均增长5%左右") both
# match and both are the wrong number. The colon is what marks a target
# announcement — "「十四五」主要目标任务基本完成" has no colon and is skipped.
ANCHOR = re.compile(r'(?:主要)?(?:预期)?目标(?:是|为)?\s*[：:]')
# Provinces word both the subject and the range differently:
#   地区生产总值增长5%左右      most provinces
#   全市生产总值增长5%左右      Shanghai (and 全省/全区 elsewhere)
#   经济增长5.5%左右            Hubei
#   4.5%—5%                    percent on both ends
#   4.5-5%                     percent only on the last (Heilongjiang)
#   地区生产总值按增长5%安排  Jiangsu, via the 人大公报 PDF
FIGURE = re.compile(
    r'(?:(?:地区|全市|全省|全区)?生产总值(?:按|预计)?(?:增长|增速)|经济增长)'
    r'(?:预期目标)?\s*'
    r'(\d+(?:\.\d+)?)\s*%?'
    r'(?:\s*[—–\-~－至到]\s*(\d+(?:\.\d+)?)\s*%)?'
    r'\s*(左右|以上|以内)?')

def target(text):
    """-> (low, high, phrasing, sentence) or None. A range keeps both ends."""
    # '|' as well as whitespace: a gazette PDF converts to markdown tables whose
    # pipes run straight through the target sentence
    flat = re.sub(r'[\s|]+', '', text)
    for a in ANCHOR.finditer(flat):
        seg = flat[a.end():a.end() + 260]
        f = FIGURE.search(seg)
        if not f: continue
        lo = float(f.group(1))
        hi = float(f.group(2)) if f.group(2) else lo
        if not (0 < lo <= 20 and 0 < hi <= 20): continue     # sanity: a growth rate
        return lo, hi, (f.group(3) or ('区间' if f.group(2) else '')), seg[:120]
    return None

def main():
    os.makedirs(RAW, exist_ok=True); os.makedirs(TXT, exist_ok=True)
    reg = json.load(open(os.path.join(DIR, 'sources.json'), encoding='utf-8'))
    today = datetime.date.today().isoformat()
    rows, missing, failed = [], [], []
    for p in reg['provinces']:
        if not p['reports']:
            missing.append(p['cn']); continue
        for year, url in sorted(p['reports'].items()):
            base = f'{year}_{p["code"]}'
            is_pdf = url.lower().split('?')[0].endswith('.pdf')
            rawp = os.path.join(RAW, base + ('.pdf' if is_pdf else '.html'))
            txtp = os.path.join(TXT, base + '.txt')
            if not (os.path.exists(rawp) and os.path.getsize(rawp) > 2000):
                try:
                    # fetch first, write second: open(...,'w') truncates, so writing
                    # inline would leave a 0-byte file that later runs treat as cached
                    if is_pdf:
                        open(rawp, 'wb').write(get_bytes(url))
                    else:
                        open(rawp, 'w', encoding='utf-8').write(get(url))
                    time.sleep(1.0)
                except Exception as e:
                    print(f'  {p["cn"]:9} {year} FETCH FAILED  {type(e).__name__}: {e}')
                    failed.append((p['cn'], year, str(e))); continue
            txt = (pdf_text(rawp) if is_pdf
                   else strip(open(rawp, encoding='utf-8', errors='replace').read()))
            open(txtp, 'w', encoding='utf-8').write(txt)
            t = target(txt)
            if not t:
                print(f'  {p["cn"]:9} {year} no target found in {len(txt)} chars')
                failed.append((p['cn'], year, 'no target matched')); continue
            lo, hi, phrase, sent = t
            rows.append({'cn': p['cn'], 'en': p['en'], 'code': p['code'], 'year': int(year),
                         'low': lo, 'high': hi, 'phrasing': phrase,
                         'sentence': sent, 'url': url, 'domain': p['domain'],
                         'retrieved': today, 'file': f'text/{base}.txt'})
            print(f'  {p["cn"]:9} {year}  {lo}{"–"+str(hi) if hi != lo else ""}% {phrase}')
    rows.sort(key=lambda r: (r['year'], r['code']))
    json.dump(rows, open(os.path.join(DIR, 'targets.json'), 'w'),
              ensure_ascii=False, separators=(',', ':'))
    print(f'\n  targets.json: {len(rows)} province-years')
    if missing: print(f'  no URL yet ({len(missing)}): {" ".join(missing)}')
    if failed:  print(f'  failed ({len(failed)}): {", ".join(f"{a} {b}" for a, b, _ in failed)}')

if __name__ == '__main__':
    print('Fetching provincial 政府工作报告 from each province\'s own portal ...')
    main()
