# -*- coding: utf-8 -*-
"""HW02-1 补充下载：腾讯财经前复权（qfq）日线。

用途：作业要求"跨来源检查代码、日期和复权口径"。现已有不复权（raw）与后复权（hfq）日线，
本脚本补齐前复权（qfq）日线，用于在 Notebook 中做三口径交叉核验：
前复权与后复权算出的日收益率应完全一致（均为含分红再投资的总回报口径），
不复权则在除权除息日出现向下假跳变，会低估真实收益。

数据快照保存到 hw02-1/data/raw/tx_daily_{代码}_qfq.csv，列与既有文件一致：
date,open,close,high,low,amount。脚本幂等：已存在的文件跳过。

运行：
  /Users/shan/.workbuddy/binaries/python/envs/fineco/bin/python code/fetch_qfq.py

说明：akshare 1.18.39 的 stock_zh_a_hist_tx 在本机抛 ValueError（init_start_date 解析异常），
故直接调用腾讯行情接口（与 akshare 同源同一 endpoint），字段与单位保持一致。
"""
import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent.parent          # hw02-1/
RAW = HERE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

START = "2020-12-30"
END = "2026-09-16"
URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

STOCKS = [
    ("600036", "招商银行"), ("600519", "贵州茅台"), ("000333", "美的集团"),
    ("000651", "格力电器"), ("002594", "比亚迪"),   ("600030", "中信证券"),
    ("600276", "恒瑞医药"), ("601012", "隆基绿能"), ("600900", "长江电力"),
    ("002230", "科大讯飞"),
]


def sym_of(code):
    return ("sh" if code.startswith("6") else "sz") + code


def fetch_window(sym, start, end):
    p = {"param": f"{sym},day,{start},{end},640,qfq"}
    r = requests.get(URL, params=p, timeout=30)
    r.raise_for_status()
    d = json.loads(r.text)["data"][sym]
    rows = d.get("qfqday") or d.get("day") or []
    # 前 6 列为 date/open/close/high/low/amount；第 7 列（若存在）为分红除权事件字典
    return [(x[:6], (x[6] if len(x) > 6 else None)) for x in rows]


def fetch_qfq(code):
    """腾讯接口单次最多返回 640 行，按时间从后往前翻页取全区间。

    同时收集接口返回的分红除权事件（FHcontent / djr 股权登记日 / cqr 除权日），
    用于在 Notebook 中核验：这些日期上不复权价向下跳变、复权价保持连续。
    """
    sym = sym_of(code)
    end = END
    frames, events = [], []
    while True:
        rows = fetch_window(sym, START, end)
        if not rows:
            break
        df = pd.DataFrame([r[0] for r in rows],
                          columns=["date", "open", "close", "high", "low", "amount"])
        frames.append(df)
        for r, ev in rows:
            if isinstance(ev, dict):
                events.append({"代码": code, "除权日": r[0], "年度": ev.get("nd"),
                               "股权登记日": ev.get("djr"), "除权除息日": ev.get("cqr"),
                               "方案": ev.get("FHcontent")})
        earliest = df["date"].min()
        if earliest <= START:
            break
        end = (datetime.strptime(earliest, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        if end < START:
            break
        time.sleep(1.0)
    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates("date").sort_values("date").reset_index(drop=True)
    for c in ["open", "close", "high", "low", "amount"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    ev = pd.DataFrame(events).drop_duplicates(["代码", "除权日"]) if events else pd.DataFrame(
        columns=["代码", "除权日", "年度", "股权登记日", "除权除息日", "方案"])
    return out, ev


manifest_path = HERE / "data" / "fetch-manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"files": [], "errors": []}
manifest.setdefault("files", [])
manifest.setdefault("errors", [])
manifest["qfq_appended_at"] = datetime.now().isoformat(timespec="seconds")

print("=" * 60)
print("补充下载：腾讯财经前复权（qfq）日线 + 分红除权事件")
print("=" * 60)
all_events = []
for code, name in STOCKS:
    fname = f"tx_daily_{code}_qfq.csv"
    fpath = RAW / fname
    if fpath.exists():
        print(f"  跳过已有 {fname}")
        continue
    df, ev = fetch_qfq(code)
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
    manifest["files"].append({"file": f"data/raw/{fname}", "rows": len(df), "sha256": sha})
    all_events.append(ev)
    print(f"  已保存 {fname}: {len(df)} 行，{df['date'].min()} ~ {df['date'].max()}，"
          f"分红除权事件 {len(ev)} 条")
    time.sleep(1.0)

if all_events:
    ev_all = pd.concat(all_events, ignore_index=True)
    ev_all = ev_all.sort_values(["代码", "除权日"]).reset_index(drop=True)
    ev_path = RAW / "tx_div_events.csv"
    ev_all.to_csv(ev_path, index=False, encoding="utf-8-sig")
    sha = hashlib.sha256(ev_path.read_bytes()).hexdigest()
    manifest["files"].append({"file": "data/raw/tx_div_events.csv", "rows": len(ev_all), "sha256": sha})
    print(f"  已保存 tx_div_events.csv: {len(ev_all)} 条分红除权事件")

manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"完成。manifest 已更新（文件数 {len(manifest['files'])}）")
