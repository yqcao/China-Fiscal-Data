#!/usr/bin/env python3
"""
中国地方政府债券信息公开平台 (celma.org.cn) — the MOF-run local-government bond
disclosure platform mandated by 《地方政府债券信息公开平台管理办法》.

This is the only official source that publishes the **new-debt quota allocated to
each province** (新增一般/专项债务限额) alongside that province's actual issuance,
so it is what makes province-level execution computable. The Debt Center's market
report gives issuance only, and its by-province table is an image.

The site renders from a JSON API; this fetcher calls the same endpoint the page
does, at low frequency, and stores the result.

    python3 scripts/fetch_celma.py          -> data/celma/*.json

Indicators (annual, by region and national):
  01 债务限额   0101 限额 / 0102 新增限额        (general, special)
  03 债券发行额 0301 小计 / 0302 新增 / 0304 再融资
  04 债券还本   05 债券付息   06 债务余额   07 债券余额
Monthly and quarterly carry the flow indicators (03/04/05) only.
"""
import json, os, time, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
OUT = BASE + 'data/celma/'
API = 'https://www.governbond.org.cn:4443/api/loadBondData.action'
REFERER = 'https://www.celma.org.cn/ndsj/index.jhtml'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/140.0 Safari/537.36')
PAUSE = 1.0          # be a polite client; the site is a small government service


def get(**params):
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': REFERER})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode('utf-8'))
    time.sleep(PAUSE)
    if d.get('code') != '0':
        raise RuntimeError(f'API code {d.get("code")} for {params}')
    return d.get('data') or []


def tree(flag, zone):
    """Indicator tree. flag: year|quarter|month, zone: qg (national) | fdq (by region)."""
    return [{'id': z['ID'], 'parent': z.get('ZB_PARENT_ID') or None,
             'name': (z.get('ZB_NAME') or '').strip(),
             'note': (z.get('FDQ_REMARKS') if zone == 'fdq' else z.get('QG_REMARKS')) or None}
            for z in get(dataType='ZBLIST', flag=flag, zbZone=zone)]


SKIPPED = []


def num(r, key):
    """The API returns the odd row with a field missing (seen: one Liaoning row
    with no SET_YEAR). Skip those rather than fail the whole run."""
    return r.get(key)


def leaves(tr):
    """Only the indicators that actually carry numbers (the leaf nodes)."""
    parents = {z['parent'] for z in tr if z['parent']}
    return [z for z in tr if z['id'] not in parents]


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {'source': 'https://www.celma.org.cn/ (中国地方政府债券信息公开平台)',
            'api': API, 'unit': '亿元', 'fetched': time.strftime('%Y-%m-%d'), 'trees': {}}

    # ---- annual, by region: quota + issuance + repayment + balance -------------
    tr = tree('year', 'fdq'); meta['trees']['year_fdq'] = tr
    rows = []
    for z in leaves(tr):
        d = get(dataType='FDQNDZB', zb=z['id'])
        for r in d:
            if r.get('SET_YEAR') is None or r.get('AMOUNT') is None:
                SKIPPED.append({'zb': z['id'], **r}); continue
            rows.append({'zb': z['id'], 'zb_name': z['name'],
                         'code': r['AD_CODE'], 'region': r['AD_NAME'],
                         'year': int(r['SET_YEAR']), 'amount': float(r['AMOUNT'])})
        print(f"  year/fdq {z['id']} {z['name'][:22]:24s} {len(d):5d} rows")
    json.dump(rows, open(OUT + 'annual_by_region.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    yrs = sorted({r['year'] for r in rows}); regs = sorted({r['region'] for r in rows})
    print(f"  -> annual_by_region.json  {len(rows)} rows, {len(regs)} regions, {yrs[0]}..{yrs[-1]}")

    # ---- annual, national ------------------------------------------------------
    trq = tree('year', 'qg'); meta['trees']['year_qg'] = trq
    nat = []
    for z in leaves(trq):
        d = get(dataType='NDZB', adCode=87, zb=z['id'])
        for r in d:
            if r.get('SET_YEAR') is None or r.get('AMOUNT') is None:
                SKIPPED.append({'zb': z['id'], **r}); continue
            nat.append({'zb': z['id'], 'zb_name': z['name'],
                        'year': int(r['SET_YEAR']), 'amount': float(r['AMOUNT'])})
    json.dump(nat, open(OUT + 'annual_national.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    print(f"  -> annual_national.json   {len(nat)} rows")

    # ---- monthly, by region: the flow indicators -------------------------------
    trm = tree('month', 'fdq'); meta['trees']['month_fdq'] = trm
    mon = []
    for z in leaves(trm):
        d = get(dataType='FDQYDZB', zb=z['id'], monthSpan=20)
        for r in d:
            if r.get('SET_MONTH') is None or r.get('AMOUNT') is None:
                SKIPPED.append({'zb': z['id'], **r}); continue
            mon.append({'zb': z['id'], 'zb_name': z['name'],
                        'code': r['AD_CODE'], 'region': r['AD_NAME'],
                        'period': str(r['SET_MONTH']), 'amount': float(r['AMOUNT'])})
        print(f"  month/fdq {z['id']} {z['name'][:22]:24s} {len(d):5d} rows")
    json.dump(mon, open(OUT + 'monthly_by_region.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    if mon:
        ps = sorted({r['period'] for r in mon})
        print(f"  -> monthly_by_region.json {len(mon)} rows, {ps[0]}..{ps[-1]}")

    meta['skipped_malformed'] = SKIPPED
    json.dump(meta, open(OUT + 'meta.json', 'w'), ensure_ascii=False, indent=1)
    print(f'  -> meta.json   (skipped {len(SKIPPED)} malformed rows)')


if __name__ == '__main__':
    print('Fetching 中国地方政府债券信息公开平台 (celma.org.cn) ...')
    main()
