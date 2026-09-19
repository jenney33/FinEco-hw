# HW02-2 数据准备：CSMAR 原始表 → 房地产上市公司年度面板
# 用法: python prepare_data.py
# 输入: data/raw/ 下的 CSMAR CSV（需 2004-2015 完整年份；缺失年份会在报告中标明）
# 输出: data/processed/panel.csv、data/processed/sample-pipeline.csv
import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path('data/raw')
OUT = Path('data/processed')
OUT.mkdir(parents=True, exist_ok=True)

# ---------- 字段映射（CSMAR → 分析变量） ----------
BS_COLS = {
    'Stkcd': 'code', 'ShortName': 'name', 'Accper': 'date', 'Typrep': 'typrep',
    'A001101000': 'cash',        # 货币资金
    'A002101000': 'st_loan',     # 短期借款
    'A002201000': 'lt_loan',     # 长期借款
    'A002100000': 'cur_liab',    # 流动负债合计
    'A002000000': 'total_liab',  # 负债合计
    'A001000000': 'total_asset', # 资产总计
    'A003000000': 'total_eq',    # 所有者权益合计（含少数股东权益）
}
IS_COLS = {
    'Stkcd': 'code', 'Accper': 'date', 'Typrep': 'typrep',
    'B002000000': 'net_profit',  # 净利润（合并口径，含少数股东损益）
}

def read_csmar(pattern, usecols=None):
    """读取 data/raw 下所有匹配文件并纵向合并（支持分年度文件）"""
    files = sorted(RAW.glob(pattern))
    assert files, f'未找到 {pattern}'
    frames = []
    for f in files:
        df = pd.read_csv(f, encoding='utf-8-sig', usecols=usecols, low_memory=False)
        df['__src'] = f.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

def norm_code(ser):
    """公司代码统一为 6 位字符串（补零），兼容整数/字符串输入"""
    return ser.astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(6)

report = []  # 样本处理表

def count_rows(pattern):
    return sum(pd.read_csv(f, encoding='utf-8-sig', usecols=[0]).shape[0]
               for f in sorted(RAW.glob(pattern)))

# ---------- 1. 资产负债表：年度合并报表 ----------
report.append(('原始资产负债表记录（全部类型、全部报告期）', int(count_rows('FS_Combas*.csv'))))
bs = read_csmar('FS_Combas*.csv', list(BS_COLS)).rename(columns=BS_COLS)
bs['code'] = norm_code(bs['code'])
bs['date'] = pd.to_datetime(bs['date'])
bs = bs[(bs['typrep'] == 'A') & (bs['date'].dt.strftime('%m-%d') == '12-31')]
report.append(('筛选：合并报表(Typrep=A) 且 年末(12-31)', len(bs)))
dup = bs.duplicated(['code', 'date']).sum()
report.append(('主键 (公司,年末) 重复记录', int(dup)))
if dup:
    bs = bs.sort_values('__src').drop_duplicates(['code', 'date'], keep='first')
bs['year'] = bs['date'].dt.year

# ---------- 2. 利润表 ----------
ins = read_csmar('FS_Comins*.csv', list(IS_COLS)).rename(columns=IS_COLS)
ins['code'] = norm_code(ins['code'])
ins['date'] = pd.to_datetime(ins['date'])
ins = ins[(ins['typrep'] == 'A') & (ins['date'].dt.strftime('%m-%d') == '12-31')]
ins['year'] = ins['date'].dt.year
ins = ins.drop_duplicates(['code', 'date'], keep='first')
report.append(('筛选：利润表 合并报表 年末记录', len(ins)))

# ---------- 3. 行业（各年年末口径）与上市状态 ----------
anl = read_csmar('STK_LISTEDCOINFOANL*.csv').rename(columns={'Symbol': 'code', 'EndDate': 'date'})
anl['code'] = norm_code(anl['code'])
anl['date'] = pd.to_datetime(anl['date'])
anl['year'] = anl['date'].dt.year
anl = anl.drop_duplicates(['code', 'year'], keep='first')
# 行业分类映射：2012 年起为证监会 2012 版（K70=房地产业），此前为 2001 版（J 门类房地产=J01）
anl['is_re'] = np.where(anl['year'] >= 2012,
                        anl['IndustryCode'].str.startswith('K70', na=False),
                        anl['IndustryCode'].str.startswith('J01', na=False))
re_codes = anl[anl['is_re']][['code', 'year', 'IndustryCode', 'IndustryName']].copy()
report.append(('年度信息表中 房地产 公司-年度记录（按各年年末行业与上市状态）', len(re_codes)))
# 说明：上市状态以年度信息表各年年末记录为准（该表保留已退市公司的历史年度记录），
# 未用 CG_Co 交叉过滤——本地下载的 CG_Co 为"退市时间"筛选子集（3194 行，非全量公司表）

# ---------- 4. 产权（按当年实际控制人/股权性质） ----------
en = read_csmar('EN_EquityNatureAll*.csv').rename(columns={'Symbol': 'code', 'EndDate': 'date'})
en['code'] = norm_code(en['code'])
en['date'] = pd.to_datetime(en['date'])
en = en[en['date'].dt.strftime('%m-%d') == '12-31']
en['year'] = en['date'].dt.year
en = en.drop_duplicates(['code', 'year'], keep='last')
en['ownership'] = en['EquityNature'].map({'国企': '国有', '民营': '民营'}).fillna(
    en['EquityNature'].map(lambda x: '其他' if pd.notna(x) else '不明'))

# ---------- 5. 合并面板 ----------
panel = (re_codes[['code', 'year']]
         .merge(bs.drop(columns=['name', 'typrep', '__src']), on=['code', 'year'], how='left')
         .merge(ins[['code', 'year', 'net_profit']], on=['code', 'year'], how='left')
         .merge(en[['code', 'year', 'ownership', 'EquityNature', 'ActualControllerName']],
                on=['code', 'year'], how='left'))
panel['ownership'] = panel['ownership'].fillna('不明')
report.append(('合并财报后 公司-年度观测（面板全集）', len(panel)))
report.append(('其中缺失当年资产负债表的观测', int(panel['total_asset'].isna().sum())))

# ---------- 6. 指标构造 ----------
# 平均资产/平均权益的基期取自完整资产负债表（不受行业分类变动影响）
prev = bs[['code', 'year', 'total_asset', 'total_eq']].copy()
prev['year'] += 1
prev = prev.rename(columns={'total_asset': 'asset_prev', 'total_eq': 'eq_prev'})
panel = panel.merge(prev, on=['code', 'year'], how='left')
panel['avg_asset'] = (panel['total_asset'] + panel['asset_prev']) / 2
panel['avg_eq'] = (panel['total_eq'] + panel['eq_prev']) / 2

def ratio(num, den, guard=None):
    r = num / den
    if guard is not None:
        r = r.where(guard)
    return r

# 资产负债率
panel['lev'] = ratio(panel['total_liab'], panel['total_asset'], panel['total_asset'] > 0)
# bankloan：短期与长期借款均非缺失时才计算（缺失不按零处理）
loan_ok = panel['st_loan'].notna() & panel['lt_loan'].notna()
panel['bankloan'] = np.where(loan_ok & (panel['total_liab'] > 0),
                             (panel['st_loan'] + panel['lt_loan']) / panel['total_liab'], np.nan)
# 短期负债占比
panel['st_liab_ratio'] = ratio(panel['cur_liab'], panel['total_liab'], panel['total_liab'] > 0)
# ROA / ROE（合并净利润口径；负权益/零分母 → 缺失）
panel['roa'] = ratio(panel['net_profit'], panel['avg_asset'], panel['avg_asset'] > 0)
panel['roe'] = ratio(panel['net_profit'], panel['avg_eq'], panel['avg_eq'] > 0)
# Cash_TA
panel['cash_ta'] = ratio(panel['cash'], panel['total_asset'], panel['total_asset'] > 0)

# ---------- 7. 样本截取与质量报告 ----------
avail_years = sorted(panel['year'].unique())
sample = panel[(panel['year'] >= 2005) & (panel['year'] <= 2015)].copy()
need = set(range(2004, 2016))
missing_years = need - set(avail_years)
report.append(('样本截取 2005-2015 后 公司-年度观测', len(sample)))

sample.to_csv(OUT / 'panel.csv', index=False, encoding='utf-8-sig')
panel[panel['year'].isin([2004])].to_csv(OUT / 'panel-2004-base.csv', index=False, encoding='utf-8-sig')

rep_df = pd.DataFrame(report, columns=['处理阶段', '数量'])
rep_df.to_csv(OUT / 'sample-pipeline.csv', index=False, encoding='utf-8-sig')
print(rep_df.to_string(index=False))
print(f'\n面板年份覆盖: {avail_years}')
if missing_years:
    print(f'⚠ 缺失年份（需从 CSMAR 补下载）: {sorted(missing_years)}')
print(f'\n房地产样本年度公司数（现有数据）:')
print(sample.groupby('year')['code'].nunique().to_string())
print('\n产权分布（现有数据）:')
print(sample.groupby(['year', 'ownership'])['code'].nunique().unstack(fill_value=0).to_string())
print(f'\n已输出: {OUT}/panel.csv（{len(sample)} 行）、sample-pipeline.csv')
