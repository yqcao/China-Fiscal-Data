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
"""
import json, os, csv, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
D = BASE + 'data/celma/'

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


def main():
    rows = json.load(open(D + 'annual_by_region.json'))
    nat = collections.defaultdict(dict)
    for r in json.load(open(D + 'annual_national.json')):
        nat[r['year']][r['zb_name']] = r['amount']

    cell = collections.defaultdict(dict)
    code = {}
    for r in rows:
        cell[(r['region'], r['year'])][r['zb_name']] = r['amount']
        code[r['region']] = r['code']

    out = []
    for (reg, yr), d in sorted(cell.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        o = {'region': reg, 'code': code[reg], 'year': yr}
        for key, cn in FIELDS:
            o[key] = d.get(cn)
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
        comp[yr] = {'regions': sum(1 for r in out if r['year'] == yr),
                    'region_sum': round(got, 2), 'national': round(want, 2),
                    'complete': bool(want) and abs(got - want) < max(1.0, want * 0.001)}
    for r in out:
        r['year_complete'] = comp[r['year']]['complete']

    json.dump({'unit': '亿元', 'source': 'celma.org.cn', 'completeness': comp, 'rows': out},
              open(D + 'prov_panel.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    cols = (['region', 'code', 'year', 'year_complete', 'quota_total', 'issue_new_total',
             'execution_pct', 'issue_refi_total', 'bal_total', 'debt_to_gdp_pct']
            + [k for k, _ in FIELDS])
    with open(D + 'prov_panel.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in out: w.writerow(r)
    print(f'  prov_panel.json / .csv: {len(out)} region-years')
    for yr, c in comp.items():
        print(f"    {yr}  {c['regions']:2d} regions  new-bond issuance {c['region_sum']:>10,.0f} "
              f"vs national {c['national']:>10,.0f}  {'complete' if c['complete'] else 'PARTIAL'}")


if __name__ == '__main__':
    main()
