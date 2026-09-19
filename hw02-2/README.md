# HW02-2：房地产上市公司财务特征分析

构建 2005—2015 年房地产 A 股上市公司的企业—年度非平衡面板（各年年末行业/上市状态/产权口径），分析公司数量与产权结构演变，以及六个财务指标的时序与国有—民营差异。

## 当前状态

**数据管线已就绪并经 2014–2015 年数据验证；等待 2004—2013 年 CSMAR 数据补齐后重跑。**

1. 按 [`data/README.md`](data/README.md) 的清单从 CSMAR 下载 4 张表的 2004—2013 年段，放入 `data/raw/`；
2. 依次运行：
   ```bash
   python code/prepare_data.py    # CSMAR 原始表 → 面板（自动合并多年份文件）
   python code/build_notebook.py  # 生成 hw02-2.ipynb
   python code/run_notebook.py    # 从头执行
   ```

## 目录

```
hw02-2/
├── hw02-2.ipynb        # 主分析报告（数据补齐后生成）
├── code/
│   ├── prepare_data.py    # 数据清洗合并管线（已验证）
│   ├── build_notebook.py  # Notebook 构建
│   └── run_notebook.py    # 无头执行
├── data/
│   ├── README.md          # 下载清单、字段对应表、权限说明
│   ├── raw/               # CSMAR CSV（受限数据，不入库）
│   └── processed/         # 面板与样本处理表（受限数据，不入库）
└── figs/                  # Notebook 生成的图
```

## 口径要点

- 样本：年度信息表**各年年末**行业（≤2011 年 2001 版 `J01` 前缀；≥2012 年 2012 版 `K70`）与上市状态，允许退市/行业/产权跨年变化；
- 产权：当年股权性质（国企→国有、民营→民营、外资/其他→其他、缺失→不明）；
- 指标：lev、bankloan（两借款字段齐全才计算）、st_liab_ratio、ROA/ROE（平均资产/权益，需 2004 年末基期）、cash_ta；负权益 ROE 记缺失；极端值保留不缩尾。

## 数据权限

CSMAR 为受限数据，`data/` 不入公开仓库；教师核验请按 `data/README.md` 的下载条件与字段清单获取。
