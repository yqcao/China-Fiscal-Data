"""Build data/imf-china/catalog.json and INDEX.md.

The IMF's official documents on the People's Republic of China (mainland) since
October 2021: Article IV staff reports, Selected Issues, FSAP reports, technical
assistance reports and a departmental paper, plus the press releases, mission
statements and briefing transcripts that accompany them.

imf.org and the IMF eLibrary both sit behind bot protection, so the files cannot be
fetched unattended. They were collected one by one and saved under files/ (local only,
gitignored: the reports are (c) IMF). This script only records what is there: it reads the
curated list below, adds size, page count and SHA-256 for any local copy, and writes
the catalog. To add a document, append it to DOCS, save its PDF under files/, rerun.
"""
import hashlib
import json
import os
import re
import subprocess

ROOT = os.path.join(os.path.dirname(__file__), '..', 'data', 'imf-china')
IMF = 'https://www.imf.org'
EL = 'https://www.elibrary.imf.org/view/journals'

# kind, number, published, completed (cut-off date stated in the report), title,
# pdf path on imf.org, landing page on imf.org, eLibrary issue page, local file
DOCS = [
    ('Article IV', 'CR 22/21', '2022-01-28', '2021-12-21',
     '2021 Article IV Consultation — Press Release; Staff Report; and Statement by the Executive Director',
     '/-/media/files/publications/cr/2022/english/1chnea2022001.pdf',
     'https://www.imf.org/external/pubs/cat/longres.aspx?sk=512248',
     '002/2022/021/002.2022.issue-021-en.xml', '2022-01-28_CR22-21_2021-article-iv.pdf'),
    ('Selected Issues', 'CR 22/22', '2022-02-04', '2021-12-20',
     'Selected Issues',
     '/-/media/files/publications/cr/2022/english/1chnea2022002.pdf', None,
     '002/2022/022/002.2022.issue-022-en.xml', '2022-02-04_CR22-22_selected-issues.pdf'),
    ('Article IV', 'CR 23/67', '2023-02-03', '2022-12-19',
     '2022 Article IV Consultation — Press Release; Staff Report; and Statement by the Executive Director',
     '/-/media/files/publications/cr/2023/english/1chnea2023001.pdf',
     'https://www.imf.org/en/Publications/CR/Issues/2023/02/02/Peoples-Republic-of-China-2022-Article-IV-Consultation-Press-Release-Staff-Report-and-529067',
     '002/2023/067/002.2023.issue-067-en.xml', '2023-02-03_CR23-67_2022-article-iv.pdf'),
    ('Selected Issues', 'CR 23/81', '2023-02-10', '2022-12-19',
     'Selected Issues',
     '/-/media/files/publications/cr/2023/english/1chnea2023002.pdf', None,
     '002/2023/081/002.2023.issue-081-en.xml', '2023-02-10_CR23-81_selected-issues.pdf'),
    ('Article IV', 'CR 24/38', '2024-02-02', '2023-12-19',
     '2023 Article IV Consultation — Press Release; Staff Report; and Statement by the Executive Director',
     '/-/media/files/publications/cr/2024/english/1chnea2024001.pdf', None,
     '002/2024/038/002.2024.issue-038-en.xml', '2024-02-02_CR24-38_2023-article-iv.pdf'),
    ('Selected Issues', 'CR 24/50', '2024-02-09', '2023-12-19',
     'Selected Issues',
     '/-/media/files/publications/cr/2024/english/1chnea2024002.pdf', None,
     '002/2024/050/002.2024.issue-050-en.xml', '2024-02-09_CR24-50_selected-issues.pdf'),
    ('Article IV', 'CR 24/258', '2024-08-02', '2024-07-03',
     '2024 Article IV Consultation — Press Release; Staff Report; and Statement by the Executive Director',
     '/-/media/files/publications/cr/2024/english/1chnea2024003-print-pdf.pdf', None,
     '002/2024/258/002.2024.issue-258-en.xml', '2024-08-02_CR24-258_2024-article-iv.pdf'),
    ('Selected Issues', 'CR 24/276', '2024-08-30', '2024-07-03',
     'Selected Issues',
     '/-/media/files/publications/cr/2024/english/1chnea2024004-print-pdf.pdf',
     'https://www.imf.org/en/publications/cr/issues/2024/08/29/peoples-republic-of-china-selected-issues-554232',
     '002/2024/276/002.2024.issue-276-en.xml', '2024-08-30_CR24-276_selected-issues.pdf'),
    ('FSAP', 'CR 25/100', '2025-04-30', '2025-02-04',
     'Financial Sector Assessment Program — Financial System Stability Assessment; Press Release; Staff Report; and Statement by the Executive Director',
     '/-/media/files/publications/cr/2025/english/1chnea2025001-print-pdf.pdf',
     'https://www.imf.org/en/publications/cr/issues/2025/04/30/peoples-republic-of-china-financial-sector-assessment-program-financial-system-stability-566570',
     '002/2025/100/002.2025.issue-100-en.xml', '2025-04-30_CR25-100_fsap-fssa.pdf'),
    ('Technical assistance', 'TAR 25/54', '2025-05-09', '2025-01',
     'Technical Assistance Report — Advancing Risk Management for Large Taxpayers (State Taxation Administration; FAD)',
     '/-/media/files/publications/tar/2025/english/tarea2025054-print-pdf.pdf',
     'https://www.imf.org/en/publications/technical-assistance-reports/issues/2025/05/09/people-s-republic-of-china-technical-assistance-report-advancing-risk-management-for-large-566831',
     '019/2025/054/019.2025.issue-054-en.xml', '2025-05-09_TAR25-54_ta-large-taxpayer-risk-management.pdf'),
    ('Technical assistance', 'HLS 25/19', '2025-05-20', '2025-05',
     'High-Level Summary — Advancing Risk Management for Large Taxpayers',
     '/-/media/files/publications/hls/2025/english/hlsea2025019.pdf',
     'https://www.imf.org/en/publications/high-level-summary-technical-assistance-reports/issues/2025/05/20/peoples-republic-of-china-advancing-risk-management-for-large-taxpayers-567045',
     '029/2025/019/029.2025.issue-019-en.xml', '2025-05-20_HLS25-19_summary-large-taxpayer-risk-management.pdf'),
    ('FSAP', 'CR 25/302', '2025-11-14', '2025-10-27',
     'Financial Sector Assessment Program — Technical Note on Anti-Money Laundering/Combating the Financing of Terrorism',
     '/-/media/files/publications/cr/2025/english/1chnea2025002-source-pdf.pdf', None,
     '002/2025/302/002.2025.issue-302-en.xml', '2025-11-14_CR25-302_fsap-tn-aml-cft.pdf'),
    ('FSAP', 'CR 25/303', '2025-11-14', '2025-10-27',
     'Financial Sector Assessment Program — Technical Note on Climate Risk Analysis',
     '/-/media/files/publications/cr/2025/english/1chnea2025003-source-pdf.pdf', None,
     '002/2025/303/002.2025.issue-303-en.xml', '2025-11-14_CR25-303_fsap-tn-climate-risk.pdf'),
    ('Article IV', 'CR 26/44', '2026-02-18', '2026-01-28',
     '2025 Article IV Consultation — Press Release; Staff Report; and Statement by the Executive Director',
     '/-/media/files/publications/cr/2026/english/1chnea2026001-source-pdf.pdf',
     'https://www.imf.org/en/publications/cr/issues/2026/02/17/peoples-republic-of-china-2025-article-iv-consultation-press-release-staff-report-and-574028',
     '002/2026/044/002.2026.issue-044-en.xml', '2026-02-18_CR26-44_2025-article-iv.pdf'),
    ('Technical assistance', 'HLS 26/15', '2026-03-10', '2025-09',
     'High-Level Summary — Structured Approaches to Risk Assessment (State Taxation Administration; FAD)',
     '/-/media/files/publications/hls/2026/english/hlsea2026015.pdf',
     'https://www.imf.org/en/publications/high-level-summary-technical-assistance-reports/issues/2026/03/09/peoples-republic-of-china-structured-approaches-to-risk-assessment-574542',
     '029/2026/015/029.2026.issue-015-en.xml', '2026-03-10_HLS26-15_summary-structured-risk-assessment.pdf'),
    ('Selected Issues', 'CR 26/214', '2026-08-07', '2026-01-28',
     'Selected Issues (background to the 2025 Article IV, published six months after it)',
     '/-/media/files/publications/cr/2026/english/1chnea2026002.pdf',
     'https://www.imf.org/en/publications/cr/issues/2026/08/07/peoples-republic-of-china-selected-issues-578524',
     '002/2026/214/002.2026.issue-214-en.xml', '2026-08-07_CR26-214_selected-issues.pdf'),
    ('Departmental paper', 'DP 26/19', '2026-09-25', None,
     'Local Government Finances in China: Policy Options to Tackle the Debt Overhang (Adams, Ashcroft, Garrido, Hoyle, Jain-Chandra, Rendak et al.)',
     None, None,
     '087/2026/019/087.2026.issue-019-en.xml', '2026-09-25_DP26-19_local-government-finances.html'),
]

# Statements: not archived (imf.org serves them only as web pages; the Board press
# releases are reproduced inside the Article IV reports above). kind, date, number, title, url
NEWS = 'https://www.imf.org/en/news/articles/'
STATEMENTS = [  # dates are each page's publishDate on imf.org
    ('Mission statement', '2021-11-18', 'PR 21/338', 'IMF Staff Completes 2021 Article IV Mission to the People\'s Republic of China',
     '2021/11/18/pr21338-china-imf-staff-completes-2021-article-iv-mission-to-the-peoples-republic-of-china'),
    ('Board conclusion', '2022-01-28', 'PR 22/17', 'IMF Executive Board Concludes 2021 Article IV Consultation with the People\'s Republic of China',
     '2022/01/26/pr2217-imf-executive-board-concludes-2021-article-iv-consultation-with-the-peoples-republic-of-china'),
    ('Briefing transcript', '2022-01-29', '', 'Press Briefing: 2021 China Article IV',
     '2022/01/29/tr012722-press-briefing-2021-china-article-iv'),
    ('Mission statement', '2022-11-23', 'PR 22/401', 'IMF Staff Completes 2022 Article IV Mission to the People\'s Republic of China',
     '2022/11/21/pr22401-imf-staff-completes-2022-article-iv-mission-to-the-peoples-republic-of-china'),
    ('Board conclusion', '2023-02-03', 'PR 23/28', 'IMF Executive Board Concludes 2022 Article IV Consultation with the People\'s Republic of China',
     '2023/02/02/pr2328-imf-executive-board-concludes-2022-article-iv-consultation-with-peoples-republic-of-china'),
    ('Briefing transcript', '2023-02-02', '', 'Transcript of Press Briefing on the 2022 China Article IV Staff Report',
     '2023/02/02/tr020223-transcript-of-press-briefing-on-the-2022-china-article-iv-staff-report'),
    ('Mission statement', '2023-11-07', 'PR 23/380', 'IMF Staff Completes 2023 Article IV Mission to the People\'s Republic of China',
     '2023/11/07/pr23380-imf-staff-completes-2023-article-iv-mission-to-the-peoples-republic-of-china'),
    ('Board conclusion', '2024-02-02', 'PR 24/33', 'IMF Executive Board Concludes 2023 Article IV Consultation with the People\'s Republic of China',
     '2024/02/01/pr2433-china-imf-executive-board-concludes-2023-article-iv-consultation'),
    ('Mission statement', '2024-05-29', 'PR 24/184', 'IMF Staff Completes 2024 Article IV Mission to the People\'s Republic of China',
     '2024/05/28/pr24184-china-imf-staff-completes-2024-art-iv-mission'),
    ('Briefing transcript', '2024-05-30', '', 'Transcript of Press Briefing on China Article IV Consultation',
     '2024/05/30/tr052924-transcript-of-press-briefing-on-china-article-iv-consultation'),
    ('Board conclusion', '2024-08-02', 'PR 24/295', 'IMF Executive Board Concludes 2024 Article IV Consultation with the People\'s Republic of China',
     '2024/07/31/pr24295-china-imf-exec-board-concludes-2024-art-iv-consult'),
    ('Board conclusion', '2025-04-04', 'PR 25/090', 'IMF Executive Board Concludes 2024 Financial System Stability Assessment with the People\'s Republic of China',
     '2025/04/04/pr25090-china-imf-executive-board-concludes-2024-financial-system-stability-assessment'),
    ('Mission statement', '2025-12-10', 'PR 25/415', 'IMF Staff Completes 2025 Article IV Mission to the People\'s Republic of China',
     '2025/12/10/pr-25415-china-imf-staff-completes-2025-article-iv-mission-to-the-peoples-republic-of-china'),
    ('Briefing transcript', '2025-12-12', '', 'Press Briefing Transcript: China Article IV Consultation',
     '2025/12/12/tr-12-11-25-press-briefing-on-china-article-iv-consultation-transcript'),
    ('Board conclusion', '2026-02-18', 'PR 26/053', 'IMF Executive Board Concludes 2025 Article IV Consultation with China',
     '2026/02/18/pr-26053-china-imf-executive-board-concludes-2025-article-iv-consultation'),
]


# imf.org catalogue ids (from RePEc's IMF Country Reports series); the IMF keeps
# longres.aspx?sk=<id> as a permanent redirect to each report's page.
SK = {'CR 22/21': '512248', 'CR 22/22': '512253', 'CR 23/67': '529067', 'CR 23/81': '529473', 'CR 24/38': '544379', 'CR 24/50': '544651', 'CR 24/258': '552803', 'CR 24/276': '554232', 'CR 25/100': '566570', 'CR 25/302': '571842', 'CR 25/303': '571847', 'CR 26/44': '574028', 'CR 26/214': '578524'}


def file_stats(name):
    path = os.path.join(ROOT, 'files', name)
    if not os.path.exists(path):
        return {'local': False}
    data = open(path, 'rb').read()
    out = {'local': True, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if name.endswith('.pdf'):
        try:
            info = subprocess.run(['pdfinfo', path], capture_output=True, text=True).stdout
            m = re.search(r'^Pages:\s+(\d+)', info, re.M)
            out['pages'] = int(m.group(1)) if m else None
        except FileNotFoundError:
            pass
    return out


def main():
    docs = []
    for kind, num, pub, done, title, pdf, landing, el, fname in DOCS:
        d = {'kind': kind, 'number': num, 'published': pub, 'completed': done, 'title': title,
             'pdf_url': IMF + pdf if pdf else None,
             'landing_url': landing or (f'{IMF}/external/pubs/cat/longres.aspx?sk={SK[num]}' if num in SK else None),
             'elibrary_url': f'{EL}/{el}', 'file': f'files/{fname}'}
        d.update(file_stats(fname))
        docs.append(d)
    stm = [{'kind': k, 'date': dt, 'number': n or None, 'title': t, 'url': NEWS + p}
           for k, dt, n, t, p in STATEMENTS]
    json.dump({'documents': docs, 'statements': stm},
              open(os.path.join(ROOT, 'catalog.json'), 'w'), ensure_ascii=False, indent=1)

    local = [d for d in docs if d['local']]
    mb = sum(d['bytes'] for d in local) / 1e6
    pages = sum(d.get('pages') or 0 for d in local)
    L = ['# IMF official documents on China, October 2021 – October 2026', '',
         'People\'s Republic of China (mainland). Sources: [imf.org](https://www.imf.org/en/countries/chn) '
         'and the [IMF eLibrary](https://www.elibrary.imf.org/).', '',
         f'{len(docs)} documents ({len(local)} held locally, {pages:,} PDF pages, {mb:.1f} MB) and '
         f'{len(stm)} press releases, mission statements and briefing transcripts.', '',
         '**The files are local only.** IMF reports are © International Monetary Fund, so `files/` '
         '(the PDFs) and `text/` (`pdftotext -layout` extractions for searching) are gitignored. '
         'Each row links the IMF\'s own PDF. imf.org and the eLibrary both sit behind bot protection, '
         'so no script in this repo downloads them; the copies were collected one at a time and checked '
         'against the report number on each cover. `scripts/build_imf_china_index.py` rebuilds this '
         'index and `catalog.json` (size, pages, SHA-256) from whatever is in `files/`.', '',
         '**Scope.** Included: Article IV staff reports, Selected Issues, FSAP reports, technical '
         'assistance reports and summaries, and departmental papers whose subject is mainland China. '
         'Excluded: IMF Working Papers (staff research that carries the disclaimer that it does not '
         'represent IMF views), multi-country reports such as the WEO, and the separate Hong Kong SAR '
         'and Macao SAR reports.', '',
         '## Documents', '',
         '| Published | No. | Type | Title | Completed | Pages | Local file | Source |',
         '|---|---|---|---|---|---|---|---|']
    for d in sorted(docs, key=lambda x: x['published'], reverse=True):
        src = []
        if d['pdf_url']: src.append(f"[PDF]({d['pdf_url']})")
        if d['landing_url']: src.append(f"[page]({d['landing_url']})")
        src.append(f"[eLibrary]({d['elibrary_url']})")
        L.append(f"| {d['published']} | {d['number']} | {d['kind']} | {d['title']} | {d['completed'] or '—'} | "
                 f"{d.get('pages') or '—'} | `{d['file']}` | {' · '.join(src)} |")
    L += ['', '*Completed* is the date each report says its information was cut off; for the '
          'technical-assistance reports it is the cover date.', '',
          'The departmental paper has no PDF link: its imf.org page could not be located, and the '
          'eLibrary serves its PDF only behind a browser challenge. The local copy is the eLibrary\'s '
          'full-text HTML page.', '',
          '## Press releases, mission statements and briefings', '',
          'Listed, not archived: imf.org serves these only as web pages. The Board press releases are '
          'also reproduced at the front of the matching Article IV report above.', '',
          '| Date | No. | Type | Title |', '|---|---|---|---|']
    for s in sorted(stm, key=lambda x: x['date'], reverse=True):
        L.append(f"| {s['date']} | {s['number'] or '—'} | {s['kind']} | [{s['title']}]({s['url']}) |")
    open(os.path.join(ROOT, 'INDEX.md'), 'w').write('\n'.join(L) + '\n')
    print(f'{len(docs)} documents ({len(local)} local, {pages} pages, {mb:.1f} MB), {len(stm)} statements')


if __name__ == '__main__':
    main()
