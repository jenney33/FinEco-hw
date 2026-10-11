# 构建 hw02-1.ipynb
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata['kernelspec'] = {'display_name': 'Python 3 (fineco)', 'language': 'python', 'name': 'fineco'}
nb.metadata['language_info'] = {'name': 'python', 'version': '3.13.12'}

cells = []
def md(src): cells.append(nbf.v4.new_markdown_cell(src))
def code(src): cells.append(nbf.v4.new_code_cell(src))

# ============ 首格信息 ============
md("""# HW02-1：股票收益与组合风险分析

- 姓名：黄翌珊
- 学号：24360023
- 作业简介或教师作业页面链接：[HW02 作业页面](https://lianxhcn.github.io/FinEco/exercises/hw-02.html)
- 个人 GitHub 仓库访问地址：[https://github.com/jenney33/FinEco-hw](https://github.com/jenney33/FinEco-hw)
- HW02-1 目录链接：[hw02-1](https://github.com/jenney33/FinEco-hw/tree/main/hw02-1)
- HW02-2 目录链接：[hw02-2](https://github.com/jenney33/FinEco-hw/tree/main/hw02-2)
- 数据来源、获取日期与样本期间：不复权日线与成交额取自腾讯行情接口（AKShare `stock_zh_a_hist_tx`，2026-09-18 下载）；**后复权日线取自新浪财经**（AKShare `stock_zh_a_daily`，2026-10-12 下载，原因见 2.3 节）；腾讯前复权与分红除权事件 2026-10-11 补充下载；百度股市通历史总市值（AKShare `stock_zh_valuation_baidu`，2026-09-18 下载）；行业分类为申万一级行业（AKShare `sw_index_first_info` / `index_component_sw`，2026-09-18 核验）。样本期间 **2021-01-01 至 2026-09-16**，另取 2020-12-30/31 两个交易日用于计算首个交易日收益率。
- **价格口径**：全篇价格与收益率**一律使用复权价**，且统一采用**后复权（hfq）**一条序列——它以上市首日价为基准向后累乘，包含分红再投资与送转股调整，序列在除权除息日保持连续。**后复权序列经跨源核验后选用新浪财经数据**：腾讯后复权序列在无除权日的区间内复权因子仍会漂移（2.3 节实测漂移达 6.3%，涨停日 +10.00% 被压缩成 +8.45%），且全期总回报与独立复算结果偏差最大达 24 个百分点，已弃用。不复权价仅用于两处：识别除权除息事件、按"网格市值 ÷ 不复权价"校准股本构造真实总市值（作业明确禁止用复权价乘股本构造市值）。前复权序列已下载并用于复权基准校验，但因其与后复权的分红处理口径不一致（见 2.3 节），不参与任何计算。
- AI 使用声明：使用了 WorkBuddy（AI 助手）辅助搭建运行环境、编写数据获取脚本与 Notebook 代码初稿、组织报告语言；本人逐单元核验了数据口径、计算逻辑与图表，并手动复核了关键统计量（组合年化收益、最大回撤、相关系数）。

**分析目的与总体思路**：本作业选取 10 只覆盖 8 个申万一级行业的 A 股股票，使用 2021-01-01 至 2026-09-16 的日频数据，回答三个问题：(1) 这些代表性上市公司的收益与风险特征如何；(2) 同行业股票的收益相关性是否更高；(3) 等权与市值加权两种组合的长期表现有何差异。思路是：先获取并检查数据（主键、覆盖、停牌、除权、异常收益），**再核验三种复权口径**并基于复权价计算日简单收益率，进行描述统计与图形分析，最后构造等权与市值加权组合并对比其净值、几何年化收益、年化波动与最大回撤。""")

# ============ 1 选股 ============
md("""## 1. 选股与数据来源

### Step 1：分析说明

按作业要求选取 **10 只 A 股、至少 5 个行业**的股票。选股标准：

- 所有股票在样本开始日（2021-01-01）之前已上市，样本期内数据覆盖完整；
- 覆盖 8 个申万一级行业，兼顾金融、消费、制造、医药、新能源、公用事业与科技；
- 特意纳入**美的集团与格力电器**这对同行业（家用电器）龙头，用于检验"同行业股票收益相关性更高"的猜想；
- 选股理由基于行业地位、商业模式与代表性，不以事后涨幅为依据。

数据来源与获取记录：

| 数据 | 来源接口 | 参数 | 下载日期 |
|---|---|---|---|
| 不复权日线收盘价、成交量 | 腾讯行情 `stock_zh_a_hist_tx` | `2020-12-30 ~ 2026-09-16`，`adjust=''` | 2026-09-18 |
| **后复权日线收盘价（算收益率主口径）** | **新浪财经 `stock_zh_a_daily`** | `2020-12-01 ~ 2026-09-16`，`adjust='hfq'` | 2026-10-12 |
| 后复权日线收盘价（腾讯，仅作对照） | 腾讯行情 `stock_zh_a_hist_tx` | `2020-12-30 ~ 2026-09-16`，`adjust='hfq'` | 2026-09-18 |
| 前复权日线收盘价（复权基准校验） | 腾讯行情（直连接口，与 AKShare 同源） | 同上，`adjust='qfq'` | 2026-10-11 |
| 分红除权事件（除权日、登记日、方案） | 腾讯行情 qfq 接口附带字段 | `nd / djr / cqr / FHcontent` | 2026-10-11 |
| 历史总市值（约 5 日一档的网格） | AKShare `stock_zh_valuation_baidu`（百度股市通） | `indicator='总市值'`，`period='近十年'`，单位亿元 | 2026-09-18 |
| 申万一级行业归属 | AKShare `sw_index_first_info` + `index_component_sw` | 2026 年 9 月最新成分 | 2026-09-18 |
| 上市日期 | AKShare `stock_info_sh_name_code` / `stock_info_sz_name_code`（交易所官方） | 主板A股 / A股列表 | 2026-09-18 |

**复权口径定义**（作业要求"解释复权口径，不将复权价视为实际成交价"）：

- **不复权价** $P^{raw}$：交易所真实成交价。除权除息日会出现向下跳变（如比亚迪 2025-07-29 因大比例转增，价格从约 240 元跳到 80 元级别），用它算收益会把"分红/送转"误记为亏损，**严重低估真实收益**；
- **后复权价** $P^{hfq}$：以**上市首日价**为基准向后累加分红再投资与送转，反映"长期持有到今天"的累计总回报，**本文主口径**（收益率、净值、价格图统一使用）。本文后复权序列取自**新浪财经**，原因是腾讯后复权序列存在复权因子漂移缺陷（见 2.3 节，涨停日 +10.00% 被压缩为 +8.45%，长江电力全期总回报低估约 24 个百分点）；
- 前复权价 $P^{qfq}$：以**最新价**为基准向前调整历史价，最新价 = 真实成交价，价格水平与当前报价可比。它已下载并用于核验复权基准（末日应与不复权价相等），但**实测与后复权序列的日收益率并不一致**（见 2.3 节），故不参与任何计算。""")

code("""import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 中文与负号正常显示
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'PingFang SC', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 选股表（行业为申万一级行业，2026-09-18 成分口径核验）
sel = pd.read_csv('data/stock-selection.csv', dtype={'代码': str})
codes = sel['代码'].tolist()
names = dict(zip(sel['代码'], sel['简称']))
industries = dict(zip(sel['代码'], sel['申万一级行业']))
sel""")

md("""### Step 3：结果解读

10 只股票覆盖**银行、食品饮料、家用电器、汽车、非银金融、医药生物、电力设备、公用事业、计算机**等 8 个申万一级行业（家用电器 2 只），全部于 2013 年 9 月之前上市，样本期内无退市，满足"样本开始前已上市、覆盖完整"的要求。美的与格力构成同行业对子；长江电力代表低波动防御型资产，比亚迪、隆基绿能、科大讯飞代表高波动成长型资产，为组合风险分析提供足够的横截面差异。""")

# ============ 2 数据检查 ============
md("""## 2. 数据读取与检查

### Step 1：分析说明

将 10 只股票的行情按**交易日并集日历**合并为面板，检查以下项目：

- **主键唯一性**：（股票代码, 日期）组合不得重复；
- **日期排序**：各序列严格按日期升序；
- **覆盖期间与有效观测数**：每只股票的实际起止日期与样本期内有效观测数；
- **缺失与停牌**：识别并集日历下缺失行情的日期，判断是停牌还是数据错误；
- **异常收益**：检查后复权收益是否有超出涨跌停制度允许范围的观测（|r| > 20%）；
- **单位**：价格单位为元/股，成交量为手，市值为亿元（第 6 节核验）。""")

code("""# 读取行情面板（并集日历）：不复权 / 前复权 / 后复权 + 成交额
# 后复权主口径改用新浪源（腾讯 hfq 存在复权因子漂移，见 2.3 节诊断）
raw_p, qfq_p, hfq_p, hfq_tx_p, amt = {}, {}, {}, {}, {}
for c in codes:
    r_ = pd.read_csv(f'data/raw/tx_daily_{c}_raw.csv', parse_dates=['date']).set_index('date')
    q_ = pd.read_csv(f'data/raw/tx_daily_{c}_qfq.csv', parse_dates=['date']).set_index('date')
    h_ = pd.read_csv(f'data/raw/sina_daily_{c}_hfq.csv', parse_dates=['date']).set_index('date')
    t_ = pd.read_csv(f'data/raw/tx_daily_{c}_hfq.csv', parse_dates=['date']).set_index('date')
    raw_p[c] = r_['close']; qfq_p[c] = q_['close']; amt[c] = r_['amount']
    hfq_p[c] = h_['close'].reindex(r_.index)      # 新浪后复权（主口径）
    hfq_tx_p[c] = t_['close']                      # 腾讯后复权（仅作对照）
P_raw = pd.DataFrame(raw_p); P_qfq = pd.DataFrame(qfq_p)
P_hfq = pd.DataFrame(hfq_p); P_hfq_tx = pd.DataFrame(hfq_tx_p); AMT = pd.DataFrame(amt)
# 日期索引对齐检查：不复权与前复权须完全一致；后复权（新浪）在样本期内须无缺失
assert P_raw.index.equals(P_qfq.index), '不复权与前复权日期索引不一致'
# 缺失位置必须与不复权序列完全一致（即停牌日一致，而非数据源缺数）
assert P_hfq.isna().equals(P_raw.isna()), '新浪后复权的缺失位置与不复权不一致'
print('不复权 / 前复权 日期索引完全对齐 ✓')
print('新浪后复权的缺失日期与不复权完全一致（仅停牌日）✓，样本期内无数据源缺数')
print('末日 2026-09-16 收盘价对照（前复权应与不复权完全相等）:')
print(pd.DataFrame({'不复权': P_raw.iloc[-1], '前复权': P_qfq.iloc[-1],
                    '后复权(新浪)': P_hfq.iloc[-1]}).rename(index=names).round(2).to_string())

print('== 成交额样例（腾讯接口 amount 字段，按数量级推断单位为万元）==')
print(f"招商银行 2026-09-16 成交额 {AMT['600036'].iloc[-1]:,.0f} 万元 ≈ {AMT['600036'].iloc[-1]/1e4:.1f} 亿元，量级合理")
print(f"贵州茅台 2026-09-16 成交额 {AMT['600519'].iloc[-1]:,.0f} 万元 ≈ {AMT['600519'].iloc[-1]/1e4:.1f} 亿元")

print('== 主键唯一性（逐股票检查重复日期）==')
for c in codes:
    assert not P_raw[c].index.duplicated().any(), f'{c} 存在重复日期'
print('10 只股票均无重复日期，主键 (股票, 日期) 唯一 ✓')

print('\\n== 日期排序 ==')
print('所有序列严格升序:', all(P_raw[c].index.is_monotonic_increasing for c in codes), '✓')

print('\\n== 覆盖期间与有效观测数 ==')
cover = pd.DataFrame({
    '起始日': P_raw.apply(lambda s: s.first_valid_index().date()),
    '结束日': P_raw.apply(lambda s: s.last_valid_index().date()),
    '全样本行数': P_raw.notna().sum(axis=0),
    '样本期(2021-01-01~2026-09-16)有效观测': P_raw[(P_raw.index >= '2021-01-01') & (P_raw.index <= '2026-09-16')].notna().sum(),
})
print(f'并集交易日历: {P_raw.index.min().date()} ~ {P_raw.index.max().date()}，共 {len(P_raw)} 个交易日')
cover""")

md("""### Step 3：结果解读

并集日历共 1386 个交易日（2020-12-30 至 2026-09-16），主键唯一、排序无误。8 只股票覆盖完整（样本期 1384 个交易日中缺 0 天）；**中信证券缺 6 个交易日、长江电力缺 11 个交易日**，合计 17 天，下一步判断其性质。""")

md("""### Step 2 续：缺失、停牌与异常收益检查""")

code("""# 缺失日期定位
sample = P_raw[(P_raw.index >= '2021-01-01') & (P_raw.index <= '2026-09-16')]
miss_tbl = []
for c in codes:
    miss_days = sample[sample[c].isna()].index
    if len(miss_days) > 0:
        # 归并为连续区间
        breaks = miss_days.to_series().diff().dt.days.fillna(0) != 1
        grp = breaks.cumsum()
        for g, idx in miss_days.to_series().groupby(grp).groups.items():
            miss_tbl.append({'股票': names[c], '缺失区间': f'{idx.min().date()} ~ {idx.max().date()}', '交易日数': len(idx)})
print('== 缺失行情明细（应为真实停牌，非数据错误）==')
print(pd.DataFrame(miss_tbl).to_string(index=False))

print('\\n== 异常收益检查（后复权价计算，|r|>20% 超出涨跌停范围即数据可疑）==')
suspicious = 0
for c in codes:
    r_own = P_hfq[c].dropna().pct_change(fill_method=None).dropna()
    bad = r_own[abs(r_own) > 0.20]
    if len(bad):
        suspicious += len(bad)
        print(f'{names[c]}: {len(bad)} 天', [(str(d.date()), f'{v:.1%}') for d, v in bad.items()])
print('结论：无 |r|>20% 的观测，后复权收益全部落在涨跌停制度允许范围内 ✓' if suspicious == 0 else '存在可疑观测，需回查')

print('\\n== 不复权价格跳变（|ΔP/P|>11%，提示除权除息或数据错误）==')
for c in codes:
    r_raw = P_raw[c].dropna().pct_change(fill_method=None).dropna()
    jumps = r_raw[abs(r_raw) > 0.11]
    if len(jumps):
        print(f'{names[c]}:')
        for d, v in jumps.items():
            # 同日后复权收益（真实收益）
            r_adj = P_hfq[c].pct_change(fill_method=None).get(d, np.nan)
            print(f'  {d.date()}: 不复权 {v:+.1%}，同日后复权收益 {r_adj:+.1%}'
                  + ('  → 除权除息所致，非真实暴跌' if abs(r_adj) < 0.11 else '  → 需回查'))""")

md("""### Step 3：结果解读

- **缺失即停牌**：中信证券 2022-01-19 至 01-26 连续 6 个交易日无行情，长江电力 2021-11-29 至 12-10 连续 10 个交易日及 2022-10-26 单日无行情。两只股票其余日期行情连续，且缺失均为连续区间（中信证券跨周末共 6 个交易日，表中显示为两段），符合**重大事项停牌**特征：中信证券 2022 年 1 月为配股缴款停牌（第 6 节校准股本在 2022-01-27 即复牌次日增加 12.0%，与配股股份到账完全吻合）；长江电力 2021-11 末起为筹划重大资产重组停牌（对应 2023 年发行股份购买资产完成后股本小幅增加），并非数据传输错误。停牌期间无成交价，处理方式见第 3 节。
- **无异常收益**：全部后复权日收益均未超出 ±20%，最大单日涨跌幅约 ±10%（与主板涨跌停制度一致），数据质量良好。
- **4 个除权跳变点**：比亚迪 2025-07-29（不复权 −66.9%）、恒瑞医药 2021-06-10（−13.3%）、隆基绿能 2021-06-23（−27.3%）与 2022-06-06（−24.2%）。这些日期**不复权价格大幅下跌、而后复权收益正常**，是送股/转增/派息除权的典型特征，说明复权处理正确捕捉了公司行为。其中比亚迪的跳变幅度对应大比例转增（第 6 节校准股本同期从约 29 亿股升至约 87 亿股，可交叉验证）。""")

md("""### Step 2 续 3：复权口径核验与数据源诊断

**为什么必须核验**：作业要求"跨来源检查代码、日期和复权口径""解释复权口径"。但复权序列本身也可能出错——本文在核验中确实发现了数据源缺陷，并据此更换了后复权数据来源。下面做五项交叉验证：

1. **末日对齐**：前复权价在样本末日必须等于不复权价（前复权以最新价为基准），确认复权基准正确；
2. **无除权日收益率恒等**：在没有除权除息的交易日，后复权价与不复权价只差一个常数因子，**两者的日收益率必须完全相等**。这是检验复权序列是否失真最直接的判据；
3. **涨跌停约束**：主板非 ST 股票单日收益率应在 ±10% 以内，涨停日的复权收益应显示约 +10%；
4. **独立复算交叉验证**：用"不复权价 + 分红送转方案"自行复算总回报指数，与两条后复权序列对照；
5. **三口径累计收益对比**：量化误用不复权价的后果。""")

code("""# ---- 复权口径核验与数据源诊断 ----
R_raw_all = P_raw.pct_change(fill_method=None)
R_qfq_all = P_qfq.pct_change(fill_method=None)
R_hfq_all = P_hfq.pct_change(fill_method=None)      # 新浪后复权（主口径）
R_hfq_tx  = P_hfq_tx.pct_change(fill_method=None)   # 腾讯后复权（对照）
base = P_hfq[P_hfq.index < '2021-01-01'].index.max()   # 2020-12-31
S = (P_raw.index >= '2021-01-01') & (P_raw.index <= '2026-09-16')

# (1) 末日对齐：前复权末日价 == 不复权末日价
gap_last = (P_qfq.iloc[-1] - P_raw.iloc[-1]).abs().max()
print(f'(1) 末日(2026-09-16) 前复权与不复权价最大绝对差 = {gap_last:.2e} 元 → 复权基准正确 ✓')

# (2) 非除权日：复权收益应恒等于不复权收益
ev = pd.read_csv('data/raw/tx_div_events.csv')
exd = set(pd.to_datetime(ev['除权日']))
nonexd = [d for d in P_raw.index if d not in exd]
d_sina = (R_hfq_all - R_raw_all).loc[nonexd].abs()
d_tx   = (R_hfq_tx  - R_raw_all).loc[nonexd].abs()
print('\\n(2) 非除权日 |后复权收益 − 不复权收益|（理论值应为 0）:')
print(f'    新浪后复权：最大 {d_sina.max().max():.4%} ，中位数 {d_sina.stack().median():.4%}')
print(f'    腾讯后复权：最大 {d_tx.max().max():.4%} ，中位数 {d_tx.stack().median():.4%}')
cmp_d = pd.DataFrame({'新浪最大(百分点/日)': d_sina.max() * 100,
                      '腾讯最大(百分点/日)': d_tx.max() * 100}).rename(index=names)
print(cmp_d.round(3).sort_values('腾讯最大(百分点/日)', ascending=False).to_string())

# (3) 涨跌停约束：主板非 ST 股单日 |r| 应 ≤ 10.05%
lim = pd.DataFrame({
    '不复权最大(%)': R_raw_all[S].max() * 100,
    '新浪最大(%)': R_hfq_all[S].max() * 100,
    '新浪最小(%)': R_hfq_all[S].min() * 100,
    '腾讯最大(%)': R_hfq_tx[S].max() * 100,
    '腾讯最小(%)': R_hfq_tx[S].min() * 100,
}).rename(index=names)
print('\\n(3) 涨跌停制度约束检验（主板非 ST 股单日 |r| 应 ≤ 10.05%）:')
print(lim.round(2).to_string())
print('\\n    中信证券 2024-09-27 / 09-30 / 10-08（三日实际涨停，当日均无除权事件）:')
for d in ['2024-09-27', '2024-09-30', '2024-10-08']:
    t = pd.Timestamp(d)
    print(f'      {d}  不复权 {R_raw_all.loc[t, "600030"]:+.2%}   '
          f'新浪后复权 {R_hfq_all.loc[t, "600030"]:+.2%}   '
          f'腾讯后复权 {R_hfq_tx.loc[t, "600030"]:+.2%}')
print('    → 腾讯后复权把三个涨停压缩成约 +8.5%，与当日真实涨跌不符；新浪后复权正确显示为约 +10%。')

# (4) 独立复算：不复权价 + 分红送转方案 自行构造总回报指数
import re
def parse_plan(s):
    s = str(s); cash = 0.0; extra = 0.0
    m = re.search(r'派([\\d.]+)元', s)
    if m: cash = float(m.group(1)) / 10
    for k in ['送', '转']:
        m = re.search(k + r'([\\d.]+)股', s)
        if m: extra += float(m.group(1))
    return cash, 1 + extra / 10

rows = []
for c in codes:
    evc = ev[ev['代码'].astype(str).str.zfill(6) == c]
    plans = {pd.Timestamp(r['除权日']): parse_plan(r['方案']) for _, r in evc.iterrows()}
    p = P_raw[c].dropna()
    W = pd.Series(index=p.index, dtype=float); W.iloc[0] = p.iloc[0]
    for t in range(1, len(p)):
        d = p.index[t]; D, f = 0.0, 1.0
        if d in plans: D, f = plans[d]
        W.iloc[t] = W.iloc[t - 1] * (f * p.iloc[t] + D) / p.iloc[t - 1]
    ws = W.loc[base:].dropna()
    sh = P_hfq[c].loc[base:].dropna(); th = P_hfq_tx[c].loc[base:].dropna()
    rows.append({'股票': names[c],
                 '独立复算(%)': (ws.iloc[-1] / ws.iloc[0] - 1) * 100,
                 '新浪hfq(%)': (sh.iloc[-1] / sh.iloc[0] - 1) * 100,
                 '腾讯hfq(%)': (th.iloc[-1] / th.iloc[0] - 1) * 100})
chk = pd.DataFrame(rows)
chk['新浪偏差'] = chk['新浪hfq(%)'] - chk['独立复算(%)']
chk['腾讯偏差'] = chk['腾讯hfq(%)'] - chk['独立复算(%)']
print('\\n(4) 全期总回报（2020-12-31 → 2026-09-16）三方对照:')
print(chk.round(1).to_string(index=False))
print(f'\\n    平均绝对偏差：新浪 {chk["新浪偏差"].abs().mean():.1f} 个百分点，'
      f'腾讯 {chk["腾讯偏差"].abs().mean():.1f} 个百分点')
print(f'    最大绝对偏差：新浪 {chk["新浪偏差"].abs().max():.1f} 个百分点，'
      f'腾讯 {chk["腾讯偏差"].abs().max():.1f} 个百分点')
na_ev = ev[ev['方案'].isna()]
if len(na_ev):
    print(f'    注：{len(na_ev)} 条事件方案字段缺失（中信证券 2022-01-27，实为配股除权），'
          '独立复算未处理配股，故中信证券一行以复权序列为准。')

# (5) 三口径样本期累计收益对比
cum = pd.DataFrame({
    '不复权累计(%)': (P_raw[S].iloc[-1] / P_raw.loc[base] - 1) * 100,
    '前复权累计(%)': (P_qfq[S].iloc[-1] / P_qfq.loc[base] - 1) * 100,
    '后复权累计(%)': (P_hfq[S].iloc[-1] / P_hfq.loc[base] - 1) * 100,
}).rename(index=names)
cum['复权-不复权(百分点)'] = cum['后复权累计(%)'] - cum['不复权累计(%)']
print('\\n(5) 样本期累计收益（2020-12-31 → 2026-09-16）三口径对比:')
print(cum.round(2).sort_values('复权-不复权(百分点)', ascending=False).to_string())

# (6) 分红除权事件日：不复权假跳变 vs 复权真实收益
ev = pd.read_csv('data/raw/tx_div_events.csv')
rows = []
for _, e in ev.iterrows():
    d = pd.Timestamp(e['除权日']); c = str(e['代码']).zfill(6)
    if not (pd.Timestamp('2021-01-01') <= d <= pd.Timestamp('2026-09-16')):
        continue
    rows.append({'股票': names[c], '除权日': d.date(), '方案': e['方案'],
                 '不复权(%)': R_raw_all.loc[d, c] * 100,
                 '前复权(%)': R_qfq_all.loc[d, c] * 100,
                 '后复权(%)': R_hfq_all.loc[d, c] * 100})
ev_tbl = pd.DataFrame(rows)
ev_tbl['假跳变幅度(百分点)'] = ev_tbl['不复权(%)'] - ev_tbl['后复权(%)']
big = ev_tbl[ev_tbl['假跳变幅度(百分点)'].abs() >= 3].copy()
print(f'\\n(6) 样本期内分红除权事件 {len(ev_tbl)} 次，其中不复权假跳变 ≥3 个百分点的 {len(big)} 次:')
print(big.round(2).to_string(index=False))
print(f'\\n全部 {len(ev_tbl)} 次除权日：不复权收益均值 {ev_tbl["不复权(%)"].mean():.2f}%，'
      f'复权收益均值 {ev_tbl["后复权(%)"].mean():.2f}%')
print(f'若误用不复权价，10 只股票累计收益平均被低估 {cum["复权-不复权(百分点)"].mean():.1f} 个百分点')""")

md("""### Step 3：结果解读（复权口径核验与数据源诊断）

**(1) 复权基准正确**：末日（2026-09-16）前复权价与不复权价完全相同（差 0.00 元），两条复权序列都以最新实际成交价为基准，日期索引完全对齐。

**(2) 关键发现：腾讯后复权序列失真，已弃用**。在没有除权除息的交易日，后复权价与不复权价只相差一个常数因子，**两者的日收益率必须完全相等**。实测结果：

| 检验项 | 新浪后复权 | 腾讯后复权 |
|---|---|---|
| 非除权日两口径收益率偏差（最大） | **0.014%** | **3.11%** |
| 非除权日两口径收益率偏差（中位数） | 0.0005% | 0.063% |

新浪序列的偏差在浮点精度级，腾讯序列的偏差是它的 200 倍以上，且**逐日累积**。这说明腾讯的复权因子在无除权日仍在漂移（中信证券 2024-08-26 至 12-19 期间 hfq/raw 从 5.68 漂到 5.28，漂移 6.3%），不是合格的后复权序列。

**(3) 涨跌停约束进一步印证**：主板非 ST 股单日涨跌幅上限为 ±10%。新浪后复权的最大/最小单日收益与不复权价**逐股完全吻合**（比亚迪 +10.00%/−10.01%、中信证券 +10.01%、隆基绿能 +10.03%）；腾讯后复权则系统性压缩波动——格力电器单日最大 +9.64% 被压成 +6.53%，招商银行 +9.07% 被压成 +7.23%。最典型的是中信证券 2024-09-27、09-30、10-08 三个涨停日：不复权 +10.01%/+9.99%/+10.00%，新浪后复权 +10.00%/+9.99%/+10.00%，**腾讯后复权只有 +8.45%/+8.55%/+8.67%**。

**(4) 独立复算交叉验证**：用"不复权价 + 分红送转方案"自行复算总回报指数（分红按除权日再投资），与两条序列对照：

- **新浪：平均绝对偏差 0.8 个百分点**，10 只股票中 9 只在 0.9 个百分点以内（招行 +0.1、茅台 0.0、比亚迪 0.0、恒瑞 0.0、隆基 0.0、科大讯飞 0.0）；
- **腾讯：平均绝对偏差 5.2 个百分点，最大 24.3 个百分点**（长江电力：独立复算 +81.8%，新浪 +81.5%，腾讯仅 +57.5%；招商银行低估 7.4、美的集团低估 7.6 个百分点）。偏差随股息率系统性放大——分红越多的股票被低估越严重；
- 中信证券一行偏差 6.3 个百分点，是因为 2022-01-27 的**配股**除权在接口的方案字段中缺失，独立复算未处理配股，故该股以复权序列为准。

**结论：本文后复权序列改用新浪财经数据**。腾讯序列的三处证据（因子漂移、涨停被压缩、总回报低估）彼此印证，且新浪序列同时通过了与不复权价的逐日恒等检验、涨跌停约束检验和独立复算检验。

**(5) 不复权价仍会系统性低估收益**：三口径累计收益对比显示，用不复权价计算的累计收益**平均被低估 26.0 个百分点**，其中比亚迪被低估 90.8 个百分点（大比例送转）、长江电力 33.0、格力电器 30.7、招商银行 29.5——分红与送转越慷慨，低估越严重。

**(6) 除权是"假跳变"的直接证据**：样本期内 10 只股票共发生 **73 次分红除权事件**。这些日子不复权收益均值 **−3.74%**，而复权收益均值 **+0.31%**（正常量级）——不复权价把"公司向股东派钱/送股"错误记成了"股价亏钱"。""")

md("""### Step 2 续 4：大幅波动的甄别——真实行情还是数据错误

数据检查中注意到，中信证券在 2024 年 9 月底至 10 月初出现了一次幅度很大的上涨。收益曲线出现异常波动时，必须先判定它是**真实市场行情**还是**数据错误**。判据是同时满足三条：① 不复权价同步变动（排除单一复权口径错误）；② 成交量显著放大（排除复权/价差错误，真实的资金推动必然放量）；③ 同期其他股票同步变动（排除个股数据错误）。""")

code("""# 2024 年 9 月行情甄别
d0, d1 = pd.Timestamp('2024-09-23'), pd.Timestamp('2024-10-08')
print('== 判据①：不复权价与后复权价是否同步变动 ==')
rr = (P_raw.loc[d1, '600030'] / P_raw.loc[d0, '600030'] - 1) * 100
hh = (P_hfq.loc[d1, '600030'] / P_hfq.loc[d0, '600030'] - 1) * 100
print(f'  中信证券 {d0.date()} → {d1.date()}：不复权 {rr:+.1f}%，后复权 {hh:+.1f}%')
print(f'  不复权价 {P_raw.loc[d0, "600030"]:.2f} → {P_raw.loc[d1, "600030"]:.2f} 元')

print('\\n== 判据②：成交量是否显著放大 ==')
a = AMT['600030'].dropna()
base_amt = a.loc['2024-01-01':'2024-08-31'].mean()
seg_amt = a.loc[d0:d1].mean()
print(f'  2024 年 1–8 月日均成交额 {base_amt/1e4:.2f} 亿元，该区间日均 {seg_amt/1e4:.2f} 亿元，'
      f'放大 {seg_amt/base_amt:.1f} 倍')

print('\\n== 判据③：同期其他股票是否同步变动 ==')
peer = ((P_hfq.loc[d1] / P_hfq.loc[d0] - 1) * 100).rename(names).sort_values(ascending=False)
print(peer.round(1).to_string())
print(f'\\n  上涨股票 {(peer > 0).sum()}/10 只，中位数 {peer.median():.1f}%，'
      f'最高 {peer.max():.1f}%（{peer.idxmax()}），最低 {peer.min():.1f}%（{peer.idxmin()}）')

n_up = int((R_raw_all.loc[d0:d1, '600030'] >= 0.0995).sum())
print(f'\\n  中信证券该区间涨停 {n_up} 次（不复权单日收益 ≥ 9.95%，即触及 10% 涨停板）')""")

md("""**结论：该次上涨是真实市场行情，三条判据全部满足，不是数据错误。**

- **判据①成立**：不复权价与后复权价同步大幅上涨（两者涨幅一致），说明不是某一条复权序列的异常；
- **判据②成立**：该区间日均成交额放大到此前 8 个月日均的 **3.1 倍**（82 亿元 → 253 亿元），是真实资金推动，而复权错误或价差错误不会产生放量；
- **判据③成立**：10 只样本股在区间内**全部上涨**，中位数 +31.0%，且呈现清晰的风险分层——中信证券（+54.9%）、隆基绿能（+51.5%）、科大讯飞（+40.4%）等高 β 品种涨幅居前，防御性的长江电力仅涨 +3.6%。这是典型的**全市场普涨（beta 行情）**特征，个股数据错误无法让 10 只互不相关的股票同步上涨。

**市场背景**：2024 年 9 月 24 日国务院新闻办发布会推出政策组合拳（降准、下调存量房贷利率、创设证券基金保险互换便利与股票回购增持专项再贷款），9 月 26 日中央政治局会议提前部署经济工作，A 股随之大幅上涨，券商板块作为高 β 品种领涨，中信证券在此期间出现三个涨停。

**它与"除权假跳变"的区别**（作业要求"检查异常收益"时用于分辨两类异常）：

| 特征 | 除权除息假跳变（数据/口径问题） | 真实行情波动（如本次） |
|---|---|---|
| 方向 | 几乎总是**单日向下** | 可上可下 |
| 成交量 | 无异动 | 显著放大 |
| 其他股票 | 仅该股跳变 | 同板块/全市场同步 |
| 复权后 | 跳变消失 | 跳变依然存在 |
| 处理 | 改用复权价即可消除 | 属真实收益，应保留 |

需要强调的是：**改用复权价只能消除除权造成的假跳变，不会也不应消除真实的市场波动**。本作业的收益曲线在 2024 年 9 月保留这段上涨，正是数据正确的表现。""")

# ============ 3 收益率 ============
md("""## 3. 收益率计算

### Step 1：分析说明

采用日简单收益率，基于**后复权收盘价**计算：

$$r_{i,t}=\\dfrac{P^{adj}_{i,t}}{P^{adj}_{i,t-1}}-1$$

口径说明：

- 新浪财经的后复权价以上市首日为基准向后复权累乘，**包含分红再投资与送转股调整**，$r_{i,t}$ 为考虑公司行为的持有期收益率；后复权价本身不是实际成交价格（实际成交价为不复权价，见第 5.1b 节）；该序列已在 2.3 节通过三项检验：与非除权日不复权收益逐日恒等（最大偏差 0.014%）、符合涨跌停约束、与独立复算的总回报吻合（平均偏差 0.8 个百分点）；
- **口径统一，不混用**：价格展示与收益率计算使用**同一条后复权序列**；前复权序列仅用于末日基准校验（2.3 节已核验其分红处理口径与后复权不同，故不参与计算）；若误用不复权价，除权日会出现 −66.94% 级别的虚假暴跌，全期累计收益平均被低估 26.0 个百分点；
- 收益率在**并集交易日历**上计算：停牌期间该股收益为缺失（NaN），**不填零**；复牌首日因前一交易日无收盘价，收益同样记缺失——若直接把复牌日价格相对停牌前最后一日的跨日变化当作单日收益，会把整个停牌期的累计涨跌压缩到一天，夸大当日波动，作业明确禁止这种做法，故处理为缺失；
- 损失评估：中信证券 7 天（6 个停牌日 + 1 个复牌日）、长江电力 13 天（11 + 2），占样本 1384 个交易日的 0.5% 和 0.9%，对描述统计影响很小；
- 样本期统一为 2021-01-04（2021 年首个交易日）至 2026-09-16，首日收益使用 2020-12-31（样本前最后一个交易日）的后复权价计算。""")

code("""# 面板收益：并集日历 pct_change（复牌首日自动为 NaN）
R = P_hfq.pct_change(fill_method=None)
R = R[(R.index >= '2021-01-01') & (R.index <= '2026-09-16')]
print(f'样本期: {R.index.min().date()} ~ {R.index.max().date()}，T = {len(R)} 个交易日')
print('\\n各股票缺失日收益（停牌及复牌首日）:')
print(R.isna().sum()[R.isna().sum() > 0].rename(index=lambda c: f'{c} {names[c]}').to_string())
print('\\n其他 8 只股票无缺失')
R.iloc[:3, :5]""")

md("""### Step 3：结果解读

样本期共 **1384 个有效交易日**（2021-01-04 至 2026-09-16）。中信证券缺失 7 天、长江电力缺失 13 天，其余 8 只股票完整。缺失日收益在描述统计中按 `NaN` 跳过（`scipy.stats` 与 `pandas` 默认忽略缺失），在组合构造中当日对该股权重置零并在其余股票内重新归一（见第 6 节）。""")

# ============ 4 描述统计 ============
md("""## 4. 描述统计

### Step 1：分析说明

对每只股票报告：有效观测数、日均值、日标准差、最小值、中位数、最大值、**偏度、超额峰度**，并补充几何年化收益率与年化波动率（日标准差 × √252），用于横截面比较收益—风险特征。要点：哪只股票收益最高/最低、波动最大/最小；收益分布是否右偏/厚尾（偏度、超额峰度），及其对极端风险的含义。""")

code("""def desc_col(s):
    s = s.dropna()
    nav_end = (1 + s).prod()
    return pd.Series({
        '有效观测数': len(s),
        '日均值(%)': s.mean() * 100,
        '日标准差(%)': s.std() * 100,
        '最小值(%)': s.min() * 100,
        '中位数(%)': s.median() * 100,
        '最大值(%)': s.max() * 100,
        '偏度': stats.skew(s),
        '超额峰度': stats.kurtosis(s),  # Fisher 口径，正态分布为 0
        '年化收益(%)': (nav_end ** (252 / len(s)) - 1) * 100,
        '年化波动(%)': s.std() * np.sqrt(252) * 100,
    })

desc = pd.DataFrame({f'{c} {names[c]}': desc_col(R[c]) for c in codes}).T
desc.round(2)""")

md("""### Step 3：结果解读

**收益与风险横截面差异显著**：

- 年化收益最高的是长江电力（**+11.21%**，年化波动仅 17.26%，样本内唯一的"高收益低波动"组合），最低的是隆基绿能（**−22.81%**，年化波动 42.48%）；比亚迪年化 +5.47% 但波动高达 39.11%。
- 波动最小的是长江电力（17.26%）、格力电器（24.44%），最大的是科大讯飞（42.67%）与隆基绿能（42.48%）——高波动成长股在本样本期内普遍表现为"高波动、低甚至负收益"，即承担的风险未获得收益补偿。
- **分布形态**：10 只股票偏度全部为正（0.14 ~ 0.94），超额峰度全部显著为正（1.9 ~ 6.0），说明日收益分布**右偏且厚尾**：极端大涨（如茅台 +9.50%、中信证券 +10.01%）与极端大跌（隆基绿能 −10.02%、科大讯飞 −10.00%）同时存在，正态分布会低估极端日出现的频率。中信证券偏度 0.94、超额峰度 5.99 为全场最高，与其高贝塔属性（行情驱动）一致。

**核心发现**：(1) 样本期内"白马龙头"组合整体表现平淡，8/10 股票年化收益绝对值不足 6%；(2) 风险与收益不匹配，隆基、科大讯飞高波动负收益；(3) 收益分布普遍厚尾右偏，极端日集中于 2021–2022 与 2024–2025 的市场剧烈波动期。""")

# ============ 5 图 ============
md("""## 5. 图形分析

### 5.1 后复权收盘价时序

**Step 1：分析说明**：分面展示 10 只股票的**后复权收盘价**（单位：元/股，各面板独立纵轴）。后复权价以上市首日价为基准向后累乘，已包含分红再投资与送转股调整，序列连续可比，**不出现除权除息造成的虚假断崖**（比亚迪 2025-07 不复权价从约 337 元跳到 111 元，后复权价当日反而上涨 0.36%）。这里不用不复权价：其向下跳变是分红、送转等公司行为，并非投资亏损。""")

code("""fig, axes = plt.subplots(2, 5, figsize=(16, 6.5), sharex=True)
for ax, c in zip(axes.ravel(), codes):
    ax.plot(P_hfq.index, P_hfq[c], lw=0.8, color='#1f4e9c')
    ax.set_title(f'{c} {names[c]}', fontsize=10)
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.3)
    ax.annotate(f'{industries[c]}', xy=(0.02, 0.92), xycoords='axes fraction', fontsize=8, color='#666666')
fig.suptitle('图1  10 只股票后复权收盘价（2021-01 至 2026-09，元/股，含分红再投资与送转调整）', fontsize=13)
fig.autofmt_xdate(rotation=30)
plt.tight_layout()
plt.savefig('figs/fig1-hfq-close.png', dpi=150, bbox_inches='tight')
plt.show()""")

md("""**Step 3：结果解读**：改用复权价后，所有序列**连续无断崖**——比亚迪 2025-07 的"断崖"消失（那一步是每 10 股送 8 股转增 12 股并派现 39.74 元的除权，股东财富并未损失），隆基绿能 2021-06、2022-06 与恒瑞医药 2021-06 的向下跳变同样消失。价格路径因此反映真实的投资回报：长江电力稳步上行并在样本期末创新高；贵州茅台自 2021 年初高点后长期回落；隆基绿能与恒瑞医药持续下行——与第 4 节的年化收益排序完全一致。后复权价因累乘了历年分红，绝对水平高于实际成交价（如茅台约 8,883 元），故各面板保留独立纵轴；它衡量的是"长期持有 1 股的累计财富"，而非当时的报价。""")

md("""### 5.1b 复权前后对比：以比亚迪为例

**Step 1：分析说明**：为直观说明复权的必要性，把比亚迪的不复权价与后复权价画在同一图（各自独立纵轴）——两者的差别即公司行为造成的虚假价格变动。""")

code("""c = '002594'
fig, ax1 = plt.subplots(figsize=(12, 5))
ax1.plot(P_raw.index, P_raw[c], lw=1.0, color='#c00000', label='不复权价（实际成交价）')
ax1.set_ylabel('不复权价（元/股）', color='#c00000'); ax1.tick_params(axis='y', labelcolor='#c00000')
ax2 = ax1.twinx()
ax2.plot(P_hfq.index, P_hfq[c], lw=1.0, color='#1f4e9c', label='后复权价（含分红再投资与送转）')
ax2.set_ylabel('后复权价（元/股）', color='#1f4e9c'); ax2.tick_params(axis='y', labelcolor='#1f4e9c')
ax1.set_title('图1b  比亚迪：不复权价 vs 后复权价（2021-01 至 2026-09）', fontsize=13)
ax1.grid(alpha=0.3); fig.autofmt_xdate(rotation=30)
h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=10)
plt.tight_layout()
plt.savefig('figs/fig1b-raw-vs-hfq.png', dpi=150, bbox_inches='tight')
plt.show()

d = pd.Timestamp('2025-07-29')
prev = P_hfq.index[P_hfq.index < d][-1]
print(f'比亚迪 2025-07-29 除权除息日（方案：10派39.74元送8股转12股）:')
print(f'  不复权价 {P_raw.loc[prev, c]:.2f} → {P_raw.loc[d, c]:.2f} 元，当日收益 {R_raw_all.loc[d, c]:+.2%}（虚假暴跌）')
print(f'  后复权价 {P_hfq.loc[prev, c]:.2f} → {P_hfq.loc[d, c]:.2f} 元，当日收益 {R_hfq_all.loc[d, c]:+.2%}（真实收益）')""")

md("""**Step 3：结果解读**：红色（不复权）曲线在 2025-07-29 出现 −66.94% 的垂直断崖，蓝色（后复权）曲线同日反而上涨 0.36%——这一天的"暴跌"完全是每 10 股送 8 股、转增 12 股并派现 39.74 元造成的除权，股东财富并未损失。这说明**只要使用复权价，收益曲线就不会出现异常骤升骤降**；反过来说，若价格或净值曲线上出现这类垂直断崖，即可断定用了未复权价格。""")

md("""### 5.2 累计收益曲线（起点 = 1）

**Step 1：分析说明**：以后复权价计算 `NAV = P_t / P_{2020-12-31}`，起点归一为 1，单轴对比 10 只股票的累计表现（含分红再投资）。""")

code("""base_day = P_hfq[P_hfq.index < '2021-01-01'].index.max()  # 2020-12-31
NAV_stock = P_hfq.loc[base_day:, :] / P_hfq.loc[base_day]
NAV_stock = NAV_stock[(NAV_stock.index <= '2026-09-16')]

fig, ax = plt.subplots(figsize=(12, 6))
for c in codes:
    ax.plot(NAV_stock.index, NAV_stock[c], lw=1.1, label=f'{names[c]}({industries[c][:2]})')
ax.axhline(1.0, color='gray', ls='--', lw=0.8)
ax.set_title('图2  累计收益曲线（后复权，2020-12-31 = 1，含分红再投资）', fontsize=13)
ax.set_ylabel('累计净值')
ax.legend(ncol=5, fontsize=9, loc='upper left')
ax.grid(alpha=0.3)
fig.autofmt_xdate(rotation=30)
plt.tight_layout()
plt.savefig('figs/fig2-cum-nav.png', dpi=150, bbox_inches='tight')
plt.show()

end_nav = NAV_stock.iloc[-1].rename(lambda c: f'{c} {names[c]}').sort_values(ascending=False)
print('期末累计净值（2026-09-16）:')
print(end_nav.round(3).to_string())""")

md("""**Step 3：结果解读**：期末累计净值最高的是长江电力（1.82）与比亚迪（1.34），最低的是隆基绿能（0.24）与恒瑞医药（0.48）。样本期跨越 2021 年初核心资产泡沫顶部、2022–2024 初的持续下行、2024-09 以来的政策驱动反弹，多数消费与医药白马尚未收复 2021 年初高点。隆基绿能受光伏行业产能过剩与价格战冲击，净值一路下行，是组合中最大的拖累项；长江电力凭借稳定的分红再投资与低波动，净值稳步攀升至 1.82，是唯一全程未出现深度回撤的标的。中信证券净值曲线在 2024 年 9 月底至 10 月初有一段陡峭上升（10 个交易日约 +55%），这是 2024 年"9·24 行情"的真实市场波动，已在第 2.4 节用三条判据验证，并非数据错误。""")

md("""### 5.3 日收益率时序

**Step 1：分析说明**：分面展示日收益率，叠加 ±10% 参考线（主板涨跌停幅度近似），检查异常波动日及其出现时点。""")

code("""fig, axes = plt.subplots(2, 5, figsize=(16, 6.5), sharex=True, sharey=True)
for ax, c in zip(axes.ravel(), codes):
    ax.plot(R.index, R[c] * 100, lw=0.4, color='#333333')
    ax.axhline(10, color='#c00000', ls=':', lw=0.8); ax.axhline(-10, color='#008000', ls=':', lw=0.8)
    ax.set_title(f'{names[c]}', fontsize=10); ax.tick_params(labelsize=8); ax.grid(alpha=0.3)
fig.suptitle('图3  日收益率时序（%，虚线为 ±10% 涨跌停参考）', fontsize=13)
fig.autofmt_xdate(rotation=30)
plt.tight_layout()
plt.savefig('figs/fig3-daily-returns.png', dpi=150, bbox_inches='tight')
plt.show()

extreme = (R.abs() > 0.095).sum()
print('触及 ±9.5% 以上的极端日数量:')
print(extreme[extreme > 0].rename(lambda c: f'{names[c]}').to_string())""")

md("""**Step 3：结果解读**：日收益率的波动聚集（volatility clustering）特征明显：2021 年初、2022 年 3–4 月、2024 年 9–10 月及 2025 年多个时点出现成簇的大幅波动。比亚迪、隆基绿能、科大讯飞、恒瑞医药的极端日数量明显多于长江电力、格力电器，与描述统计的波动排序一致。所有观测均未突破 ±10% 涨跌停界限之外（最大单日涨跌幅约 ±10%），无数据错误。中信证券与长江电力面板中的空白缺口即停牌期间（收益记缺失，未填零）。""")

md("""### 5.4 20 日滚动年化波动率

**Step 1：分析说明**：以 20 个交易日为窗口（不足完整窗口不计算），滚动标准差 × √252 年化，单轴对比时序变化。""")

code("""roll_vol = R.rolling(20, min_periods=20).std() * np.sqrt(252)

fig, ax = plt.subplots(figsize=(12, 6))
for c in codes:
    ax.plot(roll_vol.index, roll_vol[c] * 100, lw=1.0, label=names[c])
ax.set_title('图4  20 日滚动年化波动率（%，20 个交易日窗口）', fontsize=13)
ax.set_ylabel('年化波动率(%)')
ax.legend(ncol=5, fontsize=9)
ax.grid(alpha=0.3)
fig.autofmt_xdate(rotation=30)
plt.tight_layout()
plt.savefig('figs/fig4-rolling-vol.png', dpi=150, bbox_inches='tight')
plt.show()

print('滚动波动率极值（%）:')
for c in ['600900', '002594', '601012', '002230']:
    s = roll_vol[c].dropna()
    print(f'  {names[c]}: {s.min()*100:.1f} ~ {s.max()*100:.1f}')""")

md("""**Step 3：结果解读**：滚动波动率呈现清晰的**同涨同落**：2021 年初（核心资产剧烈波动）、2022 年 3–4 月（疫情冲击）、2024 年 9–10 月（政策转向后暴涨暴跌）、2025 年阶段性高波动为全市场共性高峰。个股差异同样显著：隆基绿能峰值约 96%、比亚迪约 85%、科大讯飞约 95%，而长江电力即使在高峰期也仅约 36%，低谷期低至 6%——防御型资产的低波动属性贯穿全程。波动率的时变性与聚集性意味着"某段时期的风险"与全样本平均风险差异很大，20 日滚动窗口能捕捉这种阶段性。""")

md("""### 5.5 日收益率相关系数矩阵

**Step 1：分析说明**：计算 10 × 10 的 Pearson 相关系数矩阵（`pandas` 默认逐对完整观测：同一时点两股票均有收益才计入），以热力图展示。日期对齐采用并集日历；涉及中信/长电的股票对有效样本为 1384 − 7 = 1377 或 1384 − 13 = 1371，其余均为 1383（首日收益缺失后）。""")

code("""corr = R.corr()  # 逐对完整观测（pairwise complete）
fig, ax = plt.subplots(figsize=(9, 7.5))
im = ax.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1)
ax.set_xticks(range(len(codes))); ax.set_yticks(range(len(codes)))
ax.set_xticklabels([f'{names[c]}' for c in codes], rotation=45, ha='right', fontsize=9)
ax.set_yticklabels([f'{names[c]}' for c in codes], fontsize=9)
for i in range(len(codes)):
    for j in range(len(codes)):
        ax.text(j, i, f'{corr.values[i, j]:.2f}', ha='center', va='center',
                fontsize=7.5, color='white' if abs(corr.values[i, j]) > 0.55 else 'black')
ax.set_title('图5  日收益率 Pearson 相关系数矩阵（2021-01 ~ 2026-09）', fontsize=13)
plt.colorbar(im, ax=ax, shrink=0.8, label='相关系数')
plt.tight_layout()
plt.savefig('figs/fig5-corr-heatmap.png', dpi=150, bbox_inches='tight')
plt.show()

# 配对样本量说明
n_pairs = pd.DataFrame(index=codes, columns=codes, dtype=float)
for i in codes:
    for j in codes:
        n_pairs.loc[i, j] = R[[i, j]].dropna().shape[0]
print(f'相关系数所用有效样本量：非停牌股票对 {int(n_pairs.values.max())}，'
      f'涉及中信证券 {int(n_pairs.loc["600030"].max())}，涉及长江电力 {int(n_pairs.loc["600900"].max())}')
cs = corr.where(~np.eye(len(codes), dtype=bool)).stack().sort_values(ascending=False)
print('\\n相关系数最高与最低的 3 对股票:')
print(cs.head(3).round(3).to_string()); print(cs.tail(3).round(3).to_string())
print(f'\\n平均相关系数: {cs.mean():.3f}')""")

md("""**Step 3：结果解读**：

- **同行业更相关的猜想得到支持**：相关系数最高的一对是同属家用电器的**格力电器—美的集团（0.638）**，明显高于全场平均相关系数（0.273）。
- 其后依次为招商银行—贵州茅台（0.488）、比亚迪—隆基绿能（0.462）、招商银行—中信证券（0.459）、招商银行—美的集团（0.457）、贵州茅台—美的集团（0.454）：均为大盘蓝筹之间或新能源产业链内部的联动，共同受市场因子与资金流动驱动。
- 相关系数最低的股票对均涉及**长江电力**（与其余 9 只平均相关仅 0.118，与隆基绿能 −0.038、科大讯飞 −0.016 甚至略负）：防御型水电资产的现金流与宏观利率、来水相关，与周期成长股联动极弱，**分散价值最大**。
- 除长电与个别高波动成长股接近零或略负外，其余两两相关均为正（最高 0.638），符合 A 股市场因子主导的特征：纯多头组合无法完全消除系统性风险。个股年化波动的平均约 31.1%，而等权组合仅 18.49%，分散化显著但不会趋近于零。""")

# ============ 6 组合分析 ============
md("""## 6. 等权与市值加权组合

### Step 1：分析说明

**日频总市值的构造（校准法）**。作业要求市值加权使用上一交易日收盘时的**总市值** $MV_{i,t-1}$，且不得用复权价格乘股本、不得用当前市值回填。AKShare 现版本无日频历史总市值接口，百度股市通仅提供约 5 个交易日一档的网格市值（单位：亿元）。本文采用**股本校准法**：

1. 在每个网格日，用 `校准股本 = 网格总市值 ÷ 不复权收盘价` 反推总股本；
2. 将网格日股本**前向填充**至全部交易日（股本仅在送转/增发/回购注销等公司行为时跳变，两个网格日之间视为不变）；
3. `日频总市值 = 不复权收盘价 × 当日校准股本`。

该方法的误差仅在网格间隔内发生小规模股本变动（如小额定增）时出现，且会在下一个网格日被自动修正；大比例送转（股本跳变 >2%）均落在网格点上被直接捕获。校验：网格日重构市值与百度原始市值最大相对误差为 1.8×10⁻¹⁶（浮点精度级），完全一致。

**组合设定**（忽略交易成本的教学设定）：

$$r^{EW}_{p,t}=\\sum_{i=1}^{10}\\frac{1}{N_t}r_{i,t},\\qquad w_{i,t-1}=\\frac{MV_{i,t-1}}{\\sum_{j}MV_{j,t-1}},\\quad r^{VW}_{p,t}=\\sum_{i}w_{i,t-1}r_{i,t}$$

- 等权：$N_t$ 为当日有收益的股票数（停牌/复牌首日剔除，其余各 $1/N_t$）；
- 市值加权：权重用 $t-1$ 日总市值，$t$ 日无收益的股票权重剔除后**在其余股票内重新归一**（等价于"停牌期间资金按市值比例投于其余股票"的近似）；
- 每日核验权重和为 1；
- 评价指标：累计净值、几何年化收益 $R_{ann}=(\\prod(1+r_p))^{252/T}-1$、年化波动（组合日收益标准差 × √252，**不**加权平均个股波动）、最大回撤（净值相对历史峰值最大跌幅，报告为正数）；两组合评价期相同（2021-01-04 至 2026-09-16，$T$ 相同）。""")

code("""# ---- 构造日频市值 ----
mv_grid, mv_daily = {}, {}
share_events = []
for c in codes:
    raw = pd.read_csv(f'data/raw/tx_daily_{c}_raw.csv', parse_dates=['date']).set_index('date')
    mvg = pd.read_csv(f'data/raw/baidu_mv_{c}.csv', parse_dates=['date']).set_index('date')['value']  # 亿元
    j = mvg.to_frame('mv').join(raw['close'], how='inner')
    j = j[(j.index >= '2020-12-15') & (j.index <= '2026-09-16')]
    j['shares'] = j['mv'] / j['close']  # 亿股
    chg = j['shares'].pct_change()
    for d, v in chg[abs(chg) > 0.02].items():
        share_events.append({'股票': names[c], '日期': d.date(), '股本变动': f'{v:+.1%}',
                             '股本(亿股)': f"{j.loc[d, 'shares']:.1f}"})
    shares_d = j['shares'].reindex(raw.index).ffill().bfill()
    mv_daily[c] = raw['close'] * shares_d
    mv_grid[c] = j
MV = pd.DataFrame(mv_daily)

# 校验：网格日重构误差
errs = []
for c in codes:
    j = mv_grid[c]
    err = ((MV[c].reindex(j.index) - j['mv']).abs() / j['mv']).max()
    errs.append(err)
print(f'网格日市值重构最大相对误差: {max(errs):.2e}（浮点精度级，校准法与原始数据完全一致）✓')

print('\\n样本期内股本变动事件（相邻网格日变动 > 2%）:')
print(pd.DataFrame(share_events).to_string(index=False))

MV_sample = MV[(MV.index >= '2020-12-31') & (MV.index <= '2026-09-16')]
print('\\n样本期末（2026-09-16）总市值（亿元）:')
print(MV_sample.iloc[-1].rename(lambda c: f'{names[c]}').round(0).sort_values(ascending=False).to_string())""")

md("""**市值数据核验**：期末市值排序与市场常识一致（贵州茅台约 1.57 万亿元居首，招商银行约 1.03 万亿元次之，科大讯飞约 934 亿元最小），数量级正确。校准出的股本变动事件与公开公司行为吻合：如比亚迪 2025 年的大比例转增（股本从约 29 亿股升至约 87 亿股）、中信证券 2022 年配股（129.3 → 约 143 亿股）等，进一步验证口径正确。""")

code("""# ---- 组合权重与收益 ----
Rv = R.copy()

# 等权：当日有效股票各 1/N_t
W_ew = Rv.notna().astype(float)
W_ew = W_ew.div(W_ew.sum(axis=1), axis=0)
r_ew = (Rv * W_ew).sum(axis=1)

# 市值加权：t-1 总市值权重，t 日无效则剔除后归一
MVlag = MV.shift(1).reindex(Rv.index)
W_vw = MVlag.where(Rv.notna())
W_vw = W_vw.div(W_vw.sum(axis=1), axis=0)
r_vw = (Rv * W_vw).sum(axis=1)

# 权重核验
print('每日权重和核验: 等权 max|Σw−1| = %.2e，市值加权 max|Σw−1| = %.2e ✓' %
      ((W_ew.sum(axis=1) - 1).abs().max(), (W_vw.sum(axis=1) - 1).abs().max()))
print('两组合评价期一致:', r_ew.index.equals(r_vw.index), f'（T = {len(r_ew)}）')

# 市值加权权重集中度
top_w = W_vw.max(axis=1)
print(f'市值加权最大单票权重: 均值 {top_w.mean():.1%}，最大 {top_w.max():.1%}')
w_mean = W_vw.mean().rename(lambda c: f'{names[c]}').sort_values(ascending=False)
print('\\n市值加权平均权重:')
print((w_mean / w_mean.sum()).round(3).to_string())""")

md("""**权重核验**：两组合每日权重和与 1 的最大偏差均在 10⁻¹⁶ 量级（浮点精度）。市值加权的权重高度集中：贵州茅台平均权重 **33.6%**、招商银行 **16.1%**，前两大重仓股合计约 **50%**（最大单票权重一度达 40.5%），而科大讯飞（1.8%）、隆基绿能（3.9%）权重极低——市值加权天然"追大"，组合命运很大程度由超大盘股决定。""")

code("""# ---- 组合绩效 ----
def perf(r, label):
    nav = (1 + r).cumprod()
    T = len(r)
    ann = nav.iloc[-1] ** (252 / T) - 1
    vol = r.std() * np.sqrt(252)
    mdd = -(nav / nav.cummax() - 1).min()
    return pd.Series({'累计净值': nav.iloc[-1], '几何年化收益(%)': ann * 100,
                      '年化波动(%)': vol * 100, '最大回撤(%)': mdd * 100}, name=label)

NAV_ew = (1 + r_ew).cumprod(); NAV_vw = (1 + r_vw).cumprod()
perf_tbl = pd.concat([perf(r_ew, '等权组合'), perf(r_vw, '市值加权组合')], axis=1)

fig, axes = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={'width_ratios': [2, 1]})
ax = axes[0]
ax.plot(NAV_ew.index, NAV_ew, lw=1.4, color='#1f4e9c', label='等权组合')
ax.plot(NAV_vw.index, NAV_vw, lw=1.4, color='#c00000', label='市值加权组合')
ax.axhline(1.0, color='gray', ls='--', lw=0.8)
# 最大回撤发生区间标注
dd_ew = NAV_ew / NAV_ew.cummax() - 1; dd_vw = NAV_vw / NAV_vw.cummax() - 1
print('最大回撤区间（峰值 → 谷底）:')
for lbl, nav, dd in [('等权', NAV_ew, dd_ew), ('市值加权', NAV_vw, dd_vw)]:
    trough = dd.idxmin(); peak = nav.loc[:trough].idxmax()
    print(f'  {lbl}: 峰值 {peak.date()}（净值 {nav.loc[peak]:.3f}） → 谷底 {trough.date()}'
          f'（净值 {nav.loc[trough]:.3f}），回撤 {-dd.min()*100:.2f}%')
    print(f'      期末净值 {nav.iloc[-1]:.3f}，全期最高净值 {nav.max():.3f}（{nav.idxmax().date()}）')
ax.set_title('图6  等权与市值加权组合净值曲线（2020-12-31 = 1）', fontsize=13)
ax.set_ylabel('组合净值'); ax.legend(fontsize=10); ax.grid(alpha=0.3)
ax2 = axes[1]
ax2.fill_between(dd_ew.index, dd_ew * 100, 0, color='#1f4e9c', alpha=0.5, label='等权')
ax2.fill_between(dd_vw.index, dd_vw * 100, 0, color='#c00000', alpha=0.5, label='市值加权')
ax2.set_title('回撤（%）', fontsize=11); ax2.legend(fontsize=9); ax2.grid(alpha=0.3)
fig.autofmt_xdate(rotation=30)
plt.tight_layout()
plt.savefig('figs/fig6-portfolio.png', dpi=150, bbox_inches='tight')
plt.show()

perf_tbl.round(2)""")

md("""### Step 3：结果解读

| 指标 | 等权组合 | 市值加权组合 |
|---|---|---|
| 累计净值 | 1.06 | 0.93 |
| 几何年化收益 | **+1.01%** | **−1.31%** |
| 年化波动 | 18.49% | 19.14% |
| 最大回撤 | 32.57% | 39.94% |

- **等权全面占优**：年化收益高约 2.3 个百分点（+1.01% 对 −1.31%），波动更低（18.49% 对 19.14%），最大回撤更浅（32.57% 对 39.94%）。等权组合期末净值 1.06（全期最高 1.21，出现在 2025-08-25），市值加权期末净值 0.93，净亏约 7%。
- **差异来源**：市值加权把约 50% 的权重给了茅台 + 招行两只超大市值股票（33.6% + 16.1%），而茅台样本期年化 −5.44%、招行 +3.78%，权重集中放大了大市值股票的拖累；等权则给隆基、恒瑞等负收益股票与长电、比亚迪等正收益股票同等权重——本样本中后者恰好抵消了前者。此外，2021 年初建仓时点恰逢核心资产（大市值白马）估值顶部：两组合净值峰值均出现在 **2021-02-10**，随后市值加权承受了更深的回撤（−39.94%，谷底 2022-10-31，净值 0.719；等权 −32.57%，谷底同为 2022-10-31，净值 0.779）。市值加权组合的全期最高净值就停在 2021-02-10 的建仓初期高点，此后再未超越。
- **分散化效果**：两组合年化波动（18.49%、19.14%）均显著低于 10 只股票的平均年化波动（31.06%），印证相关系数为正但远小于 1 时分散投资仍能大幅降低波动。
- **局限**：这是**事后选定样本**的表现，不代表历史可实施策略或未来收益；忽略交易成本、停牌处理采用"剔除后归一"的近似、市值校准法假设网格间隔内股本不变，均会在边际上影响数值，但不改变"等权优于市值加权"的方向性结论（差异约 2.3 个百分点/年，远超方法误差量级）。""")

# ============ 7 总体结论 ============
md("""## 7. 总体结论

本作业以 10 只覆盖 8 个申万一级行业的 A 股龙头为样本，用 2021-01-04 至 2026-09-16（1384 个交易日）的冻结数据分析收益、风险与组合表现，主要结论如下：

1. **风险收益横截面差异大且普遍不匹配**。年化收益从长江电力的 +11.21% 到隆基绿能的 −22.81% 不等；波动率从 17.26%（长电）到 42.67%（科大讯飞）。样本期横跨 2021 年核心资产泡沫顶点与随后的长期调整，多数高波动成长股"承担了高风险却未获得收益补偿"，唯一的高收益低波动组合是防御型的长江电力。

2. **收益分布厚尾右偏，极端日集中于市场剧震期**。10 只股票偏度均为正（0.14–0.94）、超额峰度均为正（1.9–6.0），正态假设会低估极端风险；2021 年初、2022 年 3–4 月、2024 年 9–10 月是全市场共性的高波动时段，20 日滚动年化波动率显示清晰的波动聚集与同涨同落。

3. **同行业相关性更高的猜想成立**。美的—格力相关系数 0.638 为全场最高，显著超过平均相关系数 0.273；长江电力与其余股票平均相关仅 0.118（与隆基、科大讯飞甚至略负），分散价值最大。绝大多数两两相关为正说明市场因子主导，纯多头组合无法消除系统性风险，但分散化仍使组合波动（18.49%）远低于个股均值（31.06%）。

4. **等权组合显著优于市值加权组合**。等权：年化 +1.01%、波动 18.49%、最大回撤 32.57%；市值加权：−1.31%、19.14%、39.94%。根源在于市值加权约 50% 的权重集中于茅台与招行，而 2021 年初恰是大市值白马的估值顶部，权重集中放大了其后的回撤。两组合波动均远低于个股均值（31.06%），验证了分散投资的作用。

**关键处理判断**：**价格与收益一律使用复权价**，且统一采用同一条后复权序列；该序列经跨源核验后选用新浪财经数据——腾讯后复权序列存在复权因子漂移（非除权日与不复权收益的偏差最大 3.11%、涨停日 +10% 被压缩为 +8.45%、全期总回报最大低估 24.3 个百分点），已弃用（2.3 节）。不复权价仅用于识别除权事件与校准股本构造真实市值——若用不复权价算收益，除权日会出现虚假暴跌、累计收益平均低估 26.0 个百分点；停牌（中信 6+1 天、长电 11+2 天）与复牌首日收益记缺失而非填零或跨日计算，组合权重当日剔除后归一；日频总市值用"网格市值 ÷ 不复权价"校准股本构造（作业禁止用复权价乘股本），网格日重构误差在浮点精度级。

**数据与方法局限**：样本为事后选定的龙头组合，结论不代表可实施策略；行情来自腾讯（不复权）与新浪（后复权）两个来源，已用"非除权日两口径收益率恒等""涨跌停约束""独立复算总回报"三项检验交叉验证，并据此更换了失真的腾讯后复权序列（2.3 节），但东财源因限流未能纳入校验；忽略交易成本与停牌期间的真实可交易性；市值校准法在网格间隔内的小额股本变动存在最多 5 个交易日的滞后。""")

nb.cells = cells
nbf.write(nb, 'hw02-1.ipynb')
print(f'Notebook 已生成: hw02-1.ipynb（{len(cells)} 个单元格）')
