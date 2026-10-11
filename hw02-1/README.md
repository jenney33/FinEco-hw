# HW02-1：股票收益与组合风险分析

选取 10 只覆盖 8 个申万一级行业的 A 股（含美的/格力同行业对子），用 2021-01-01 至 2026-09-16 的日频数据分析收益、风险，并对比等权与市值加权组合。

## 数据来源与版本

| 数据 | 接口 | 参数 | 下载日期 | 文件 |
|---|---|---|---|---|
| 不复权日线、成交额 | AKShare `stock_zh_a_hist_tx`（腾讯） | `2020-12-30 ~ 2026-09-16`，`adjust=''` | 2026-09-18 | `data/raw/tx_daily_{代码}_raw.csv` |
| 后复权日线（**主口径**） | AKShare `stock_zh_a_hist_tx`（腾讯） | 同上，`adjust='hfq'` | 2026-09-18 | `data/raw/tx_daily_{代码}_hfq.csv` |
| 前复权日线（仅作复权基准校验） | 腾讯行情接口（与 AKShare 同源） | 同上，`qfq` | 2026-10-11 | `data/raw/tx_daily_{代码}_qfq.csv` |
| 分红除权事件（除权日、登记日、方案） | 腾讯行情 qfq 接口附带字段 | `nd / djr / cqr / FHcontent` | 2026-10-11 | `data/raw/tx_div_events.csv` |
| 历史总市值（约 5 日一档网格，亿元） | AKShare `stock_zh_valuation_baidu`（百度股市通） | `indicator='总市值'`，`period='近十年'` | 2026-09-18 | `data/raw/baidu_mv_{代码}.csv` |
| 申万一级行业归属 | AKShare `sw_index_first_info` + `index_component_sw` | 2026-09 最新成分 | 2026-09-18 | `data/stock-selection.csv`（已并入） |
| 上市日期/交易所 | AKShare `stock_info_sh_name_code` / `stock_info_sz_name_code` | 主板A股 / A股列表 | 2026-09-18 | `data/raw/sse_main_a_list.csv`、`data/raw/szse_a_list.csv` |

- 数据快照已入库（`data/`），复现**无需联网**；`data/fetch-manifest.json` 记录每个文件的 sha256 与获取参数。
- **价格与收益率统一使用复权价（后复权 hfq）**：后复权价以上市首日价为基准向后累乘，含分红再投资与送转调整，除权除息日序列连续。不复权价仅用于识别除权事件与构造真实总市值（作业禁止用复权价乘股本）。若误用不复权价，除权日会出现 −66.94% 级别的虚假暴跌（比亚迪 2025-07-29），10 只股票全期累计收益平均被低估 **22.0 个百分点**。
- **前复权序列不参与计算**：实测腾讯接口的 qfq 与 hfq 序列日收益率不一致（单日最大差 9.37 个百分点，长江电力全期累计差 44.9 个百分点），分红处理口径不同；qfq 仅用于核验复权基准（末日 qfq 价 = 实际成交价，差 0.00 元）与提取分红除权事件。
- 原计划使用东财接口（`stock_zh_a_hist`）作行情主源，下载时触发限流（错误已记录在 `code/fetch_data.py` 运行输出中），改用腾讯接口；行情字段满足作业全部要求。
- AKShare 现版本无日频历史总市值接口，采用"网格市值 ÷ 不复权价"校准股本构造日频市值（Notebook 第 6 节，网格日重构误差在浮点精度级）。

## 环境与运行

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name fineco   # 或使用默认 python3 内核
jupyter notebook hw02-1.ipynb                       # 从头运行（Kernel → Restart & Run All）
```

- Python 3.13；核心包：pandas 2.3.3、numpy 2.4.2、scipy 1.15.3、matplotlib 3.10.9、nbformat 5.10.4、nbclient 0.10.4；联网取数需 akshare 1.18.39（见 `requirements.txt`）。
- macOS 下中文图使用 Hiragino Sans GB；其他系统如缺字体请替换 `plt.rcParams['font.sans-serif']`。
- 全部使用相对路径（`data/`、`figs/`），请在 `hw02-1/` 目录内运行。

## 目录与运行顺序

```
hw02-1/
├── hw02-1.ipynb      # 主分析报告（从头运行，预期输出见下）
├── code/
│   ├── fetch_data.py      # 数据获取脚本（联网，已生成 data/ 快照）
│   ├── fetch_qfq.py       # 前复权日线与分红除权事件补下载（2026-10-11）
│   ├── build_notebook.py  # Notebook 构建脚本
│   └── run_notebook.py    # 无头执行脚本（nbclient）
├── data/             # 冻结数据快照 + 选股表 + fetch-manifest.json
└── figs/             # Notebook 生成的 7 张图（fig1 后复权价时序、fig1b 复权前后对比、
                      #   fig2 累计收益、fig3 日收益、fig4 滚动波动、fig5 相关矩阵、fig6 组合）
```

**预期主要输出**：样本期 2021-01-04 ~ 2026-09-16（1384 个交易日）；等权组合几何年化 +0.14%、年化波动 16.85%、最大回撤 30.7%；市值加权组合 −1.82%、17.35%、37.4%；美的—格力相关系数 0.63 为全场最高。
