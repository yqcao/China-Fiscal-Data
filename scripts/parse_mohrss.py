#!/usr/bin/env python3
"""Parse the archived MOHRSS monthly statistics into data/mohrss/mohrss_series.json.

Source: 人力资源和社会保障部 · 数字人社 · 统计数据
        https://www.mohrss.gov.cn/SYrlzyhshbzb/zwgk/szrs/tjsj/

Collection is browser-assisted (the site sits behind a JS bot challenge that plain
HTTP clients cannot satisfy) — see README. This script only parses what is already
archived under data/mohrss/files/, so it is safe to re-run at any time.

Two eras, two formats:
  2013-01 .. 2019-12   legacy binary .xls  (needs `xlrd`; skipped with a warning if absent)
  2020-01 .. present   PDF                 (needs `pdftotext`, from poppler)

The row *numbering* shifts between releases — the 技师/职业技能等级证书 row appears only
in some editions, pushing every later index down — so nothing is keyed off 序号. Uniquely
named indicators are matched by label; the four insurance schemes are matched by the fixed
order in which their (参保人数, 基金收入, 基金支出) triplets appear.
"""
import os, re, glob, json, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
DIR  = BASE + 'data/mohrss/'
FILES = DIR + 'files/'

UNITS = '万人次|万人|亿元|万件|万户|万元|%'
ROW   = re.compile(r'(?<!\d)(\d{1,2})\s+(.*?)\s\s+(' + UNITS + r')\s+([\d,]+\.?\d*)\s*$')

# The four schemes carried by the PDF era (2020-), in the fixed order their
# (参保人数, 基金收入, 基金支出) triplets appear in the table.
SCHEMES = ['pension_urban', 'pension_rural', 'ui', 'injury']
# The xls era additionally carries medical and maternity insurance. Both leave the
# table when their administration moves out of MOHRSS: 医疗保险 to the new 国家医保局
# (last seen 2018), 生育保险 merged into medical insurance (last seen 2018).
ALL_SCHEMES = SCHEMES + ['medical', 'maternity']

LABEL_FIX = {
    '就业困难人员就业': '就业困难人员就业人数',
    '基本医疗保险基金总收入': '基金收入',
    '基本医疗保险基金支出': '基金支出',
    '主动监察用人单位户数': '主动检查用人单位户数',
}

def norm(lab):
    lab = re.sub(r'[（(][^）)]*[）)]', '', lab or '').strip()   # drop 「（6月份）」 etc.
    lab = lab.rstrip('*').strip()
    # exact fix-ups first: the generic 基金总收入 rewrite below would otherwise mangle
    # 「基本医疗保险基金总收入」 into a label this table never uses.
    lab = LABEL_FIX.get(lab, lab)
    return lab.replace('期末参保人数', '参保人数').replace('基金总收入', '基金收入')

def to_num(s):
    try:
        return round(float(str(s).replace(',', '')), 4)
    except (TypeError, ValueError):
        return None

# ---------------------------------------------------------------- extractors
def rows_from_pdf(path):
    """-> [(idx, label, unit, value)] in table order."""
    txt = subprocess.run(['pdftotext', '-layout', path, '-'],
                         capture_output=True, text=True).stdout
    out, seen = [], set()
    for ln in txt.split('\n'):
        m = ROW.search(ln.rstrip())
        if not m:
            continue
        idx, lab, unit, val = m.groups()
        idx = int(idx)
        if idx in seen:              # later pages repeat nothing, but be safe
            continue
        seen.add(idx)
        lab = re.sub(r'^[一-鿿]{0,8}\s+', '', lab).strip()   # strip vertical group text
        out.append((idx, norm(lab), unit, to_num(val)))
    return sorted(out)

def rows_from_xls(path):
    """-> [(idx, label, unit, value, group)] in table order."""
    import xlrd
    sh = xlrd.open_workbook(path).sheet_by_index(0)
    out, grp = [], ''
    for r in range(sh.nrows):
        c = [str(sh.cell_value(r, i)).strip() for i in range(sh.ncols)]
        if c and c[0]:
            grp = c[0].replace('\n', '')
        if len(c) < 5:
            continue
        try:
            idx = int(float(c[1]))
        except ValueError:
            continue
        out.append((idx, norm(c[2]), c[3], to_num(c[4]), grp))
    return out

# ---------------------------------------------------------------- assembling
GROUP_KEY = {'城镇职工基本养老保险': 'pension_urban',
             '城乡居民基本养老保险': 'pension_rural',
             '城乡居民社会养老保险': 'pension_rural',      # 2013 naming
             '失业保险': 'ui', '工伤保险': 'injury',
             '医疗保险': 'medical', '基本医疗保险': 'medical',
             '生育保险': 'maternity'}
SIMPLE = {'城镇新增就业人数': 'emp_new', '城镇失业人员再就业人数': 'emp_reemp',
          '就业困难人员就业人数': 'emp_hard', '城镇调查失业率': 'unemp_survey',
          '期末城镇登记失业率': 'unemp_registered', '城镇登记失业率': 'unemp_registered',
          '立案受理案件总数': 'disp_cases', '立案受理案件涉及劳动者人数': 'disp_workers',
          '当期审结案件数': 'disp_concluded', '劳动保障监察案件结案数': 'insp_closed',
          '主动检查用人单位户数': 'insp_checked', '督促补签劳动合同': 'insp_contracts',
          '追发工资等待遇金额': 'insp_wages', '督促缴纳社会保险费金额': 'insp_siprem'}
TRIPLE = {'参保人数': 'insured', '基金收入': 'rev', '基金支出': 'exp'}

def build(period, rows, src):
    rec = {'period': period, 'year': int(period[:4]), 'month': int(period[5:]), 'src': src}
    for k in SIMPLE.values():
        rec[k] = None
    rec['skill_certs'] = None
    for s in ALL_SCHEMES:
        for f in TRIPLE.values():
            rec[f'{s}_{f}'] = None

    order = []          # scheme slots discovered in table order (PDF path)
    for row in rows:
        if src == 'xls':
            idx, lab, unit, val, grp = row
            scheme = GROUP_KEY.get(grp)
        else:
            idx, lab, unit, val = row
            scheme = None

        if lab in SIMPLE:
            rec[SIMPLE[lab]] = val
            continue
        if unit == '万人次' or '技师' in lab or '获证' in lab:
            rec['skill_certs'] = val
            continue
        if lab in TRIPLE:
            if src == 'pdf':
                if lab == '参保人数':          # a 参保人数 row opens each scheme block
                    order.append(len(order))
                slot = len(order) - 1
                scheme = SCHEMES[slot] if 0 <= slot < len(SCHEMES) else None
            if scheme:
                rec[f'{scheme}_{TRIPLE[lab]}'] = val
    # derived: fund balance for each scheme
    for s in ALL_SCHEMES:
        r, e = rec[f'{s}_rev'], rec[f'{s}_exp']
        rec[f'{s}_bal'] = round(r - e, 4) if (r is not None and e is not None) else None
    return rec

def main():
    cat = {c['period']: c for c in json.load(open(DIR + 'catalog.json'))}
    have_xlrd = True
    try:
        import xlrd  # noqa: F401
    except ImportError:
        have_xlrd = False

    # Anything we cannot re-parse on this machine is carried over from the previous
    # run rather than dropped, so running without xlrd does not silently destroy the
    # 2013-2019 half of the series.
    prev_path = DIR + 'mohrss_series.json'
    prev = {}
    if os.path.exists(prev_path):
        prev = {r['period']: r for r in json.load(open(prev_path))}

    out, skipped, kept = [], 0, 0
    for path in sorted(glob.glob(FILES + 'mohrss_*')):
        base = os.path.basename(path)
        period = base[7:14]
        if path.endswith('.pdf'):
            rec = build(period, rows_from_pdf(path), 'pdf')
        else:
            if not have_xlrd:
                skipped += 1
                if period in prev:
                    out.append(prev[period]); kept += 1
                continue
            rec = build(period, rows_from_xls(path), 'xls')
        c = cat.get(period, {})
        rec['title'] = c.get('title')
        rec['url'] = c.get('article')
        out.append(rec)
    out.sort(key=lambda r: r['period'])
    json.dump(out, open(DIR + 'mohrss_series.json', 'w'), ensure_ascii=False,
              separators=(',', ':'))
    span = f"{out[0]['period']}..{out[-1]['period']}" if out else '-'
    print(f'  mohrss_series.json: {len(out)} months {span}')
    if skipped:
        print(f'  NOTE: xlrd not installed — {skipped} legacy .xls files not re-parsed'
              f' ({kept} carried over from the previous run). `pip install xlrd` to rebuild them.')
    return out

if __name__ == '__main__':
    print('Parsing MOHRSS monthly statistics ...')
    main()
