#!/usr/bin/env python3
"""
Province-level local-government bond issuance, from the 发行明细表 appendix of the
Debt Center's monthly 地方政府债券市场报告.

The report's own by-province table (表2) and the YTD chart (图3) are images in the
PDF and carry no extractable text. The appendix behind them lists every single
bond -- name, issue date, maturity, size, tenor, coupon -- so the province split is
rebuilt by classifying each bond from its name and adding them up.

    python3 scripts/parse_prov_bonds.py [year]   ->  data/mof-research-reports/prov_bonds.json

Needs pdftotext (poppler) and the PDFs under data/mof-research-reports/files/,
which are gitignored; re-download with fetch_bonds.py if absent.
"""
import json, os, re, subprocess, sys, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
DIR = BASE + 'data/mof-research-reports/'

# The 36 issuers: 31 provinces + 5 计划单列市 + the XPCC. Order matters -- longer
# names first so 新疆生产建设兵团 is not swallowed by 新疆维吾尔自治区.
REGIONS = [
 ('新疆生产建设兵团','XPCC','新疆生产建设兵团'),
 ('新疆维吾尔自治区','XJ','新疆'), ('宁夏回族自治区','NX','宁夏'),
 ('广西壮族自治区','GX','广西'), ('内蒙古自治区','NM','内蒙古'),
 ('西藏自治区','XZ','西藏'),
 ('黑龙江省','HL','黑龙江'), ('北京市','BJ','北京'), ('天津市','TJ','天津'),
 ('河北省','HE','河北'), ('山西省','SX','山西'), ('辽宁省','LN','辽宁'),
 ('吉林省','JL','吉林'), ('上海市','SH','上海'), ('江苏省','JS','江苏'),
 ('浙江省','ZJ','浙江'), ('安徽省','AH','安徽'), ('福建省','FJ','福建'),
 ('江西省','JX','江西'), ('山东省','SD','山东'), ('河南省','HA','河南'),
 ('湖北省','HB','湖北'), ('湖南省','HN','湖南'), ('广东省','GD','广东'),
 ('海南省','HI','海南'), ('重庆市','CQ','重庆'), ('四川省','SC','四川'),
 ('贵州省','GZ','贵州'), ('云南省','YN','云南'), ('陕西省','SN','陕西'),
 ('甘肃省','GS','甘肃'), ('青海省','QH','青海'),
 ('大连市','DL','大连'), ('宁波市','NB','宁波'), ('厦门市','XM','厦门'),
 ('青岛市','QD','青岛'), ('深圳市','SZ','深圳'),
]
EN = {'XPCC':'Xinjiang Corps','XJ':'Xinjiang','NX':'Ningxia','GX':'Guangxi','NM':'Inner Mongolia',
 'XZ':'Tibet','HL':'Heilongjiang','BJ':'Beijing','TJ':'Tianjin','HE':'Hebei','SX':'Shanxi',
 'LN':'Liaoning','JL':'Jilin','SH':'Shanghai','JS':'Jiangsu','ZJ':'Zhejiang','AH':'Anhui',
 'FJ':'Fujian','JX':'Jiangxi','SD':'Shandong','HA':'Henan','HB':'Hubei','HN':'Hunan',
 'GD':'Guangdong','HI':'Hainan','CQ':'Chongqing','SC':'Sichuan','GZ':'Guizhou','YN':'Yunnan',
 'SN':'Shaanxi','GS':'Gansu','QH':'Qinghai','DL':'Dalian','NB':'Ningbo','XM':'Xiamen',
 'QD':'Qingdao','SZ':'Shenzhen'}
# 计划单列市 are reported separately from their province
PARENT = {'DL':'LN','NB':'ZJ','XM':'FJ','QD':'SD','SZ':'GD'}

ROW = re.compile(r'^\s*(\d{1,4})\s+(.+?)\s+(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})\s+'
                 r'([\d,]+\.\d+)\s+(\d+)\s+([\d.]+)\s*$')

def region_of(name):
    flat = name.replace(' ', '')
    for cn, code, _ in REGIONS:
        if cn in flat: return code
    return None

def classify(name):
    flat = name.replace(' ', '')
    kind = 'refi' if '再融资' in flat else 'new'
    if '专项债' in flat: typ = 'special'
    elif '一般债' in flat: typ = 'general'
    else: typ = None
    # NOTE: the bonds that replace hidden debt are issued as ordinary
    # 再融资专项债券 and are not distinguishable by name, so they cannot be
    # separated from refinancing that rolls maturing bonds. refi_special is the
    # upper bound on the swap.
    return kind, typ

def rows_from_pdf(pdf):
    txt = subprocess.run(['pdftotext', '-layout', pdf, '-'],
                         capture_output=True, text=True).stdout
    i = txt.find('附表')
    if i < 0: return []
    out = []
    # A long bond name wraps onto the following lines; the province can sit there
    # (e.g. 雄安新区建设一般债券(一期)-2025年河北省政府一般债券), so continuation
    # lines are folded back into the name of the row they belong to.
    for line in txt[i:].splitlines():
        m = ROW.match(line)
        if m:
            seq, name, d0, d1, amt, tenor, rate = m.groups()
            out.append({'name': name.strip(), 'issued': d0, 'matures': d1,
                        'amt': float(amt.replace(',', '')), 'tenor': int(tenor), 'rate': float(rate)})
            continue
        if not out: continue
        t = line.strip()
        # continuation: has Chinese, no dates, not a page number or table header
        if (t and not re.search(r'\d{4}-\d{2}-\d{2}', t) and re.search(r'[\u4e00-\u9fff]', t)
                and not re.match(r'^\d+$', t) and '债券名称' not in t and '发行日期' not in t
                and '附表' not in t and '发行明细表' not in t):
            out[-1]['name'] += t
    return out

def main(year=2025):
    cat = json.load(open(DIR + 'catalog.json'))
    months = {}
    for c in cat:
        m = re.search(r'地方政府债券市场报告（(\d{4})年(\d{1,2})月）', c['title'])
        if m and int(m.group(1)) == year:
            p = DIR + c['file']
            if os.path.exists(p): months[int(m.group(2))] = p
    if not months:
        sys.exit(f'no {year} report PDFs under {DIR}files/ (gitignored; run fetch_bonds.py)')

    bonds, missing = [], []
    for mo in sorted(months):
        rs = rows_from_pdf(months[mo])
        for r in rs:
            code = region_of(r['name'])
            if code is None:
                missing.append(r['name']); continue
            kind, typ = classify(r['name'])
            r.update(month=mo, region=code, kind=kind, type=typ)
            bonds.append(r)
        print(f'  {year}-{mo:02d}: {len(rs):4d} bonds, {sum(x["amt"] for x in rs):>10,.2f} 亿元')

    agg = collections.defaultdict(lambda: collections.defaultdict(float))
    for b in bonds:
        a = agg[b['region']]
        a['total'] += b['amt']
        a[b['kind']] += b['amt']
        if b['type']: a[b['kind'] + '_' + b['type']] += b['amt']
        a['n'] += 1
        a['_wr'] += b['amt'] * b['rate']; a['_wt'] += b['amt'] * b['tenor']
    out = []
    for code, a in agg.items():
        out.append({'region': code, 'en': EN[code],
                    'cn': next(c for c, k, _ in REGIONS if k == code),
                    'parent': PARENT.get(code),
                    'n': int(a['n']),
                    'total': round(a['total'], 2),
                    'new': round(a['new'], 2), 'refi': round(a['refi'], 2),
                    'new_general': round(a['new_general'], 2), 'new_special': round(a['new_special'], 2),
                    'refi_general': round(a['refi_general'], 2), 'refi_special': round(a['refi_special'], 2),
                    'avg_rate': round(a['_wr'] / a['total'], 3) if a['total'] else None,
                    'avg_tenor': round(a['_wt'] / a['total'], 2) if a['total'] else None})
    out.sort(key=lambda r: -r['total'])

    monthly = collections.defaultdict(lambda: collections.defaultdict(float))
    for b in bonds:
        monthly[(b['region'], b['month'])]['total'] += b['amt']
        monthly[(b['region'], b['month'])][b['kind']] += b['amt']
    mo_out = [{'region': k[0], 'month': k[1], 'total': round(v['total'], 2),
               'new': round(v['new'], 2), 'refi': round(v['refi'], 2)}
              for k, v in sorted(monthly.items())]

    doc = {'year': year, 'unit': '亿元',
           'source': 'Debt Center 地方政府债券市场报告, 发行明细表 appendix, monthly',
           'months_covered': sorted(months), 'bond_count': len(bonds),
           'total': round(sum(b['amt'] for b in bonds), 2),
           'by_region': out, 'by_region_month': mo_out}
    json.dump(doc, open(DIR + f'prov_bonds_{year}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'\n  prov_bonds_{year}.json: {len(bonds)} bonds, {len(out)} regions, '
          f'{doc["total"]:,.2f} 亿元')
    if missing:
        print(f'  WARNING unclassified: {len(missing)}')
        for n in missing[:5]: print('   ', n)

if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2025)
