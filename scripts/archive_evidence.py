#!/usr/bin/env python3
"""固定证据 (pin the evidence) for province_scale.json.

Source URLs rot — gov pages 403/503, get moved, or are media reposts that vanish.
This script makes every figure's evidence durable and checkable:

  1. Fetches each unique source URL, saves a cleaned-text snapshot to
     evidence/text/<sha8>.txt (committed to the repo — the primary durable copy).
  2. Records the raw-bytes sha256 + byte length + HTTP status + fetch date.
  3. VERIFIES the claim: checks whether the distinctive number(s) from each row's
     quote actually appear in the fetched page text (verified / not-found / no-fetch).
  4. Looks up a permanent Wayback Machine snapshot (and, with --save, asks the
     Wayback Machine to capture URLs that have none) as a secondary pin.

Outputs:
  evidence/text/*.txt        cleaned snapshots (the on-disk evidence)
  evidence/manifest.json     per-URL: provinces, status, sha256, verified, wayback
  EVIDENCE.md                human-readable pin status, grouped by verification
  sources.json               per-province recheck recipe (canonical page + channel)

Re-run anytime: python3 scripts/archive_evidence.py [--save] [--only PROVINCE]
  --save   also trigger web.archive.org/save for URLs lacking a snapshot (slow)
"""
import os, re, sys, json, html, time, hashlib, datetime, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'govt-guidance-funds')
EVID = os.path.join(DIR, 'evidence')
TEXT = os.path.join(EVID, 'text')
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
SAVE = '--save' in sys.argv
WB   = SAVE or '--wayback' in sys.argv   # Wayback lookups are slow; opt in
ONLY = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None


def get(url, timeout=20):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,*/*'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def to_text(raw):
    t = raw.decode('utf-8', 'replace')
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = html.unescape(t)
    return re.sub(r'[ \t　]+', ' ', re.sub(r'\n\s*\n+', '\n', t)).strip()


def norm(s):
    """Drop separators so '17,700' / '1.77 万亿' style variants compare cleanly."""
    return re.sub(r'[\s,，]', '', s or '')


def claim_tokens(quote):
    """Distinctive number tokens to look for: numbers with a 亿/万亿/万/% suffix,
    plus bare decimals >= 3 chars (e.g. 112.65, 534.75, 7549)."""
    toks = re.findall(r'\d+(?:\.\d+)?(?:万亿|亿元|亿|万|%)', quote or '')
    toks += [t for t in re.findall(r'\d+\.\d+', quote or '') if len(t) >= 4]
    # keep distinctive ones (avoid bare years / single small ints)
    return sorted(set(toks), key=len, reverse=True)


def wayback_lookup(url):
    api = 'https://archive.org/wayback/available?url=' + urllib.parse.quote(url, safe='')
    try:
        _, raw = get(api, timeout=30)
        snap = (json.loads(raw).get('archived_snapshots') or {}).get('closest')
        if snap and snap.get('available'):
            return snap.get('url'), snap.get('timestamp')
    except Exception:
        pass
    return None, None


def wayback_save(url):
    try:
        get('https://web.archive.org/save/' + url, timeout=60)
        time.sleep(2)
    except Exception:
        pass


def main():
    os.makedirs(TEXT, exist_ok=True)
    rows = json.load(open(os.path.join(DIR, 'province_scale.json')))['data']
    if ONLY:
        rows = [r for r in rows if r['province'] == ONLY]
    # reuse Wayback links already found on a previous run (avoid re-querying / regressing)
    prior_wb = {}
    mpath = os.path.join(EVID, 'manifest.json')
    if os.path.exists(mpath):
        for m in json.load(open(mpath)).get('sources', []):
            if m.get('wayback_url'):
                prior_wb[m['url']] = (m['wayback_url'], m.get('wayback_ts'))

    # group rows by url
    by_url = {}
    for r in rows:
        if not r.get('source'):
            continue
        by_url.setdefault(r['source'], []).append(r)

    manifest = []
    for url, rs in by_url.items():
        h8 = hashlib.sha256(url.encode()).hexdigest()[:12]
        provinces = sorted({r['province'] for r in rs})
        rec = {'url': url, 'provinces': provinces, 'rows': len(rs),
               'status': None, 'sha256': None, 'bytes': None, 'text_file': None,
               'verified': 'no-fetch', 'matched': [], 'missing': [],
               'wayback_url': None, 'wayback_ts': None,
               'fetched': datetime.date.today().isoformat()}
        try:
            status, raw = get(url)
            rec['status'] = status
            rec['sha256'] = hashlib.sha256(raw).hexdigest()
            rec['bytes'] = len(raw)
            txt = to_text(raw)
            fn = f'{provinces[0]}_{h8}.txt'
            open(os.path.join(TEXT, fn), 'w', encoding='utf-8').write(
                f'SOURCE: {url}\nFETCHED: {rec["fetched"]}\nSHA256(raw): {rec["sha256"]}\n'
                f'PROVINCES: {",".join(provinces)}\n{"="*60}\n{txt}')
            rec['text_file'] = f'evidence/text/{fn}'
            body = norm(txt)
            want, have = [], []
            for r in rs:
                toks = claim_tokens(r['quote'])
                key = toks[0] if toks else None
                if not key:
                    continue
                want.append(key)
                if norm(key) in body:
                    have.append(key)
            rec['matched'] = sorted(set(have))
            rec['missing'] = sorted(set(want) - set(have))
            rec['verified'] = ('verified' if want and not rec['missing'] else
                               'partial' if have else
                               'not-found' if want else 'no-number')
        except Exception as e:
            rec['status'] = str(e).split('\n')[0][:80]
        wb_url, wb_ts = (wayback_lookup(url) if WB else prior_wb.get(url, (None, None)))
        if not wb_url and SAVE and rec['verified'] != 'verified':
            wayback_save(url)
            wb_url, wb_ts = wayback_lookup(url)
        rec['wayback_url'], rec['wayback_ts'] = wb_url, wb_ts
        flag = {'verified': '✓', 'partial': '~', 'not-found': '✗', 'no-fetch': '!', 'no-number': '·'}.get(rec['verified'], '?')
        print(f"  [{flag}] {rec['status']!s:>3}  wb={'Y' if wb_url else '-'}  {','.join(provinces)}  {url[:60]}")
        manifest.append(rec)
        time.sleep(0.3)

    manifest.sort(key=lambda m: (m['provinces'], m['url']))
    json.dump({'updated': datetime.date.today().isoformat(), 'count': len(manifest),
               'sources': manifest}, open(os.path.join(EVID, 'manifest.json'), 'w'),
              ensure_ascii=False, indent=1)

    # ---- sources.json: per-province recheck recipe (from headline rows) ----
    def channel(url, report):
        u = url.lower()
        if 'czt.' in u or 'caizheng' in u or '财政厅' in report: return '财政厅(公告/专栏/预算报告)'
        if 'mof.gov.cn' in u: return '财政部专题'
        if any(k in u for k in ('pdf', 'evaluation', 'rating')) or '评级' in report: return '评级/债券披露'
        if '.gov.cn' in u: return '政府/部门官网'
        if any(k in report for k in ('日报', '证券', '财经', '澎湃', '新华', '21', '投中', '投资界')): return '官方媒体/财经媒体'
        return '其他'
    src_recipe = {}
    for r in rows:
        if not r['headline']:
            continue
        src_recipe[r['province']] = {
            'province': r['province'],
            'latest_value_yi': r['value_yi'], 'latest_paidin_yi': r['paidin_yi'],
            'latest_count': r['count'], 'latest_basis': r['basis'],
            'as_of': r['report_date'], 'metric': r['metric'],
            'channel': channel(r['source'], r['report']),
            'recheck_url': r['source'], 'report': r['report'],
            'note': '年度复查:在此渠道找下一年同口径汇总(发布会/运营情况/预算报告)。',
        }
    json.dump({'updated': datetime.date.today().isoformat(),
               'note': '逐省「本省汇总规模」的官方复查入口。channel=财政厅专栏 的最可复现(如四川)。',
               'provinces': dict(sorted(src_recipe.items()))},
              open(os.path.join(DIR, 'sources.json'), 'w'), ensure_ascii=False, indent=1)

    # ---- EVIDENCE.md ----
    by_state = {}
    for m in manifest:
        by_state.setdefault(m['verified'], []).append(m)
    nver = len(by_state.get('verified', [])); npar = len(by_state.get('partial', []))
    nwb = sum(1 for m in manifest if m['wayback_url'])
    L = ['# 证据固定 (evidence pin) — province_scale', '',
         f'{len(manifest)} 个唯一来源 · 抓取于 {datetime.date.today().isoformat()}。', '',
         f'- **数字核验通过(verified)**: {nver} · 部分(partial): {npar} · '
         f'未命中(not-found): {len(by_state.get("not-found",[]))} · 抓取失败(no-fetch): {len(by_state.get("no-fetch",[]))}',
         f'- **本地文本快照**: evidence/text/ (随仓库提交，URL 失效也在)',
         f'- **Wayback 永久存档**: {nwb}/{len(manifest)} 个有快照', '',
         '> verified = 引用的关键数字在抓取到的原文里找到;not-found/no-fetch 多因 gov 页 403/503 '
         '或为图片版 PDF/媒体转载,这些依赖本地快照+Wayback 兜底。', '',
         '| 核验 | HTTP | Wayback | 省 | 关键数字 | 快照 | 来源 |',
         '|:--:|:--:|:--:|------|------|------|------|']
    flagmap = {'verified': '✓', 'partial': '~', 'not-found': '✗', 'no-fetch': '!', 'no-number': '·'}
    for m in sorted(manifest, key=lambda x: (x['verified'] != 'verified', x['provinces'])):
        nums = ','.join((m['matched'] or m['missing'])[:3]) or '—'
        snap = f"[txt]({m['text_file']})" if m['text_file'] else '—'
        wb = f"[wb]({m['wayback_url']})" if m['wayback_url'] else '—'
        L.append(f"| {flagmap.get(m['verified'],'?')} | {m['status']} | {wb} | {','.join(m['provinces'])} | "
                 f"{nums} | {snap} | [src]({m['url']}) |")
    open(os.path.join(ROOT, 'data', 'govt-guidance-funds', 'EVIDENCE.md'), 'w', encoding='utf-8').write('\n'.join(L))

    print(f"\n  manifest: {len(manifest)} sources · verified {nver} · partial {npar} · "
          f"wayback {nwb} · snapshots in evidence/text/")
    print(f"  sources.json: {len(src_recipe)} provinces' recheck entries")


if __name__ == '__main__':
    print(f'Pinning evidence for province_scale.json {"(+wayback save)" if SAVE else ""}...')
    main()
    print('Done.')
