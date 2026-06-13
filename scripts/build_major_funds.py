#!/usr/bin/env python3
"""Compile a curated table of China's *major* government guidance / investment
funds (政府引导基金 / 政府投资基金) with their scale and a source for every figure.

Why this is separate from fetch_ggf.py: AMAC's public registry (what fetch_ggf
scrapes) carries NO fund-size field, so per-fund scale has to be assembled by
hand from announcements / 工商登记 / finance media. This file is that curated
layer — limited to the *large* funds (national-level and the big provincial /
municipal ones), each row carrying its own source URL. Re-run to regenerate the
JSON + the human-readable MAJOR_FUNDS.md.

Two scale columns, deliberately kept apart to avoid the double-counting that
plagues headline numbers:
  * paidin_yi  — the fund's own government / committed capital (认缴/实缴), 亿元
  * target_yi  — announced 目标/规划 scale, which for most funds is a *leverage*
                 target for a whole 基金群/体系 (撬动社会资本后的盘子), 亿元
`scope` flags whether target_yi describes a single fund ("fund") or an explicitly
cluster/system-level goal ("cluster") — sum only within one scope, never mix.

Unit: 亿元 (RMB 100 million). 10000 亿 = 1 万亿 = 1 RMB trillion.

Incremental update: append rows here (or correct a figure + its source) and re-run.
Sources are as-reported (.gov.cn, fund announcements, 投资界/投中/证券时报/新浪 etc.);
verify against the primary filing before citing a specific number.
"""
import os, re, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR  = os.path.join(ROOT, 'data', 'govt-guidance-funds')

# ---------------------------------------------------------------------------
# National level (国家级)
# ---------------------------------------------------------------------------
NATIONAL = [
 ("国家集成电路产业投资基金（大基金）一期", "全国", 1387, 987.2, "2014-09",
  "财政部、国开金融、中国烟草、中国移动等",
  "https://finance.sina.com.cn/roll/2025-06-29/doc-infctvcn5343398.shtml",
  "注册资本(认缴)987.2亿，含优先股后募资总规模约1387亿"),
 ("国家集成电路产业投资基金（大基金）二期", "全国", 2041.5, 2041.5, "2019-10",
  "财政部、国开金融、地方国资及多家央企", "https://www.jiemian.com/article/3630039.html",
  "公司制，注册资本即认缴规模2041.5亿"),
 ("国家集成电路产业投资基金（大基金）三期", "全国", 3440, 3440, "2024-05",
  "财政部、六大国有银行(合计1140亿)、国开金融等19家",
  "https://jrj.wuhan.gov.cn/ztzl_57/xyrd/dcczbsc/202405/t20240531_2410056.shtml",
  "注册资本3440亿，迄今最大；财政部持股17.44%，存续期15年"),
 ("国家中小企业发展基金（母基金）", "全国", 1000, 357.5, "2020-06",
  "财政部(持股42.66%)、中国烟草、上海国盛等",
  "https://finance.sina.com.cn/china/gncj/2020-06-23/doc-iirczymk8617953.shtml",
  "母基金注册357.5亿，撬动子基金总规模目标超1000亿"),
 ("国家新兴产业创业投资引导基金", "全国", 400, None, "2016",
  "发改委、财政部牵头，中金启元/国投创合/盈富泰克三家管理",
  "https://www.ndrc.gov.cn/fzggw/jgsj/gjss/sjdt/202109/t20210917_1297011.html",
  "目标总规模400亿，分三家母基金；母基金层实缴未单独披露"),
 ("国家科技成果转化引导基金", "全国", None, None, "2011",
  "科技部、财政部", "https://fuwu.most.gov.cn/html/jcxtml/20181212/2846.html?tab=xgwj",
  "中央财政拨款制(非认缴)，母基金规模未公开；累计36只子基金合计624亿"),
 ("国家制造业转型升级基金", "全国", 1472, 73.6, "2019-11",
  "财政部、国开金融、中国烟草等20家股东", "https://startup.aliyun.com/info/1030742.html",
  "注册资本(认缴)1472亿，首期实缴仅73.6亿(5%)"),
 ("国家绿色发展基金", "全国", 885, 232.75, "2020-07",
  "财政部(100亿)、生态环境部、上海市及沿江11省市、五大行",
  "https://www.nbd.com.cn/articles/2020-07-15/1460912.html",
  "注册资本885亿，成立时实缴232.75亿(后增至约309.5亿)；重点长江经济带"),
 ("中国国有企业结构调整基金（国调基金）一期", "全国", 3500, 1310, "2016-09",
  "中国诚通、邮储银行(500亿)、招商局(200亿)等",
  "https://www.ndrc.gov.cn/fggz/tzgg/ggkx/201610/t20161013_1078431.html",
  "总目标3500亿分期；一期首期认缴1310亿"),
 ("中国国有企业结构调整基金（国调基金）二期", "全国", 1000, 737.5, "2021-08",
  "中国诚通牵头，中国移动、中铁资本、中国电信等", "https://www.wxrb.com/doc/2021/10/08/120720.shtml",
  "目标不低于1000亿，注册(认缴)737.5亿；属3500亿总规划二期"),
 ("中国国有企业混合所有制改革基金（混改基金）", "全国", 2000, 707, "2020-12",
  "中国诚通(33.95%)、三峡、中国建材、国新、万科、上海临港等",
  "https://jrj.sh.gov.cn/ZXYW178/20201230/8b9b2d909a424c97b576162a02cd47cc.html",
  "总目标2000亿，首期认缴707亿"),
 ("国家军民融合产业投资基金一期", "全国", 1500, 510, "2018-12",
  "财政部、中航资本牵头及多家军工央企", "https://www.stcn.com/article/detail/1606228.html",
  "总目标1500亿，一期认缴510亿(实缴479.2亿)"),
 ("国家军民融合产业投资基金二期", "全国", None, 596, "2025-03",
  "财政部(21%/100亿)、航空工业/中核/航天科技/船舶等及地方引导基金",
  "https://www.stcn.com/article/detail/1606228.html",
  "2025年新设，注册(认缴)596亿，目标未公开"),
 ("先进制造产业投资基金一期", "全国", 200, None, "2016-06",
  "发改委/财政部/工信部牵头，国投(40亿)、工行等",
  "https://www.ime.ac.cn/zhxx/ynxx/201809/t20180916_5082218.html",
  "首期目标200亿，中央财政出资60亿；有限合伙"),
 ("先进制造产业投资基金二期", "全国", 500, None, "2019",
  "国投招商、国家开发投资集团发起，社保基金参与", "https://www.trjcn.com/cyxm/115260.html",
  "目标500亿；认缴/实缴未公开"),
 ("国家融资担保基金", "全国", None, 661, "2018-07",
  "财政部(300亿/45.4%)、国开行、进出口行、六大行等21家", "https://m.thepaper.cn/newsDetail_forward_2330677",
  "注册(认缴)661亿；再担保非股权投资，无目标规模概念；2024年合作业务1.41万亿"),
 ("中央企业乡村产业投资基金", "全国", 1000, 337.43, "2016-10",
  "国资委牵头、财政部参与，91家央企", "https://c.m.163.com/news/a/HCCVGEK70519DDQ2.html",
  "目标1000亿分期，截至2022年中认缴337.43亿；原央企扶贫基金，2021年更名"),
 ("国家创业投资引导基金", "全国", 10000, 1000, "2025-07",
  "发改委、财政部(100%持股，财政出资1000亿，来自超长期特别国债)",
  "https://news.pedaily.cn/202512/559188.shtml",
  "母基金财政出资1000亿；目标三层架构撬动万亿级；首批区域基金京津冀296.46+长三角471+粤港澳450.5亿"),
]

# ---------------------------------------------------------------------------
# Eastern / coastal provinces + municipalities
# ---------------------------------------------------------------------------
EAST = [
 ("上海集成电路产业母基金", "上海", 450.01, None, "2024", "上海国投先导牵头，国泰君安/海通/上汽等",
  "https://stcn.com/article/detail/1266418.html", "目标即认缴450.01亿，三大先导母基金合计890.03亿"),
 ("上海生物医药产业母基金", "上海", 215.01, None, "2024", "上海国投先导牵头，国泰君安/海通/上汽/临港等",
  "https://stcn.com/article/detail/1266418.html", "目标即认缴215.01亿"),
 ("上海人工智能产业母基金", "上海", 225.01, None, "2024", "上海国投先导牵头，徐汇区/国泰君安/海通等",
  "https://finance.sina.com.cn/roll/2024-07-11/doc-incctzkx5300010.shtml", "目标即认缴225.01亿，落地徐汇"),
 ("上海未来产业基金", "上海", 150, 100, "2024", "上海市财政全额出资",
  "https://stcsm.sh.gov.cn/xwzx/mtjj/20240913/ec45fdaa7a9f4aa394ed8fc2a040c6ec.html",
  "市财政全额出资100亿，2025年9月据报扩募至150亿；聚焦脑机/量子/合成生物"),
 ("北京市政府投资引导基金", "北京", 2500.1, None, "2016", "北京国资运营(市国资委)持股99.996%",
  "https://stcn.com/article/detail/1483760.html", "初始1000.1亿，2025年1月增资至2500.1亿；下设8只市级产业基金"),
 ("北京市科技创新基金", "北京", 300, 200, "2018", "北京市引导基金、市属国企、中金资本等",
  "https://www.beijing.gov.cn/ywdt/gzdt/202410/t20241014_3918386.html",
  "目标300亿，首期认缴200亿；截至2024年10月带动824亿"),
 ("北京市人工智能产业投资基金", "北京", 100, None, "2023", "北京国管及市引导基金，君联资本管理",
  "https://finance.sina.com.cn/tech/roll/2025-03-03/doc-ineniuqs0997449.shtml", "目标100亿，首期40亿"),
 ("北京市医药健康产业投资基金", "北京", 200, None, "2023", "北京国管及市引导基金，康桥资本管理",
  "https://kfqgw.beijing.gov.cn/cxyzkfq/shggxxq/tzcj/202401/t20240110_3531604.html", "目标200亿，首期100亿"),
 ("北京市先进制造和智能装备产业投资基金", "北京", 200, None, "2024", "北京国管及市引导基金，基石资本管理",
  "https://finance.sina.com.cn/tech/roll/2025-03-03/doc-ineniuqs0997449.shtml", "目标200亿；北京国管8只基金合计1000亿之一"),
 ("北京机器人产业发展投资基金", "北京", 100, None, "2023", "首程控股联合北京国管",
  "https://finance.sina.com.cn/money/fund/fundzmt/2024-01-17/doc-inacvxxs3322043.shtml", "目标100亿，落地经开区"),
 ("北京信息产业发展投资基金", "北京", 100, None, "2023", "北京国管及市引导基金，启明创投管理",
  "https://finance.sina.com.cn/tech/roll/2025-03-03/doc-ineniuqs0997449.shtml", "目标100亿"),
 ("广东省战略性新兴产业投资引导基金", "广东", 1000, 500, "2025", "广东省财政厅全额出资，粤财基金运营",
  "https://www.stcn.com/article/detail/3926175.html", "目标1000亿，首期注册500亿；广东首支永续公司制省级政府投资基金"),
 ("广东省半导体及集成电路产业投资基金一期", "广东", 200, None, "2020", "粤财控股(省财政)>90%，东莞/中山各4.5%",
  "https://www.cls.cn/detail/1326301", "初始200亿，后扩至约310亿"),
 ("广东省半导体及集成电路产业投资基金二期", "广东", 300, 110.01, "2023", "粤财控股主导",
  "https://www.dramx.com/News/IC/20231220-35423.html", "目标300亿(规划)，首关实际出资110.01亿；存续17年"),
 ("深圳市政府投资引导基金", "广东(深圳)", 1000, 1500, "2015", "深圳市财政全额，深创投受托管理",
  "https://www.sz.gov.cn/cn/zjsz/fwts_1_3/yxhjjc/content/post_12073134.html",
  "初始目标1000亿，分批注入累计实缴超1500亿；参设子基金300+，子基金总规模约4700亿"),
 ("深圳市“20+8”产业基金群", "广东(深圳)", 10000, None, "2022", "深圳引导基金与市区国资、社会资本",
  "https://www.sznews.com/news/content/2025-03/11/content_31485329.htm",
  "基金群(非单只)，2026年底目标形成万亿级；首批目标165亿、第二批85亿"),
 ("江苏省战略性新兴产业母基金", "江苏", 500, None, "2024", "江苏省政府，江苏高科技投资集团管理",
  "https://www.jiangsu.gov.cn/art/2024/6/22/art_60096_11277076.html",
  "母基金500亿；两批36只专项基金合计914亿，预计撬动2800亿"),
 ("浙江省产业基金（“4+1”基金群3.0）", "浙江", 1000, None, "2023", "浙江省产业基金公司管理，省财政厅监管",
  "https://www.21jingji.com/article/20230518/herald/399893865cbcea13710b5ba2c95e4726.html",
  "基金群目标，首批600亿+，母子放大形成2000亿+；累计认缴近600亿"),
 ("宁波市国资国改基金", "浙江(宁波)", 500, None, "2020", "宁波市国资委牵头，宁波通商集团",
  "https://finance.sina.com.cn/tech/roll/2023-02-02/doc-imyehyin6664384.shtml", "总规模500亿，两大母基金"),
 ("山东省新旧动能转换基金（引导基金）", "山东", 200, 204, "2018", "省市两级出资，省财政200亿，省新动能基金管理",
  "http://czt.shandong.gov.cn/art/2023/11/14/art_21859_10317110.html",
  "引导基金省财政200亿，截至2023年底实缴204亿；带动总参与基金超2200亿"),
 ("安徽省新兴产业引导基金", "安徽", 2000, 500, "2023", "省财政500亿撬动社会资本",
  "https://news.cnstock.com/industry,rdjj-202304-5051273.htm", "省财政认缴500亿(5年分批)，体系目标2000亿"),
 ("天津海河产业基金", "天津", 1000, None, "2017", "市政府引导200亿，中信/中民投/紫光/海尔及弘毅等",
  "https://www.yicai.com/news/5262371.html", "引导200亿，目标母基金群约1000亿；截至2024年底72只母基金总规模703亿"),
 ("福建省级政府投资基金", "福建", 100, None, "2024", "福建省财政，省国资委管理",
  "https://m.thepaper.cn/newsDetail_forward_30854087", "规模100亿，目标5年构建300亿功能类基金群；已参股6只总规模465亿+"),
 ("福建省产业基金", "福建", 100, None, "2015", "省财政，福建省投资开发集团",
  "https://m.thepaper.cn/newsDetail_forward_30854087", "规模100亿，目标构建1000亿基金群；累计23只总规模370亿+"),
]

# ---------------------------------------------------------------------------
# Central / Western / Northern / Northeastern provinces
# ---------------------------------------------------------------------------
CENTRAL = [
 ("湖北省长江经济带产业基金（基金群）", "湖北", 2000, 4577, "2015", "省财政引导400亿，长江产业投资集团牵头",
  "https://www.gov.cn/xinwen/2015-12/22/content_5026425.htm",
  "2015年母基金目标2000亿；基金群认缴已超5735亿、实缴4577亿(截至2024末)"),
 ("长江产业投资基金", "湖北", 400, 375, "2022", "湖北省长江产业投资集团(省国资委)",
  "https://www.yangtze-fund.com/ywbk/cjcytzjj_2/", "目标400亿，截至2022年底认缴375亿"),
 ("湖北省政府投资引导基金", "湖北", 200, None, "2023", "省财政厅，中金资本/深创投联合受托",
  "https://www.hubei.gov.cn/zwgk/hbyw/hbywqb/202402/t20240226_5096381.shtml", "首期200亿，目标带动省市县超2000亿"),
 ("楚天凤鸣科创天使基金", "湖北", 100, 12.06, "2023", "长江产业投资集团牵头，省引导基金参股",
  "https://www.hubei.gov.cn/zwgk/hbyw/hbywqb/202402/t20240226_5096381.shtml", "目标100亿，截至2024初实缴约12.06亿"),
 ("武汉光谷产业投资基金矩阵（三母基金）", "湖北(武汉)", 4000, 3870, "2017", "东湖高新区(光谷)管委会",
  "https://www.stcn.com/article/detail/950504.html", "三母基金目标合计4000亿，子基金总规模已超3870亿(实缴超2500亿)"),
 ("湖南省金芙蓉投资基金（体系）", "湖南", 3000, None, "2024", "省财政(约240亿)+省属国企(约800亿)+市县社会资本，财信金控管理",
  "https://czt.hunan.gov.cn/czt/xxgk/gzdt/gzdt/202409/t20240905_33447423.html",
  "3年目标3000亿；财政+国企撬动本金约1040亿；“1+5+N”"),
 ("湖南省省级产业引导母基金", "湖南", 200, None, "2024", "省财政厅(存量30亿+新增170亿)，财信产业基金管理",
  "https://www.thepaper.cn/newsDetail_forward_27413152", "金芙蓉体系内省级引导母基金，目标200亿+"),
 ("河南省新兴产业投资引导基金", "河南", 1500, None, "2022", "省财政130亿+省属投资公司170亿(母基金300亿)撬动市县社会资本",
  "https://news.sciencenet.cn/htmlnews/2022/2/474216.shtm", "目标1500亿(整合450亿+新增1050亿)，母基金300亿，5年到位"),
 ("四川省政府产业投资引导基金", "四川", 1000, 200, "2024", "省财政厅(首期200亿)，四川产业振兴基金集团受托",
  "https://finance.sina.com.cn/roll/2024-08-21/doc-inckkkkn7942687.shtml", "母基金首期200亿，目标省市县联动形成1000亿+集群"),
 ("四川产业振兴基金投资集团", "四川", 300, None, "2011", "省财政厅、四川发展(控股)",
  "https://startup.aliyun.com/city/cd/info/8956", "公司制，2024年12月注册资本增至300亿；在管基金规模超1200亿"),
 ("重庆市产业投资母基金", "重庆", 2000, None, "2023", "渝富控股、两江新区、高新区，渝富资本运营",
  "https://news.pedaily.cn/202305/513965.shtml", "目标2000亿(一期认缴800亿)，截至2025初子基金认缴603亿、母基金出资138亿"),
 ("重庆两江新区高质量发展产业投资基金", "重庆(两江)", 200, None, "2023", "两江产业/投资/基金集团等区内国企",
  "https://www.cq.gov.cn/ywdt/zwhd/bmdt/202303/t20230314_11758422.html", "区级200亿，目标撬动形成600亿集群"),
 ("陕西省政府投资引导基金（集群）", "陕西", 1055, None, "2019", "省财政厅，陕西财金投资管理",
  "https://www.shaanxi.gov.cn/xw/sxyw/202507/t20250717_3544059.html",
  "2019年首期200亿；截至2025年6月形成1055.38亿集群(45只子基金)"),
 ("江西省现代产业引导基金", "江西", 3000, None, "2022", "江西国控牵头，省母基金首批300亿撬动市县社会资本",
  "https://jiangxi.jxnews.com.cn/system/2023/07/03/020131422.shtml", "目标3000亿(首批1500亿)，省母基金首批出资300亿"),
 ("河北省科技投资引导基金", "河北", 28.85, None, None, "省科技厅主管，省政府出资",
  "https://www.most.gov.cn/dfkj/hb/zxdt/202501/t20250124_192982.html", "约28.85亿，全省唯一专注科创的省级引导基金；37只子基金合计204亿"),
 ("雄安产业投资引导基金", "河北(雄安)", 100, None, "2018", "雄安新区管委会，中国雄安集团基金公司",
  "https://www.chinaventure.com.cn/news/80-20250619-386791.html", "100亿，8只子基金；2025年再设100亿科创基金"),
 ("山西省省级政府投资基金群（12只）", "山西", None, 460, None, "省财政/省级国资，山西省产业基金管理等",
  "https://finance.sina.com.cn/jjxw/2024-12-17/doc-inczukxm4774364.shtml",
  "截至2024年12月12只，累计投放460亿；正整合为三大母基金集群"),
 ("云南省政府投资基金体系", "云南", 500, None, None, "省财政，“引导基金+产业母基金+子基金”三级",
  "https://jrb.km.gov.cn/c/2024-12-27/4928490.shtml", "2024年12月方案：5年内构建500亿+体系，带动社会资本1000亿"),
 ("贵州省“四化”及生态环保政府投资基金（5只）", "贵州", 200, 200, "2021", "省财政厅，贵州金控代表管理",
  "https://finance.sina.com.cn/wm/2023-01-08/doc-imxznaas2417968.shtml",
  "省财政200亿设5只基金，2021年已全部到位，带动6.6倍；2024年再注入267亿"),
 ("广西壮族自治区投资引导基金", "广西", 300, 110.63, None, "自治区财政厅，广西投资引导基金公司(注册30亿)运营",
  "https://www.chinanews.com.cn/cj/2025/05-04/10410532.shtml",
  "目标2027年底财政累计注资300亿+；截至2025年3月实缴110.63亿，参设66只，撬动484亿"),
 ("辽宁省产业（创业）投资引导基金", "辽宁", 200, None, "2015", "省财政，辽宁金控旗下辽宁基金运营",
  "https://finance.sina.com.cn/tech/roll/2022-11-21/doc-imqmmthc5383682.shtml",
  "初始100亿，2022年增资至200亿；参股子基金为主"),
 ("龙江现代产业投资引导基金", "黑龙江", 200, None, "2023", "省级财政，省金控旗下托管",
  "https://www.hlj.gov.cn/hlj/c107857/202309/c00_31666641.shtml", "总规模200亿，首期70亿，2023年10月设立；母子基金运作"),
 ("内蒙古重点产业引导基金", "内蒙古", 85, None, "2025", "自治区工信厅，管理人公开遴选",
  "https://finance.sina.com.cn/tech/roll/2025-06-09/doc-ineznhpn9966786.shtml",
  "2025年专项资金9.85亿结合后约85亿总规模；现存最大省级产业引导基金"),
 ("新疆产业发展投资引导基金", "新疆", 100, None, "2022", "自治区政府，新疆金投发起，新疆新动能管理",
  "https://m.jiemian.com/article/8108181.html", "首只百亿级，目标形成500亿+集群(“1+N”)"),
 ("甘肃省产业结构调整基金（兴陇系列）", "甘肃", 100, None, None, "甘肃国投与工银投资发起",
  "https://finance.sina.com.cn/jjxw/2024-12-03/doc-incyekxt4880855.shtml", "总规模100亿；另管兰州新区引导基金30亿"),
]

# ---------------------------------------------------------------------------
# Smaller AMAC seed funds enriched with scale via web search (demo, local).
# ---------------------------------------------------------------------------
SEED = [
 ("宁夏产业引导基金二期有限公司", "宁夏", 10, 10, "2025", "宁夏回族自治区财政厅全资",
  "https://www.jiemian.com/article/13848554.html", "注册资本(认缴)10亿；AMAC备案命中"),
 ("四川省文旅商贸股权投资引导基金", "四川", 50, 50, "2026", "四川产业基金系，管理人四川盈耀",
  "https://m.chinaventure.com.cn/news/80-20260411-390898.html", "认缴50亿；AMAC备案命中"),
 ("南宁市人工智能创新合作发展产业投资基金", "广西(南宁)", 50, 50, "2025", "南宁财金/朱槿资本/南宁投资引导基金",
  "https://finance.sina.com.cn/jjxw/2025-08-07/doc-infkcwez4529326.shtml", "出资额50亿；AMAC备案命中"),
]

CLUSTER_HINT = re.compile(r'集群|基金群|体系|撬动|联动|形成\d|母子|目标.*(?:亿|万亿).*(?:撬动|形成|带动)')


def level_of(bucket):
    return bucket


def rows():
    out = []
    def add(items, default_level):
        for fund, region, tgt, paid, est, backer, src, note in items:
            # market/provincial level from the explicit name, else default
            lv = '国家级' if default_level == '国家级' else (
                '市级' if any(k in fund for k in ('市', '区', '雄安', '光谷', '两江', '南宁')) and '省' not in fund
                else '省级')
            scope = 'cluster' if (CLUSTER_HINT.search(note) or any(
                k in fund for k in ('基金群', '矩阵', '体系', '集群'))) else 'fund'
            out.append({
                'fund': fund, 'level': lv, 'region': region,
                'target_yi': tgt, 'paidin_yi': paid, 'scope': scope,
                'established': est, 'backer': backer, 'source': src, 'note': note,
            })
    add(NATIONAL, '国家级')
    add(EAST, '地方')
    add(CENTRAL, '地方')
    add(SEED, '地方')
    return out


def fmt(v):
    if v is None: return '—'
    return f'{v:,.0f}' if float(v).is_integer() else f'{v:,.2f}'


def build():
    data = rows()
    meta = {
        'title': 'China major government guidance/investment funds — scale (政府引导基金 规模)',
        'unit': '亿元 (RMB 100 million); 10000亿 = 1万亿 = 1 trillion',
        'columns': {
            'paidin_yi': "fund's own government/committed capital (认缴/实缴)",
            'target_yi': 'announced 目标/规划 scale — for many funds a leverage target for a 基金群/体系',
            'scope': 'fund = single fund; cluster = system/基金群 target (do not sum across scopes)',
        },
        'caveat': '每个数字以其 source 链接为准；目标规模多为撬动社会资本后的体系目标，远大于政府实际出资。引用前核对原始公告。',
        'updated': datetime.date.today().isoformat(),
        'count': len(data),
    }
    out = {'meta': meta, 'funds': data}
    json.dump(out, open(os.path.join(DIR, 'major_funds.json'), 'w'),
              ensure_ascii=False, separators=(',', ':'))

    # markdown, grouped by level, sorted by best-available scale
    order = {'国家级': 0, '省级': 1, '市级': 2}
    def key(f): return (order.get(f['level'], 9), -((f['target_yi'] or 0) or (f['paidin_yi'] or 0)))
    data_sorted = sorted(data, key=key)
    lines = ['# 政府引导基金 / 政府投资基金 — 重点基金规模（curated）', '',
             f"单位 **亿元**(10000亿=1万亿)。共 **{len(data)}** 只。每个数字以其链接为准。", '',
             '> **口径警示：** `认缴/实缴`是基金自身的政府/承诺出资;`目标/规划`多为撬动社会资本后的'
             '基金群/体系目标,常远大于实际出资。`scope=cluster`表示体系/基金群口径,**不可与单只基金相加**。',
             '> 非官方滚动源,数据为公告/工商/财经媒体转载汇编,引用前请核对原始来源。', '']
    hdr = ('| 基金 | 地区 | 认缴/实缴 | 目标/规划 | scope | 成立 | 出资方 | 来源 |\n'
           '|------|------|-------:|-------:|:--:|:--:|------|------|')
    for lv in ('国家级', '省级', '市级'):
        grp = [f for f in data_sorted if f['level'] == lv]
        if not grp: continue
        lines += [f'## {lv}（{len(grp)}）', '', hdr]
        for f in grp:
            lines.append(f"| {f['fund']} | {f['region']} | {fmt(f['paidin_yi'])} | "
                         f"{fmt(f['target_yi'])} | {f['scope']} | {f['established'] or '—'} | "
                         f"{f['backer']} | [链接]({f['source']}) |")
        lines.append('')
    open(os.path.join(DIR, 'MAJOR_FUNDS.md'), 'w', encoding='utf-8').write('\n'.join(lines))

    # sanity aggregates (scope=fund only, to avoid cluster double counting)
    fund_paid = sum(f['paidin_yi'] or 0 for f in data if f['scope'] == 'fund')
    nat_paid  = sum(f['paidin_yi'] or 0 for f in data if f['level'] == '国家级')
    print(f"  major_funds.json + MAJOR_FUNDS.md: {len(data)} funds "
          f"({sum(f['level']=='国家级' for f in data)} 国家级 / "
          f"{sum(f['level']=='省级' for f in data)} 省级 / "
          f"{sum(f['level']=='市级' for f in data)} 市级)")
    print(f"  Σ 认缴/实缴 (scope=fund only): {fund_paid:,.0f} 亿  ·  其中国家级 {nat_paid:,.0f} 亿")
    print(f"  funds with a paid-in figure: {sum(1 for f in data if f['paidin_yi'])}/{len(data)}; "
          f"with a target figure: {sum(1 for f in data if f['target_yi'])}/{len(data)}")


if __name__ == '__main__':
    print('Compiling major government guidance fund scale table ...')
    build()
    print('Done.')
