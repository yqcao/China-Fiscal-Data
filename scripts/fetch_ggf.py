#!/usr/bin/env python3
"""Collect 政府投资基金 / 地方政府引导基金 (government guidance fund) records.

Source: 中国证券投资基金业协会 信息公示 (AMAC fund disclosure)
  https://gs.amac.org.cn/   (JSON API under /amac-infodisc/api/pof/)

Most government guidance funds and their sub-funds operate as filed private
equity / venture funds, so they appear in AMAC's public registry. This script
pages the fund list, keeps records whose fund OR manager name matches a
government-guidance-fund keyword (see KEYWORDS), and writes into
data/govt-guidance-funds/:
  funds.json      filtered fund records (merged across runs, newest first)
  managers.json   distinct managers of those funds, with fund counts
  INDEX.md        human-readable, date-sorted table
  state.json      run watermark (newest filing date seen) for incremental runs

Idempotent / incremental: re-runs dedupe by fund id; in incremental mode the
scan stops once it reaches filing dates already covered by a previous run.

NETWORK: gs.amac.org.cn must be reachable. In Claude Code web sessions the
egress allowlist blocks it by default — add the host to the environment's
network settings, or run this locally where outbound access is open.

CAVEATS:
  * AMAC does not tag "government guidance fund"; this filters by NAME only.
    Verify each hit against the 发改委 登记系统 / local announcements before
    treating it as an official government guidance fund (see SOURCES.md).
  * Keep the request rate low and review AMAC's terms before large backfills.
  * The API field names / sort order below follow AMAC's public disclosure
    JSON; if AMAC changes them, adjust norm()/rec_date() after one live run.

Usage:
  python3 scripts/fetch_ggf.py --probe          # one page, no writes: verify API shape
  python3 scripts/fetch_ggf.py                  # incremental: newest pages
  python3 scripts/fetch_ggf.py --max-pages 80   # cap pages scanned this run
  python3 scripts/fetch_ggf.py --full           # full backfill (slow; ~1500 pages)
"""
import os, sys, json, time, random, datetime, urllib.request

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR    = os.path.join(ROOT, 'data', 'govt-guidance-funds')
API    = 'https://gs.amac.org.cn/amac-infodisc/api/pof/fund'
DETAIL = 'https://gs.amac.org.cn/amac-infodisc/res/pof/fund/{}.html'
UA     = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
SIZE   = 100          # records per page
DELAY  = 0.5          # seconds between requests (be polite)
DEFAULT_MAX_PAGES = 60   # incremental safety cap (~6000 newest funds)

# Name patterns that strongly indicate a government guidance fund / 政府投资基金.
# Matched against fund name AND manager name. Tune as needed.
KEYWORDS = ['引导基金', '政府投资基金', '政府引导', '产业引导', '创业投资引导',
            '创投引导', '政府出资', '政府产业投资']

FUNDS = os.path.join(DIR, 'funds.json')
MGRS  = os.path.join(DIR, 'managers.json')
INDEX = os.path.join(DIR, 'INDEX.md')
STATE = os.path.join(DIR, 'state.json')


def post(page):
    body = json.dumps({}).encode()
    url = f'{API}?rand={random.random()}&page={page}&size={SIZE}'
    req = urllib.request.Request(url, data=body, method='POST', headers={
        'User-Agent': UA, 'Content-Type': 'application/json',
        'Accept': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace'))


def probe():
    """Fetch one page and print the live API shape — run this first after enabling
    network, to confirm field names match norm()/rec_date() before a real run."""
    data = post(0)
    print('  top-level keys:', sorted(data.keys()))
    print('  totalElements:', data.get('totalElements'), '· totalPages:', data.get('totalPages'),
          '· size:', data.get('size'), '· number:', data.get('number'))
    content = data.get('content') or []
    print('  records on page 0:', len(content))
    if content:
        r = content[0]
        print('  first-record keys:', sorted(r.keys()))
        for k in ('fundName', 'managerName', 'mandatorName', 'establishDate',
                  'putOnRecordDate', 'workingState', 'fundStatus', 'url', 'id'):
            if k in r:
                print(f'    {k} = {r[k]!r}')
        print('  → matches() on this record:', matches(r))


def load(path, default):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else default


def fmt_date(v):
    """AMAC returns dates as epoch-millis ints; normalise to YYYY-MM-DD."""
    if v in (None, ''): return ''
    if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
        try:
            return datetime.datetime.utcfromtimestamp(int(v) / 1000).strftime('%Y-%m-%d')
        except Exception:
            return str(v)
    return str(v)[:10]


def fund_id(r):
    return str(r.get('url') or r.get('id') or '') or \
        '|'.join(str(r.get(k, '')) for k in ('fundName', 'managerName', 'establishDate'))


def rec_date(r):
    return r.get('putOnRecordDate') or r.get('establishDate')


def matches(r):
    s = (r.get('fundName') or '') + ' ' + (r.get('managerName') or '')
    return any(k in s for k in KEYWORDS)


def norm(r):
    return {
        'id': fund_id(r),
        'fund': r.get('fundName'),
        'manager': r.get('managerName'),
        'custodian': r.get('mandatorName'),
        'establish': fmt_date(r.get('establishDate')),
        'record': fmt_date(r.get('putOnRecordDate')),
        'status': r.get('workingState') or r.get('fundStatus'),
        'detail': DETAIL.format(r['url']) if r.get('url') else None,
    }


def write_outputs(funds):
    rows = sorted(funds.values(), key=lambda f: (f.get('record') or '', f.get('establish') or ''), reverse=True)
    json.dump(rows, open(FUNDS, 'w'), ensure_ascii=False, indent=1)

    mgr = {}
    for f in rows:
        m = f.get('manager')
        if not m: continue
        mgr.setdefault(m, {'manager': m, 'funds': 0})['funds'] += 1
    managers = sorted(mgr.values(), key=lambda x: (-x['funds'], x['manager']))
    json.dump(managers, open(MGRS, 'w'), ensure_ascii=False, indent=1)

    span = ''
    dates = [f['record'] for f in rows if f.get('record')]
    if dates: span = f"{min(dates)}–{max(dates)}"
    with open(INDEX, 'w', encoding='utf-8') as fh:
        fh.write('# 政府投资基金 / 地方政府引导基金 — AMAC filings\n\n')
        fh.write('Government-guidance-fund records filtered from the AMAC public fund '
                 'disclosure system by fund/manager name. See [`SOURCES.md`](SOURCES.md) '
                 'for the full catalogue of official channels and the verification caveat.\n\n')
        fh.write(f'**Source:** https://gs.amac.org.cn/ · **Funds:** {len(rows)} · '
                 f'**Managers:** {len(managers)} · **Filing dates:** {span or "—"}\n\n')
        fh.write('> Name-based filter only — confirm each fund against the 发改委 登记系统 / '
                 'local announcements before treating it as an official government guidance fund.\n\n')
        fh.write('| 备案 record | 成立 establish | 基金 fund | 管理人 manager | 状态 status |\n')
        fh.write('|------------|---------------|-----------|----------------|-------------|\n')
        for f in rows:
            name = f"[{f.get('fund') or ''}]({f['detail']})" if f.get('detail') else (f.get('fund') or '')
            fh.write(f"| {f.get('record') or ''} | {f.get('establish') or ''} | {name} | "
                     f"{f.get('manager') or ''} | {f.get('status') or ''} |\n")
    print(f'  funds.json: {len(rows)} funds · managers.json: {len(managers)} · {span}')


def run(full, max_pages):
    os.makedirs(DIR, exist_ok=True)
    funds = {f['id']: f for f in load(FUNDS, [])}
    watermark = load(STATE, {}).get('watermark', '')
    new_watermark = watermark
    new_hits = 0
    page = 0
    while True:
        if not full and max_pages and page >= max_pages:
            print(f'  reached --max-pages {max_pages}; stopping'); break
        try:
            data = post(page)
        except Exception as e:
            print(f'  page {page} failed: {e}'); break
        content = data.get('content') or []
        if not content:
            break
        total = data.get('totalPages')
        page_oldest = '9999-99-99'
        for r in content:
            d = fmt_date(rec_date(r))
            if d:
                if d > new_watermark: new_watermark = d
                if d < page_oldest: page_oldest = d
            if matches(r):
                rec = norm(r)
                if rec['id'] not in funds: new_hits += 1
                funds[rec['id']] = rec
        print(f'  page {page + 1}/{total or "?"}  (+{new_hits} guidance-fund hits total this run)')
        # Incremental stop: the list is sorted newest-first, so once a whole page
        # is older than last run's watermark we have caught up with prior data.
        if not full and watermark and page_oldest <= watermark:
            print('  caught up with previous run; stopping'); break
        page += 1
        if total and page >= total:
            break
        time.sleep(DELAY)

    write_outputs(funds)
    json.dump({'watermark': new_watermark, 'updated': datetime.date.today().isoformat()},
              open(STATE, 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    if '--probe' in sys.argv:
        print('Probing AMAC fund API (one page, no writes) ...')
        probe()
        sys.exit(0)
    full = '--full' in sys.argv
    max_pages = DEFAULT_MAX_PAGES
    if '--max-pages' in sys.argv:
        max_pages = int(sys.argv[sys.argv.index('--max-pages') + 1])
    print('Fetching AMAC 政府投资基金 / 引导基金 filings ...')
    run(full, max_pages)
