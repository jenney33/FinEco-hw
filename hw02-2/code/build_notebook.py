# 构建 hw02-2.ipynb（数据 2004-2013 补齐并运行 prepare_data.py 后执行本脚本）
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata['kernelspec'] = {'display_name': 'Python 3 (fineco)', 'language': 'python', 'name': 'fineco'}
nb.metadata['language_info'] = {'name': 'python', 'version': '3.13.12'}

cells = []
def md(src): cells.append(nbf.v4.new_markdown_cell(src))
def code(src): cells.append(nbf.v4.new_code_cell(src))

md("""# HW02-2：房地产上市公司财务特征分析

- 姓名：黄翌珊
- 学号：24360023
- 作业简介或教师作业页面链接：[HW02 作业页面](https://lianxhcn.github.io/FinEco/exercises/hw-02.html)
- 个人 GitHub 仓库访问地址：（待填写）
- HW02-1 目录链接：（待填写）
- HW02-2 目录链接：（待填写）
- 数据来源、获取日期与样本期间：CSMAR（中山大学授权）。样本为 **2005—2015 年房地产 A 股上市公司**年度合并报表，另取 2004 年末资产负债表计算平均资产/权益。资产负债表/利润表/股权性质文件/基本信息年度表分两段下载：2004—2013 段（2026-09-XX 下载）、2014—2025 段（2026-09-16 下载）。
- AI 使用声明：使用了 WorkBuddy（AI 助手）辅助编写数据清洗管线与 Notebook 代码初稿；本人核验了字段口径、行业映射与图表结果。

**分析目的与总体思路**：构建 2005—2015 年房地产 A 股上市公司的企业—年度非平衡面板（按各年年末上市状态、行业与产权属性），回答三个问题：(1) 样本期内房地产公司数量与国有/民营产权结构如何演变；(2) 资产负债率、银行借款占比、短期负债占比、ROA、ROE、现金持有六个财务指标的时间趋势如何；(3) 国有与民营企业的财务特征有何差异。描述性差异不解释为产权的因果作用。""")

md("""## 1. 数据来源、样本构建与样本处理表

### Step 1：分析说明

- **数据表**：资产负债表（合并报表，年末）、利润表（合并报表，年末）、中国上市公司股权性质文件（年末）、上市公司基本信息年度表（年末），均来自 CSMAR；
- **样本构建**：以年度信息表**各年年末**的行业代码与上市状态为准确定样本——2011 年及以前按证监会 2001 版行业（J 门类房地产 `J01` 前缀），2012 年起按证监会 2012 版（`K70` 房地产业）；**不使用当前行业或当前上市状态回溯历史**，允许上市、退市、行业与产权跨年变化，构成非平衡面板；
- **产权分类**：按**当年**股权性质文件的实际控制人/股权性质：国企→国有，民营→民营，外资与其他→其他，缺失→不明；非国有不直接等于民营；
- **主键**：（公司代码, 年度）；单位：财务报表原始字段为人民币元，比率为无量纲。""")

code("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'PingFang SC', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('data/processed/panel.csv', dtype={'code': str})
pipeline = pd.read_csv('data/processed/sample-pipeline.csv')

print('== 面板年份覆盖与完整性 ==')
years = sorted(df['year'].unique())
print('覆盖年份:', years)
need = set(range(2005, 2016))
missing = sorted(need - set(years))
print('缺失年份:', missing if missing else '无（2005-2015 完整）✓')
assert not missing, '请先按 data/README.md 补齐 CSMAR 数据并重跑 prepare_data.py'

print(f'\\n样本: 2005-2015 年，{df["code"].nunique()} 家公司，{len(df)} 个公司-年度观测')
print('主键 (公司,年度) 重复:', df.duplicated(['code', 'year']).sum(), '✓' if not df.duplicated(['code', 'year']).any() else '需回查')
print('\\n== 样本处理表（下载→筛选→合并→构造各阶段数量）==')
pipeline""")

md("""### Step 3：结果解读

样本处理表记录了从原始记录到最终面板每个阶段的公司-年度观测数：原始资产负债表记录约 XX 万条（全部报告期、含母公司报表）→ 合并报表年末记录 → 房地产年末公司记录 → 样本。主键无重复，2005—2015 年每年均有观测，面板完整。

（**说明**：本段与下文各节的数值解读在 2004—2013 年 CSMAR 数据补齐、管线重跑后更新。）""")

md("""## 2. 公司数量与产权结构

### Step 1：分析说明

按各年年末状态统计：房地产上市公司**总数**；国有、民营、其他、产权**不明**公司数量；国有与民营占当年总数的比例。公司数按年代码去重，不因财务指标缺失而剔除。存在其他/不明类别时，国有+民营占比之和可以小于 100%。""")

code("""cnt = df.groupby('year')['code'].nunique().rename('总数')
own = df.groupby(['year', 'ownership'])['code'].nunique().unstack(fill_value=0)
for col in ['国有', '民营', '其他', '不明']:
    if col not in own.columns: own[col] = 0
own = own[['国有', '民营', '其他', '不明']]
tbl = pd.concat([cnt, own], axis=1)
tbl['国有占比(%)'] = (tbl['国有'] / tbl['总数'] * 100).round(1)
tbl['民营占比(%)'] = (tbl['民营'] / tbl['总数'] * 100).round(1)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ax = axes[0]
bottom = np.zeros(len(tbl))
for col, c in zip(['国有', '民营', '其他', '不明'], ['#1f4e9c', '#c00000', '#888888', '#dddddd']):
    ax.bar(tbl.index, tbl[col], bottom=bottom, label=col, color=c)
    bottom += tbl[col].values
ax.set_title('图1a  房地产上市公司数量与产权构成（家）', fontsize=12)
ax.set_xlabel('年份'); ax.set_ylabel('公司数'); ax.legend(fontsize=9)
ax2 = axes[1]
ax2.plot(tbl.index, tbl['国有占比(%)'], 'o-', color='#1f4e9c', label='国有占比')
ax2.plot(tbl.index, tbl['民营占比(%)'], 's-', color='#c00000', label='民营占比')
ax2.set_title('图1b  国有与民营企业占比（%）', fontsize=12)
ax2.set_xlabel('年份'); ax2.set_ylabel('占比(%)'); ax2.legend(fontsize=9); ax2.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('figs/fig1-counts-ownership.png', dpi=150, bbox_inches='tight')
plt.show()
tbl""")

md("""### Step 3：结果解读

（数据补齐后更新：引用各年总数、国有/民营占比的具体数值与转折点年份。预期关注点：2005 年前后样本基数、2010—2013 年房地产调控与 IPO 节奏对公司数量的影响、国有与民营占比的此消彼长。）

核心发现模板：(1) 样本公司总数从 2005 年的 X 家增长到 2015 年的 Y 家；(2) 国有占比由 X% 降至/升至 Y%，反映……；(3) 其他/不明类别占比约 X%，故国有+民营占比之和小于 100%。""")

md("""## 3. 指标质量检查：零分母、负权益与极端比率

### Step 1：分析说明

处理规则（均保留记录、不缩尾，仅将影响比率的观测记为缺失并计数）：

- **零/负分母**：总资产 ≤ 0 → 资产负债率与 Cash_TA 记缺失；总负债 ≤ 0 → bankloan 与短期负债占比记缺失；
- **负权益**：平均所有者权益 ≤ 0（资不抵债）→ ROE 记缺失（此时 ROE 无经济意义：亏损除以负权益会得到"为正"的假象）；
- **bankloan 分母口径**：短期与长期借款两个字段均非缺失才计算（缺失不按零处理）；
- **极端比率**：资产负债率 > 1（资不抵债）、|ROE| > 1 等观测保留并逐一计数说明，可能来自真实财务困境（如 ST 公司），不删除。""")

code("""n_obs = len(df)
checks = pd.DataFrame({
    '有效观测数': df[['lev', 'bankloan', 'st_liab_ratio', 'roa', 'roe', 'cash_ta']].notna().sum(),
    '缺失数': df[['lev', 'bankloan', 'st_liab_ratio', 'roa', 'roe', 'cash_ta']].isna().sum(),
})
print(f'总观测: {n_obs}')
print(checks.to_string())
print('\\n极端观测（保留，不缩尾）:')
print(f'  资产负债率 > 1（资不抵债）: {(df["lev"] > 1).sum()} 条')
if (df['lev'] > 1).any():
    print(df.loc[df['lev'] > 1, ['code', 'year', 'lev', 'total_asset']].round(3).to_string(index=False))
print(f'  平均权益 ≤ 0 导致 ROE 缺失: {((df["avg_eq"] <= 0) & df["avg_eq"].notna()).sum()} 条')
print(f'  |ROE| > 1: {(df["roe"].abs() > 1).sum()} 条')
print(f'  bankloan 两字段缺失导致无法计算: {(df["st_loan"].isna() | df["lt_loan"].isna()).sum()} 条')""")

md("""### Step 3：结果解读

（数据补齐后更新：报告各指标的有效样本量差异及原因、资不抵债观测的数量与代表公司、负权益对 ROE 缺失的影响。要点：缺失不是数据错误而是口径处理的结果，且都已在样本量表中透明呈现。）""")

md("""## 4. 六个财务指标：时序与产权分组比较

### Step 1：分析说明

对六个指标分别呈现：

1. **全部房地产企业历年均值与中位数**（企业比率的算术平均，非行业汇总值之比）；
2. **国有与民营企业历年均值比较**；
3. **国有与民营企业历年中位数比较**；
4. **各指标年度有效样本量表**。

均值受极端值影响，中位数更稳健，两者并置可识别分布偏斜与离群值影响；国有—民营差异为描述性对比，不代表产权的因果效应。""")

code("""INDS = [('lev', '资产负债率'), ('bankloan', '银行借款/总负债'), ('st_liab_ratio', '短期负债占比'),
        ('roa', 'ROA'), ('roe', 'ROE'), ('cash_ta', '货币资金/总资产')]

# 4.1 全样本均值与中位数
fig, axes = plt.subplots(2, 3, figsize=(16, 8.5))
for ax, (col, label) in zip(axes.ravel(), INDS):
    g = df.groupby('year')[col]
    ax.plot(g.mean().index, g.mean().values, 'o-', lw=1.4, color='#1f4e9c', label='均值')
    ax.plot(g.median().index, g.median().values, 's--', lw=1.4, color='#c00000', label='中位数')
    ax.set_title(label, fontsize=11); ax.legend(fontsize=9); ax.grid(alpha=0.3); ax.tick_params(labelsize=9)
fig.suptitle('图2  全部房地产企业：各指标历年均值与中位数', fontsize=13)
plt.tight_layout()
plt.savefig('figs/fig2-all-mean-median.png', dpi=150, bbox_inches='tight')
plt.show()

# 4.2 国有 vs 民营：均值
sub = df[df['ownership'].isin(['国有', '民营'])]
fig, axes = plt.subplots(2, 3, figsize=(16, 8.5))
for ax, (col, label) in zip(axes.ravel(), INDS):
    g = sub.groupby(['year', 'ownership'])[col].mean().unstack()
    ax.plot(g.index, g['国有'], 'o-', lw=1.4, color='#1f4e9c', label='国有')
    ax.plot(g.index, g['民营'], 's-', lw=1.4, color='#c00000', label='民营')
    ax.set_title(label, fontsize=11); ax.legend(fontsize=9); ax.grid(alpha=0.3); ax.tick_params(labelsize=9)
fig.suptitle('图3  国有 vs 民营：各指标历年均值比较', fontsize=13)
plt.tight_layout()
plt.savefig('figs/fig3-own-mean.png', dpi=150, bbox_inches='tight')
plt.show()

# 4.3 国有 vs 民营：中位数
fig, axes = plt.subplots(2, 3, figsize=(16, 8.5))
for ax, (col, label) in zip(axes.ravel(), INDS):
    g = sub.groupby(['year', 'ownership'])[col].median().unstack()
    ax.plot(g.index, g['国有'], 'o-', lw=1.4, color='#1f4e9c', label='国有')
    ax.plot(g.index, g['民营'], 's-', lw=1.4, color='#c00000', label='民营')
    ax.set_title(label, fontsize=11); ax.legend(fontsize=9); ax.grid(alpha=0.3); ax.tick_params(labelsize=9)
fig.suptitle('图4  国有 vs 民营：各指标历年中位数比较', fontsize=13)
plt.tight_layout()
plt.savefig('figs/fig4-own-median.png', dpi=150, bbox_inches='tight')
plt.show()

# 4.4 年度有效样本量表
n_tbl = df.groupby('year')[['lev', 'bankloan', 'st_liab_ratio', 'roa', 'roe', 'cash_ta']].count()
n_tbl.columns = [label for _, label in INDS]
n_tbl""")

md("""### Step 3：结果解读

（数据补齐后更新。分析框架：）

- **数量与产权结构**：公司总数趋势与国有/民营占比变化（结合 IPO 暂停与重启、借壳上市节奏、国企改革背景）；
- **杠杆指标**：资产负债率的均值—中位数差距反映右偏分布与少数高杠杆公司的拉动；bankloan 与短期负债占比刻画融资结构（银行信贷依赖与期限结构）；
- **盈利指标**：ROA/ROE 在 2008—2009 年金融危机、2010—2013 年地产调控、2014—2015 年库存周期中的变化；ROE > ROA 的杠杆放大效应；
- **国有 vs 民营**：若国企杠杆更高而 ROE 更低，可能反映融资约束差异与软预算约束，但这只是描述性证据——样本选择（国企多为大型上市房企）、行业周期与政策环境都可能是混杂因素，**不能解释为产权的因果作用**；
- **突变检查**：任何指标的年度突变需区分是离群值、异常分母、样本进出还是产权变更所致（结合第 3 节的计数与样本量表）。

核心发现将总结为 3—4 条。""")

md("""## 5. 总体结论

（数据补齐后更新：串联公司数量与产权结构演变、六个指标的时序特征、国有—民营差异三方面发现，并概括关键处理判断——非平衡面板的年末口径、缺失不按零、负权益记缺失、极端值保留——以及数据与方法局限：CSMAR 年末口径与会计政策变更、产权分类依赖披露质量、描述性分析无法识别因果。）""")

nb.cells = cells
nbf.write(nb, 'hw02-2.ipynb')
print(f'Notebook 已生成: hw02-2.ipynb（{len(cells)} 个单元格）')
print('注意: 需先按 data/README.md 补齐 2004-2013 年 CSMAR 数据并运行 prepare_data.py')
