# -*- coding: utf-8 -*-
"""HW02-1 数据获取脚本：下载 10 只 A 股的行情、复权行情、历史市值与基础信息。

数据快照保存到 hw02-1/data/，Notebook 只读快照，不重复联网。脚本幂等：已存在的文件跳过。

数据来源：
- 腾讯财经历史行情（akshare stock_zh_a_hist_tx）：不复权收盘价（展示）+ 后复权收盘价（算收益率）【主源】
- 东方财富历史行情（akshare stock_zh_a_hist）：跨来源校验；本机网络多次限流时记录为不可用
- 百度股市通（akshare stock_zh_valuation_baidu）：历史总市值（亿元）
- 上交所/深交所官网：上市日期；申万宏源：一级行业成分验证

运行：
  /Users/shan/.workbuddy/binaries/python/envs/fineco/bin/python code/fetch_data.py
"""
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import akshare as ak
import pandas as pd

HERE = Path(__file__).resolve().parent.parent          # hw02-1/
DATA = HERE / "data"
RAW = DATA / "raw"
RAW.mkdir(parents=True, exist_ok=True)

START_TX = "2020-12-30"  # 样本开始前最后一个交易日附近（取宽，分析时按交易日对齐）
END_TX = "2026-09-16"    # 作业统一样本截止日
START_EM = START_TX.replace("-", "")
END_EM = END_TX.replace("-", "")

STOCKS = [
    ("600036", "招商银行", "银行",     "股份制银行龙头，盈利与分红稳定，代表金融行业"),
    ("600519", "贵州茅台", "食品饮料", "白酒消费龙头，高毛利商业模式的代表"),
    ("000333", "美的集团", "家用电器", "白电龙头，多元化制造企业"),
    ("000651", "格力电器", "家用电器", "白电第二龙头，与美的构成同行业对子，检验同行业相关性"),
    ("002594", "比亚迪",   "汽车",     "新能源汽车龙头，成长与波动较高"),
    ("600030", "中信证券", "非银金融", "券商龙头，业绩与市场行情高度联动"),
    ("600276", "恒瑞医药", "医药生物", "创新药龙头，受政策与研发周期影响大"),
    ("601012", "隆基绿能", "电力设备", "光伏龙头，代表新能源制造周期"),
    ("600900", "长江电力", "公用事业", "水电龙头，现金流稳定的防御型资产"),
    ("002230", "科大讯飞", "计算机",   "AI 软件龙头，代表高估值科技股"),
]

SW_CODES = {
    "银行": "801780", "食品饮料": "801120", "家用电器": "801110", "汽车": "801880",
    "非银金融": "801790", "医药生物": "801150", "电力设备": "801730",
    "公用事业": "801160", "计算机": "801750",
}

manifest = {
    "retrieved_at": datetime.now().isoformat(timespec="seconds"),
    "akshare_version": ak.__version__,
    "sample_window": ["2021-01-01", "2026-09-16"],
    "extra_start": "2020-12-30（样本开始前最后一个交易日附近，用于计算首个交易日收益率）",
    "primary_price_source": "腾讯财经（stock_zh_a_hist_tx）",
    "cross_check_source": "东方财富（stock_zh_a_hist，如遇限流则记录不可用）",
    "market_cap_source": "百度股市通（stock_zh_valuation_baidu，单位：亿元）",
    "files": [],
    "errors": [],
}


def retry(fn, desc, times=4, sleep=5):
    last = None
    for i in range(times):
        try:
            return fn()
        except Exception as e:
            last = e
            print(f"  [重试 {i+1}/{times}] {desc}: {type(e).__name__}: {str(e)[:100]}")
            time.sleep(sleep)
    manifest["errors"].append(f"{desc}: {type(last).__name__}")
    return None


def save(df, name):
    p = RAW / name
    df.to_csv(p, index=False, encoding="utf-8-sig")
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    manifest["files"].append({"file": f"data/raw/{name}", "rows": len(df), "sha256": sha})
    print(f"  已保存 {name}: {len(df)} 行")


def exists(name):
    return (RAW / name).exists()


# ============ 1. 上市日期与行业验证 ============
print("=" * 60)
print("1. 交易所上市日期 与 申万行业成分验证")
print("=" * 60)
if not exists("sse_main_a_list.csv"):
    sh_info = retry(lambda: ak.stock_info_sh_name_code(symbol="主板A股"), "上交所主板A股列表")
    if sh_info is not None:
        save(sh_info, "sse_main_a_list.csv")
if not exists("szse_a_list.csv"):
    sz_info = retry(lambda: ak.stock_info_sz_name_code(symbol="A股列表"), "深交所A股列表")
    if sz_info is not None:
        save(sz_info, "szse_a_list.csv")

listing = {}
sh_info = pd.read_csv(RAW / "sse_main_a_list.csv", dtype=str) if exists("sse_main_a_list.csv") else None
sz_info = pd.read_csv(RAW / "szse_a_list.csv", dtype=str) if exists("szse_a_list.csv") else None
if sh_info is not None:
    for _, r in sh_info.iterrows():
        listing[str(r["证券代码"]).zfill(6)] = str(r["上市日期"])
if sz_info is not None:
    for _, r in sz_info.iterrows():
        listing[str(r["A股代码"]).zfill(6)] = str(r["A股上市日期"])

sw_verify = {}
for ind, code in SW_CODES.items():
    cons = retry(lambda c=code: ak.index_component_sw(symbol=c), f"申万成分 {ind}", times=3)
    if cons is not None:
        for _, r in cons.iterrows():
            sw_verify[str(r["证券代码"]).split(".")[0].zfill(6)] = ind
        time.sleep(1)

rows = []
for code, name, ind, reason in STOCKS:
    sw_ind = sw_verify.get(code, "未验证到")
    rows.append({
        "代码": code, "简称": name, "申万一级行业": ind,
        "行业验证": "一致" if sw_ind == ind else f"成分表为:{sw_ind}",
        "上市日期": listing.get(code, "未获取"),
        "交易所": "上交所" if code.startswith("6") else "深交所",
        "选股理由": reason,
    })
sel = pd.DataFrame(rows)
sel.to_csv(DATA / "stock-selection.csv", index=False, encoding="utf-8-sig")
print(sel.to_string(index=False))

# ============ 2. 主源：腾讯历史行情（不复权 + 后复权） ============
print("=" * 60)
print("2. 腾讯财经历史行情（主源：不复权 / 后复权）")
print("=" * 60)
for code, name, *_ in STOCKS:
    sym = ("sh" if code.startswith("6") else "sz") + code
    for adjust, tag in [("", "raw"), ("hfq", "hfq")]:
        fname = f"tx_daily_{code}_{tag}.csv"
        if exists(fname):
            print(f"  跳过已有 {fname}")
            continue
        df = retry(lambda s=sym, a=adjust: ak.stock_zh_a_hist_tx(
            symbol=s, start_date=START_TX, end_date=END_TX, adjust=a), f"腾讯 {code} {tag}")
        if df is not None:
            save(df, fname)
        time.sleep(1.5)

# ============ 3. 跨源校验：东方财富（可限流，失败则记录） ============
print("=" * 60)
print("3. 东方财富历史行情（跨源校验，单次尝试）")
print("=" * 60)
for code, name, *_ in STOCKS:
    for adjust, tag in [("", "raw"), ("hfq", "hfq")]:
        fname = f"em_daily_{code}_{tag}.csv"
        if exists(fname):
            print(f"  跳过已有 {fname}")
            continue
        try:
            df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                    start_date=START_EM, end_date=END_EM, adjust=adjust)
            save(df, fname)
        except Exception as e:
            manifest["errors"].append(f"东财 {code} {tag}: {type(e).__name__}（限流，未获取）")
            print(f"  东财 {code} {tag} 不可用: {type(e).__name__}")
        time.sleep(8)   # 东财接口限流敏感，拉长间隔

# ============ 4. 历史总市值：百度股市通 ============
print("=" * 60)
print("4. 历史总市值（百度股市通，单位：亿元）")
print("=" * 60)
for code, name, *_ in STOCKS:
    fname = f"baidu_mv_{code}.csv"
    if exists(fname):
        print(f"  跳过已有 {fname}")
        continue
    df = retry(lambda c=code: ak.stock_zh_valuation_baidu(symbol=c, indicator="总市值", period="近十年"),
               f"百度总市值 {code}")
    if df is not None:
        save(df, fname)
    time.sleep(1.5)

(DATA / "fetch-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print("=" * 60)
print(f"完成。文件数: {len(manifest['files'])}; 错误数: {len(manifest['errors'])}")
print("manifest 已保存 data/fetch-manifest.json")
