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


def ytd_from_monthly(have_years):
    """
    Year-to-date rows for a year the platform has not published annually yet.

    The platform posts by-region monthly data well before it posts the annual
    table, so the current year can be tracked from the monthly series. It is only
    usable up to the last month where the 37 regions still add up to MOF's own
    national release -- regions report at their own pace, and a month missing four
    of them understates the country by ~20%. So each month is reconciled against
    data/mof-debt-balance/repayment_series.json and the series is cut at the last
    month that agrees within 0.5%.
    """
    f = D + 'monthly_by_region.json'
    if not os.path.exists(f):
        return {}, {}
    mon = json.load(open(f, encoding='utf-8'))
    nat = {r['period']: r for r in json.load(
        open(BASE + 'data/mof-debt-balance/repayment_series.json', encoding='utf-8'))}

    ISS = ('一般债券发行额', '专项债券发行额')
    by_period = collections.defaultdict(float)
    for r in mon:
        if r['zb_name'] in ISS:
            by_period[r['period']] += r['amount']

    out, meta = {}, {}
    for yr in sorted({int(p[:4]) for p in by_period} - set(have_years)):
        months = sorted(p for p in by_period if p.startswith(str(yr)))
        good = []
        for p in months:
            k = f'{p[:4]}-{p[4:]}'
            want = (nat.get(k) or {}).get('issue')
            got = by_period[p]
            if not want or abs(got - want) > max(1.0, want * 0.005):
                break
            good.append(p)
        if not good:
            continue
        # Flows accumulate across the months; stocks do not -- a balance is a
        # level at a point in time, so take the latest month's value instead of
        # adding seven of them together.
        STOCK = ('一般债务余额', '专项债务余额', '一般债券余额', '专项债券余额',
                 '一般债务限额', '专项债务限额')
        last = good[-1]
        cell = collections.defaultdict(lambda: collections.defaultdict(float))
        code = {}
        for r in mon:
            if r['period'] not in good:
                continue
            code[r['region']] = r['code']
            if r['zb_name'] in STOCK:
                if r['period'] == last:
                    cell[r['region']][r['zb_name']] = r['amount']
            else:
                cell[r['region']][r['zb_name']] += r['amount']
        out[yr] = {reg: (dict(d), code[reg]) for reg, d in cell.items()}
        meta[yr] = {'ytd_through': f'{good[-1][:4]}-{good[-1][4:]}',
                    'months': len(good),
                    'dropped': [f'{p[:4]}-{p[4:]}' for p in months if p not in good],
                    'prior': prior_same_period(yr, {int(p[4:]) for p in good})}
    return out, meta


def prior_same_period(year, months):
    """
    Prior-year new-bond issuance over the SAME months, by region.

    A year-to-date figure is only comparable to the matching slice of the year
    before, so this reads the month-level appendix parse for year-1 and sums the
    same months. The appendix is used rather than the platform's monthly series
    because that series is missing January 2025, which would silently understate
    the base.
    """
    import glob
    f = BASE + f'data/mof-research-reports/prov_bonds_{year - 1}.json'
    if not os.path.exists(f):
        return {}
    d = json.load(open(f, encoding='utf-8'))
    cn = {r['region']: r['cn'] for r in d['by_region']}
    out = collections.defaultdict(float)
    for r in d.get('by_region_month', []):
        if r['month'] in months:
            out[cn.get(r['region'], r['region'])] += r['new']
    return dict(out)


ADCODE = {'11':'北京市','12':'天津市','13':'河北省','14':'山西省','15':'内蒙古自治区','21':'辽宁省',
 '2102':'大连市','22':'吉林省','23':'黑龙江省','31':'上海市','32':'江苏省','33':'浙江省','3302':'宁波市',
 '34':'安徽省','35':'福建省','3502':'厦门市','36':'江西省','37':'山东省','3702':'青岛市','41':'河南省',
 '42':'湖北省','43':'湖南省','44':'广东省','4403':'深圳市','45':'广西壮族自治区','46':'海南省','50':'重庆市',
 '51':'四川省','52':'贵州省','53':'云南省','54':'西藏自治区','61':'陕西省','62':'甘肃省','63':'青海省',
 '64':'宁夏回族自治区','65':'新疆维吾尔自治区','66':'新疆生产建设兵团'}


def limit_tables(year):
    """
    Quota from the statutory 表1-6 filings scraped by fetch_celma_limits.py.

    These are the primary source: each region files the table with the MOF
    platform after its people's congress approves the budget adjustment. A region
    can file more than once in a year as further tranches are allocated, so the
    LATEST cumulative filing wins. Advance-batch filings (表1-5) are ignored --
    mixing an advance figure in with cumulative ones would make execution rates
    incomparable.
    """
    f = D + f'limit_tables_{year}.json'
    if not os.path.exists(f):
        return {}
    best = {}
    for t in json.load(open(f, encoding='utf-8')).get('tables', []):
        if t.get('stage') != 'cumulative':
            continue
        reg = ADCODE.get(t['adcode']) or t.get('region') or t['adcode']
        prev = best.get(reg)
        if prev is None or (t.get('published') or '') > (prev.get('published') or ''):
            best[reg] = t
    return best


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
    ltab = {y: limit_tables(y) for y in (2025, 2026)}
    annual_years = {r['year'] for r in rows
                    if r['zb_name'] in ('新增一般债券发行额', '新增专项债券发行额') and r['amount']}
    ytd, ytd_meta = ytd_from_monthly(annual_years)
    nat = collections.defaultdict(dict)
    for r in json.load(open(D + 'annual_national.json')):
        nat[r['year']][r['zb_name']] = r['amount']

    cell = collections.defaultdict(dict)
    code = {}
    for r in rows:
        cell[(r['region'], r['year'])][r['zb_name']] = r['amount']
        code[r['region']] = r['code']

    # a current year the platform has not published annually, built from monthly
    for yr, regs in ytd.items():
        for reg, (d, c) in regs.items():
            cell[(reg, yr)] = d
            code.setdefault(reg, c)

    # years and regions the platform has not reached but the appendix has
    for reg, yrs in appx.items():
        for yr in yrs:
            if (reg, yr) not in cell and any(c for (r2, y2), c in cell.items() if y2 == yr):
                cell[(reg, yr)] = {}
                code.setdefault(reg, CODE_FALLBACK.get(reg, ''))

    out = []
    for (reg, yr), d in sorted(cell.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        o = {'region': reg, 'code': code.get(reg, ''), 'year': yr,
             'basis': 'ytd' if yr in ytd else 'annual',
             'ytd_through': (ytd_meta.get(yr) or {}).get('ytd_through')}
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
        lt = (ltab.get(yr) or {}).get(reg)
        if lt and not o['quota_source']:
            # the statutory filing is the primary source
            o['quota_general'] = lt.get('general')
            o['quota_special'] = lt.get('special')
            o['quota_source'] = 'limit-table'
            o['quota_url'] = lt.get('article')
            o['quota_verification'] = 'direct'
            o['quota_as_of'] = lt.get('published')
            if ov:  # both sources exist -- they must agree
                dg = abs((ov.get('general') or 0) - (lt.get('general') or 0))
                ds = abs((ov.get('special') or 0) - (lt.get('special') or 0))
                o['quota_crosscheck'] = 'agree' if dg < 0.5 and ds < 0.5 else 'DISAGREE'
        elif ov and not o['quota_source']:
            o['quota_general'] = ov.get('general')
            o['quota_special'] = ov.get('special')
            o['quota_source'] = 'budget-report'
            o['quota_url'] = ov.get('url')
            o['quota_verification'] = ov.get('verification', 'direct')
            o['quota_as_of'] = ov.get('as_of')
        q = (o['quota_general'] or 0) + (o['quota_special'] or 0)
        i = (o['issue_new_general'] or 0) + (o['issue_new_special'] or 0)
        o['quota_total'] = q or None
        o['issue_new_total'] = i or None
        o['execution_pct'] = round(i / q * 100, 1) if q else None
        o['issue_refi_total'] = ((o['issue_refi_general'] or 0) + (o['issue_refi_special'] or 0)) or None
        o['bal_total'] = ((o['bal_general'] or 0) + (o['bal_special'] or 0)) or None
        o['debt_to_gdp_pct'] = (round(o['bal_total'] / o['gdp'] * 100, 1)
                                if o['bal_total'] and o['gdp'] else None)
        # like-for-like year on year: same months of the previous year
        prior = (ytd_meta.get(yr) or {}).get('prior', {}).get(reg)
        o['prior_same_new'] = round(prior, 2) if prior else None
        o['yoy_pct'] = (round(i / prior * 100, 1) if prior and i else None)
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
                    'quota_sourced': sum(1 for r in yrows
                                         if r.get('quota_source') in ('budget-report', 'limit-table')),
                    'quota_disagree': [r['region'] for r in yrows
                                       if r.get('quota_crosscheck') == 'DISAGREE']}
    for r in out:
        r['year_complete'] = comp[r['year']]['complete']

    for yr, mm in ytd_meta.items():
        if yr in comp:
            comp[yr].update({k: v for k, v in mm.items() if k != 'prior'})
    json.dump({'unit': '亿元', 'source': 'celma.org.cn', 'completeness': comp, 'rows': out},
              open(D + 'prov_panel.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    cols = (['region', 'code', 'year', 'basis', 'ytd_through', 'prior_same_new', 'yoy_pct',
             'year_complete',
             'issue_source', 'quota_source', 'quota_verification', 'quota_as_of', 'quota_crosscheck',
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
              f"{(' | YTD thru ' + c['ytd_through']) if c.get('ytd_through') else ''}"
              f" | new-bond {c['region_sum']:>10,.0f}"
              f" vs national {c['national']:>10,.0f}"
              f"  {'complete' if c['complete'] else 'PARTIAL'}")


if __name__ == '__main__':
    main()
