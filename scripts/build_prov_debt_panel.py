#!/usr/bin/env python3
"""
Province panel: new-debt quota, issuance, execution, balance and the fiscal/macro
denominators, from data/celma/ (the MOF disclosure platform).

    python3 scripts/build_prov_debt_panel.py
      -> data/celma/prov_panel.json
      -> data/celma/prov_panel.csv

Completeness: the platform carries what each region reports, so recent years fill
in gradually. 2015-2024 are complete (the by-region sums reproduce the national
totals exactly); the latest year is usually partial and is flagged per row.
Gap-filling. The platform carries what each region reports, so the current year
has holes. Where a region has not reported its issuance, it is filled from
parse_prov_bonds.py -- the bond-by-bond appendix of the Debt Center's market
report, which covers every issuer. The two agree exactly for every region that
has reported (checked against the platform's own ZYZB summary for 2025: 32 of 32
matching to the yuan), so the fill is a continuation of the same figures, not a
different measure. Filled rows carry issue_source="market-report".

Quota has no second source: it is published only by the platform (and by each
province's own budget report, which this repo does not collect), so regions that
have not reported a quota simply have none, and no execution rate is computed
for them.
"""
import json, os, csv, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
D = BASE + 'data/celma/'
# adcodes for issuers the platform has not listed in a given year
CODE_FALLBACK = {'吉林省': '22', '河南省': '41', '西藏自治区': '54', '贵州省': '52', '青岛市': '3702'}

FIELDS = [
 ('quota_general', '新增一般债务限额'), ('quota_special', '新增专项债务限额'),
 ('issue_new_general', '新增一般债券发行额'), ('issue_new_special', '新增专项债券发行额'),
 ('issue_refi_general', '再融资一般债券发行额'), ('issue_refi_special', '再融资专项债券发行额'),
 ('issue_general', '一般债券发行额'), ('issue_special', '专项债券发行额'),
 ('repay_general', '一般债券还本额'), ('repay_special', '专项债券还本额'),
 ('interest_general', '一般债券付息额'), ('interest_special', '专项债券付息额'),
 ('limit_general', '一般债务限额'), ('limit_special', '专项债务限额'),
 ('bal_general', '一般债务余额'), ('bal_special', '专项债务余额'),
 ('gdp', '国内生产总值（亿元）'),
 ('budget_rev', '一般公共预算收入'), ('budget_exp', '一般公共预算支出'),
 ('fund_rev', '政府性基金预算收入'), ('fund_exp', '政府性基金预算支出'),
 ('retail', '社会消费品零售总额（亿元）'), ('trade', '进出口总额（亿元）'),
]


def quota_overrides():
    """2025+ quota taken from each region's own budget documents, for issuers the
    platform has not published. Never overrides a platform figure."""
    f = D + 'quota_sources.json'
    if not os.path.exists(f):
        return {}
    out = collections.defaultdict(dict)
    for e in json.load(open(f, encoding='utf-8')).get('entries', []):
        out[e['region']][int(e['year'])] = e
    return out


def appendix_issuance():
    """region -> year -> issuance from the market-report appendix, where parsed."""
    out = collections.defaultdict(dict)
    for f in sorted(os.listdir(D if os.path.isdir(D) else '.')):
        pass
    import glob
    for path in sorted(glob.glob(BASE + 'data/mof-research-reports/prov_bonds_*.json')):
        d = json.load(open(path, encoding='utf-8'))
        for r in d['by_region']:
            out[r['cn']][d['year']] = {
                'issue_new_general': r['new_general'] or None,
                'issue_new_special': r['new_special'] or None,
                'issue_refi_general': r['refi_general'] or None,
                'issue_refi_special': r['refi_special'] or None,
                'issue_general': round((r['new_general'] or 0) + (r['refi_general'] or 0), 2) or None,
                'issue_special': round((r['new_special'] or 0) + (r['refi_special'] or 0), 2) or None,
            }
    return out


def main():
    rows = json.load(open(D + 'annual_by_region.json'))
    appx = appendix_issuance()
    qov = quota_overrides()
    nat = collections.defaultdict(dict)
    for r in json.load(open(D + 'annual_national.json')):
        nat[r['year']][r['zb_name']] = r['amount']

    cell = collections.defaultdict(dict)
    code = {}
    for r in rows:
        cell[(r['region'], r['year'])][r['zb_name']] = r['amount']
        code[r['region']] = r['code']

    # years and regions the platform has not reached but the appendix has
    for reg, yrs in appx.items():
        for yr in yrs:
            if (reg, yr) not in cell and any(c for (r2, y2), c in cell.items() if y2 == yr):
                cell[(reg, yr)] = {}
                code.setdefault(reg, CODE_FALLBACK.get(reg, ''))

    out = []
    for (reg, yr), d in sorted(cell.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        o = {'region': reg, 'code': code.get(reg, ''), 'year': yr}
        for key, cn in FIELDS:
            o[key] = d.get(cn)
        # fill issuance from the market-report appendix only where the platform
        # has none; never overwrite what a region reported itself
        fill = appx.get(reg, {}).get(yr)
        o['issue_source'] = 'platform'
        if fill and not any(o[k] for k in ('issue_new_general', 'issue_new_special',
                                           'issue_refi_general', 'issue_refi_special')):
            for k, v in fill.items():
                if o.get(k) is None:
                    o[k] = v
            o['issue_source'] = 'market-report'
        # quota from the region's own budget document, only where the platform has none
        o['quota_source'] = 'platform' if (o['quota_general'] or o['quota_special']) else None
        ov = qov.get(reg, {}).get(yr)
        if ov and not o['quota_source']:
            o['quota_general'] = ov.get('general')
            o['quota_special'] = ov.get('special')
            o['quota_source'] = 'budget-report'
            o['quota_url'] = ov.get('url')
            o['quota_verification'] = ov.get('verification', 'direct')
        q = (o['quota_general'] or 0) + (o['quota_special'] or 0)
        i = (o['issue_new_general'] or 0) + (o['issue_new_special'] or 0)
        o['quota_total'] = q or None
        o['issue_new_total'] = i or None
        o['execution_pct'] = round(i / q * 100, 1) if q else None
        o['issue_refi_total'] = ((o['issue_refi_general'] or 0) + (o['issue_refi_special'] or 0)) or None
        o['bal_total'] = ((o['bal_general'] or 0) + (o['bal_special'] or 0)) or None
        o['debt_to_gdp_pct'] = (round(o['bal_total'] / o['gdp'] * 100, 1)
                                if o['bal_total'] and o['gdp'] else None)
        out.append(o)

    # a year is complete when the regions reproduce the national issuance totals
    comp = {}
    for yr in sorted({r['year'] for r in out}):
        got = sum((r['issue_new_general'] or 0) + (r['issue_new_special'] or 0)
                  for r in out if r['year'] == yr)
        want = (nat[yr].get('新增一般债券发行额') or 0) + (nat[yr].get('新增专项债券发行额') or 0)
        yrows = [r for r in out if r['year'] == yr]
        comp[yr] = {'regions': len(yrows),
                    'region_sum': round(got, 2), 'national': round(want, 2),
                    'complete': bool(want) and abs(got - want) < max(1.0, want * 0.001),
                    'with_issuance': sum(1 for r in yrows if r['issue_new_total']),
                    'with_quota': sum(1 for r in yrows if r['quota_total']),
                    'filled': sum(1 for r in yrows if r.get('issue_source') == 'market-report'),
                    'quota_sourced': sum(1 for r in yrows if r.get('quota_source') == 'budget-report')}
    for r in out:
        r['year_complete'] = comp[r['year']]['complete']

    json.dump({'unit': '亿元', 'source': 'celma.org.cn', 'completeness': comp, 'rows': out},
              open(D + 'prov_panel.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    cols = (['region', 'code', 'year', 'year_complete', 'issue_source', 'quota_source',
             'quota_verification',
             'quota_total', 'issue_new_total',
             'execution_pct', 'issue_refi_total', 'bal_total', 'debt_to_gdp_pct']
            + [k for k, _ in FIELDS])
    with open(D + 'prov_panel.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in out: w.writerow(r)
    print(f'  prov_panel.json / .csv: {len(out)} region-years')
    for yr, c in comp.items():
        print(f"    {yr}  {c['regions']:2d} regions | issuance {c['with_issuance']:2d}"
              f"{(' (+' + str(c['filled']) + ' from market report)') if c['filled'] else ''}"
              f" | quota {c['with_quota']:2d}"
              f"{(' (+' + str(c['quota_sourced']) + ' from budget reports)') if c['quota_sourced'] else ''}"
              f" | new-bond {c['region_sum']:>10,.0f}"
              f" vs national {c['national']:>10,.0f}"
              f"  {'complete' if c['complete'] else 'PARTIAL'}")


if __name__ == '__main__':
    main()
