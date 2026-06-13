#!/usr/bin/env python3
"""Prototype: province-level government investment / guidance fund scale, pulled
from OFFICIAL government disclosures (财政厅公告 / 发布会吹风会 / 官方媒体转载 /
财政部专题 / 政府工作报告), with the exact quoted sentence and a source URL for
every figure.

Why this layer exists: AMAC has no fund size and a name filter finds only ~200
self-identified funds; the curated major_funds list is fund-by-fund. This file
answers the *province aggregate* question ("本省产业基金规模有多大") directly.

WHAT THE 3-PROVINCE PROBE FOUND (广东 / 浙江 / 安徽) — the recipe & its limits:
  * The aggregate IS disclosed officially and is high quality.
  * It almost never lives in a clean "政府投资基金信息公开专栏" table — czt.*.gov.cn
    column pages frequently 403/503. The numbers surface in: ① 财政厅 fund-manager
    遴选公告 (which embed a 基金概况 paragraph), ② 财政厅/政府 发布会吹风会 readouts,
    ③ 官方媒体 (浙江日报/安徽日报) republished on *.gov.cn subdomains, ④ 财政部 features.
  * 政府工作报告 itself is mostly QUALITATIVE / forward-looking — it gives plans
    and completion counts, NOT cumulative stock. So the user's original hypothesis
    holds only weakly: read the 财政厅 channel, not the 工作报告.
  * 口径 is wildly mixed and MUST be tagged per figure: 认缴 / 实缴 / 撬动后(社会资本)
    / 目标 / 投放(投资额) / 只数. Never sum across 口径 or across 母/子 levels.
  => Verdict: viable as a *curated, semi-structured* per-province source (a sources.json
     recipe like fetch_guidance_rules.py + verbatim-quote extraction + human check),
     NOT a clean auto-scrape. This script is the data model + a 3-province seed.

Unit: 亿元 (RMB 100M). 10000亿 = 1万亿. Append rows / provinces and re-run.
Each row's `quote` is the verbatim official sentence — the ground truth for its number.
"""
import os, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'govt-guidance-funds')

# basis tags: 认缴 | 实缴 | 撬动 (社会资本) | 目标 | 投放 (累计投资额) | 只数
# headline=True marks the single best current province-aggregate disclosure.
ROWS = [
 # ---- 广东 ----
 dict(province='广东', report_date='2025-05', year=2024, headline=True,
      metric='全省政府投资基金存量(认缴/实缴)', basis='认缴+实缴', value_yi=17700, paidin_yi=12400, count=155,
      quote='截至2024年底，全省政府投资基金155支，基金认缴总规模1.77万亿元、已实缴1.24万亿元。',
      report='广东省财政厅新闻发布会(副厅长胡建斌)', source='https://czt.gd.gov.cn/tpxw/content/post_4710306.html'),
 dict(province='广东', report_date='2025-04', year=2025, headline=False,
      metric='全省产业+创业投资基金总规模目标', basis='目标', value_yi=10000, paidin_yi=None, count=None,
      quote='全省统筹资源整合组建超万亿元总规模的产业投资基金和创业投资基金，其中省级基金规模超过1000亿元。',
      report='《广东省进一步激发市场主体活力加快建设现代化产业体系的若干措施》',
      source='https://www.gd.gov.cn/zwgk/zcjd/mtjd/content/post_4705683.html'),
 dict(province='广东', report_date='2025-12', year=2025, headline=False,
      metric='广东省战略性新兴产业投资引导基金', basis='认缴', value_yi=1000, paidin_yi=500, count=1,
      quote='广东省战略性新兴产业投资引导基金有限责任公司注册资本500亿元，计划总规模达到1000亿元。',
      report='广东战新引导基金成立公告', source='https://finance.sina.com.cn/roll/2025-12-22/doc-inhcryri4636444.shtml'),

 # ---- 浙江 ----
 dict(province='浙江', report_date='2025-06', year=2025, headline=True,
      metric='省产业基金累计(认缴/撬动)', basis='认缴', value_yi=600, paidin_yi=600, count=117,
      quote='省产业基金通过循环投资累计认缴近600亿元，累计投资省内项目超1600个，撬动各类资本5459亿元。',
      report='《浙江产业基金壮大"耐心资本"》(浙江日报，载于 zjic.zj.gov.cn)',
      source='https://zjic.zj.gov.cn/ywdh/tzgl/202506/t20250613_23507148.shtml'),
 dict(province='浙江', report_date='2025-12', year=2025, headline=False,
      metric='"4+1"专项基金群', basis='只数', value_yi=700, paidin_yi=None, count=17,
      quote='组建了17支总规模超700亿元的"4+1"专项基金，已投资项目超400个、投资金额近400亿元。',
      report='《为创新浙江注入耐心资本》(浙江日报，载于 zjic.zj.gov.cn)',
      source='https://zjic.zj.gov.cn/ywdh/qyfz/202512/t20251202_23837981.shtml'),
 dict(province='浙江', report_date='2023-09', year=2023, headline=False,
      metric='省产业基金累计(认缴/撬动)', basis='认缴', value_yi=400, paidin_yi=400, count=99,
      quote='截至2023年6月末，省产业基金累计认缴近400亿元，累计参股基金99支，合作机构超80家，引导撬动社会资本近4000亿元。',
      report='浙江省产业基金管理机构遴选公告(czt.zj.gov.cn)',
      source='https://czt.zj.gov.cn/art/2023/9/22/art_1164164_58927426.html'),
 dict(province='浙江', report_date='2025-01', year=2024, headline=False,
      metric='政府工作报告(完成只数，定性)', basis='只数', value_yi=None, paidin_yi=None, count=17,
      quote='完成17支"4+1"专项基金组建。',
      report='浙江省2025年《政府工作报告》', source='https://jxt.zj.gov.cn/art/2025/1/21/art_1660147_58933630.html'),

 # ---- 安徽 ----
 dict(province='安徽', report_date='2025-12', year=2025, headline=True,
      metric='全省政府性股权投资基金体系', basis='实缴', value_yi=3000, paidin_yi=927, count=214,
      quote='全省政府性股权投资基金体系总规模已超过3000亿元，其中16只母基金共设立子基金198只，母子基金累计实缴规模达927亿元，省财政出资144.68亿元，撬动社会资本782.32亿元，撬动比例达到5.41倍。',
      report='安徽省政府新闻发布会(2025年末数据，财联社/科创板日报转述)', source='https://www.cls.cn/detail/2383311'),
 dict(province='安徽', report_date='2024-10', year=2024, headline=False,
      metric='省新兴产业引导基金16只母基金', basis='认缴', value_yi=1800, paidin_yi=None, count=16,
      quote='省本级16只母基金已经组建完成，总的认缴规模已经接近1800亿元，母子基金数将近200个。',
      report='财政部《一场"破"与"立"的改革》(引省财政厅官员)',
      source='https://www.mof.gov.cn/zhengwuxinxi/caizhengxinwen/202410/t20241016_3945672.htm'),
 dict(province='安徽', report_date='2023-12', year=2023, headline=False,
      metric='省新兴产业引导基金体系(实缴)', basis='实缴', value_yi=534.75, paidin_yi=534.75, count=56,
      quote='截至2023年底，基金体系母子基金实缴规模534.75亿元，累计投资项目469个；已设立16只母基金和40只子基金。',
      report='安徽省新兴产业引导基金信息公开', source='https://baike.baidu.com/item/安徽省新兴产业引导基金/62930369'),
 dict(province='安徽', report_date='2022-06', year=2022, headline=False,
      metric='省新兴产业引导基金体系(组建目标)', basis='目标', value_yi=2000, paidin_yi=500, count=16,
      quote='省级财政计划出资500亿元组建省新兴产业引导基金，下设三大基金群16只母基金，撬动形成总规模不低于2000亿元的体系。',
      report='《安徽省新兴产业引导基金组建方案》新闻发布会',
      source='http://fbh.anhuinews.com/project/202206/t20220630_6112377.html'),
]


def build():
    rows = sorted(ROWS, key=lambda r: (r['province'], r['report_date']))
    meta = {
        'title': 'Province-level government investment/guidance fund scale — official disclosures (prototype)',
        'unit': '亿元 (RMB 100M); 10000亿 = 1万亿',
        'provinces': sorted({r['province'] for r in rows}),
        'basis_tags': '认缴 | 实缴 | 撬动(社会资本) | 目标 | 投放(累计投资额) | 只数',
        'caveat': ('数字以各行 quote/source 为准。口径混杂，不可跨口径或跨母/子层相加。来源多为财政厅公告/'
                   '发布会/官方媒体转载，政府工作报告多为定性。非统一年度表，需逐省人工核验。'),
        'updated': datetime.date.today().isoformat(),
        'rows': len(rows),
    }
    json.dump({'meta': meta, 'data': rows},
              open(os.path.join(DIR, 'province_scale.json'), 'w'),
              ensure_ascii=False, separators=(',', ':'))

    def yi(v): return '—' if v is None else (f'{v:,.0f}' if float(v).is_integer() else f'{v:,.2f}')
    lines = ['# 省级政府投资基金规模 — 官方披露（原型，3 省）', '',
             '单位 **亿元**。每个数字以其 **quote/来源** 为准。', '',
             '> 口径标签:认缴 / 实缴 / 撬动(社会资本) / 目标 / 投放(累计投资额) / 只数。'
             '**不可跨口径或跨母/子层相加。** 来源以财政厅公告·发布会·官方媒体转载为主;政府工作报告多为定性。', '']
    # headline summary
    lines += ['## 各省最新汇总(headline)', '',
              '| 省 | 时点 | 口径 | 规模(亿) | 实缴(亿) | 只数 | 来源 |',
              '|----|------|------|-------:|-------:|----:|------|']
    for r in [x for x in rows if x['headline']]:
        lines.append(f"| {r['province']} | {r['report_date']} | {r['basis']} | {yi(r['value_yi'])} | "
                     f"{yi(r['paidin_yi'])} | {r['count'] or '—'} | [链接]({r['source']}) |")
    lines.append('')
    # full timeline per province
    for prov in meta['provinces']:
        lines += [f'## {prov}（时间线）', '',
                  '| 时点 | 口径 | 规模/值(亿) | 只数 | 指标 | 原文 | 来源 |',
                  '|------|------|--------:|----:|------|------|------|']
        for r in [x for x in rows if x['province'] == prov]:
            q = r['quote'][:80] + ('…' if len(r['quote']) > 80 else '')
            lines.append(f"| {r['report_date']} | {r['basis']} | {yi(r['value_yi'])} | {r['count'] or '—'} | "
                         f"{r['metric']} | {q} | [链接]({r['source']}) |")
        lines.append('')
    open(os.path.join(DIR, 'PROVINCE_SCALE.md'), 'w', encoding='utf-8').write('\n'.join(lines))

    print(f"  province_scale.json + PROVINCE_SCALE.md: {len(rows)} rows, "
          f"{len(meta['provinces'])} provinces {meta['provinces']}")
    for r in [x for x in rows if x['headline']]:
        print(f"    {r['province']} {r['report_date']}: {r['metric']} = {yi(r['value_yi'])}亿 "
              f"(实缴 {yi(r['paidin_yi'])}, {r['count']}支, {r['basis']})")


if __name__ == '__main__':
    print('Building province-level fund-scale prototype (广东/浙江/安徽) ...')
    build()
    print('Done.')
