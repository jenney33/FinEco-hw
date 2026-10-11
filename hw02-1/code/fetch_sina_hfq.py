"""补充下载：新浪财经后复权（hfq）日线，替换腾讯 hfq。

背景：腾讯接口（AKShare stock_zh_a_hist_tx）的后复权序列存在复权因子漂移——
在无除权日的区间内 hfq/raw 比值仍在变化（中信证券 2024-09-20~10-08 从 5.6390
漂到 5.2842），导致涨停日的 +10.00% 被压缩成 +8.45% 左右，全期总回报也被系统性
低估（长江电力低估约 24 个百分点）。

新浪源（AKShare stock_zh_a_daily）的复权因子在同一区间变异仅 0.002%，涨停日正确
显示 +10.00%，且与"不复权价 + 分红送转方案"独立复算的全期总回报吻合（长电 +81.5%
vs 复算 +81.8%），因此改用新浪后复权序列计算收益率。

不复权价仍沿用腾讯序列（用于构造真实总市值、识别除权除息事件），两者交易日历
在下载后做对齐检查。
"""

import hashlib
import json
import time
from pathlib import Path

import akshare as ak
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
MANIFEST = BASE / "data" / "fetch-manifest.json"

START, END = "20201201", "20260916"

STOCKS = [
    ("600036", "招商银行"), ("600519", "贵州茅台"), ("000333", "美的集团"),
    ("000651", "格力电器"), ("002594", "比亚迪"), ("600030", "中信证券"),
    ("600276", "恒瑞医药"), ("601012", "隆基绿能"), ("600900", "长江电力"),
    ("002230", "科大讯飞"),
]


def sym_of(code):
    return ("sh" if code.startswith("6") else "sz") + code


def fetch_sina_hfq(code):
    df = ak.stock_zh_a_daily(symbol=sym_of(code), start_date=START, end_date=END, adjust="hfq")
    out = df[["date", "close"]].copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out = out.rename(columns={"close": "close"})
    return out.sort_values("date").reset_index(drop=True)


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"files": []}
    print("=" * 60)
    print("补充下载：新浪财经后复权（hfq）日线")
    print("=" * 60)

    for code, name in STOCKS:
        fname = f"sina_daily_{code}_hfq.csv"
        fpath = RAW / fname
        if fpath.exists():
            print(f"  跳过已有 {fname}")
            continue
        df = fetch_sina_hfq(code)
        df.to_csv(fpath, index=False, encoding="utf-8-sig")
        sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
        manifest["files"].append({
            "file": f"data/raw/{fname}",
            "rows": len(df),
            "range": f"{df['date'].min()} ~ {df['date'].max()}",
            "source": "AKShare stock_zh_a_daily（新浪）, adjust='hfq'",
            "sha256": sha,
        })
        print(f"  已保存 {fname}: {len(df)} 行，{df['date'].min()} ~ {df['date'].max()}")
        time.sleep(0.5)

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成。manifest 已更新（文件数 {len(manifest['files'])}）")

    # 交易日历对齐检查
    print("\n交易日历对齐检查（新浪 hfq vs 腾讯 raw）：")
    for code, name in STOCKS:
        s = pd.read_csv(RAW / f"sina_daily_{code}_hfq.csv", parse_dates=["date"]).set_index("date")
        t = pd.read_csv(RAW / f"tx_daily_{code}_raw.csv", parse_dates=["date"]).set_index("date")
        only_s = len(set(s.index) - set(t.index))
        only_t = len(set(t.index) - set(s.index))
        flag = "一致" if only_s == 0 and only_t == 0 else f"差异 sina独有{only_s} tx独有{only_t}"
        print(f"  {name:<6} 新浪{len(s):5d} 行  腾讯{len(t):5d} 行  {flag}")


if __name__ == "__main__":
    main()
