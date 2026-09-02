#!/usr/bin/env python3
"""Extract the four budget accounts' annual totals from the MOF annual reports.

The monthly 全国财政收支情况 releases cover only the general public budget and the
government-managed fund. The state-capital-operations and social-insurance accounts
appear only in the annual (full-year) edition, so they are parsed separately here.

Writes data/mof-reports/accounts_annual.json.
"""
import os, re, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
TXT  = BASE + 'data/mof-reports/text/'

def val(t, kw):
    m = re.search(kw + r'\s*([\d.]+)\s*亿元([^。]*)', t)
    if not m:
        return None
    g = re.search(r'(增长|下降)\s*([\d.]+)%', m.group(2))
    return {'v': float(m.group(1)),
            'g': (float(g.group(2)) * (-1 if g.group(1) == '下降' else 1)) if g else None}

def main():
    rows = []
    for f in sorted(os.listdir(TXT)):
        t = open(TXT + f, encoding='utf-8').read().replace('—', '-')
        title = t.split('\n', 1)[0].strip()
        m = re.match(r'(\d{4})年财政收支情况', title)
        if not m:
            continue
        y = int(m.group(1))
        rec = {'year': y, 'title': title,
               'gpb_exp':  val(t, r'全国一般公共预算支出'),
               'gmf_exp':  val(t, r'全国政府性基金预算支出'),
               'sco_exp':  val(t, r'全国国有资本经营预算支出'),
               'sco_exp_central': val(t, r'中央国有资本经营预算本级支出'),
               'sco_exp_local':   val(t, r'地方国有资本经营预算支出'),
               'sif_exp':  val(t, r'全国社会保险基金预算支出'),
               'sif_rev':  val(t, r'全国社会保险基金预算收入')}
        if any(rec[k] for k in ('gpb_exp', 'sco_exp', 'sif_exp')):
            rows.append(rec)
    rows.sort(key=lambda r: r['year'])
    json.dump(rows, open(BASE + 'data/mof-reports/accounts_annual.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    print(f'  accounts_annual.json: {len(rows)} years {rows[0]["year"]}..{rows[-1]["year"]}')
    for r in rows[-6:]:
        g = lambda k: f"{r[k]['v']:>9,.0f}" if r.get(k) else '        -'
        print(f"    {r['year']}  GPB {g('gpb_exp')}  GMF {g('gmf_exp')}  SCO {g('sco_exp')}  SIF {g('sif_exp')}")
    return rows

if __name__ == '__main__':
    print('Parsing four-account annual totals ...')
    main()
