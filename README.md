# FinEco-hw

连玉君老师《金融计量经济学（FinEco）》课程作业仓库。

- [HW02-1：股票收益与组合风险分析](hw02-1/) — 10 只 A 股（8 个申万一级行业）2021-01~2026-09 的收益风险分析与等权/市值加权组合对比。**已完成**（数据快照入库，可离线复现）。
- [HW02-2：房地产上市公司财务特征分析](hw02-2/) — 2005–2015 年房地产 A 股非平衡面板与财务特征。**管线已就绪，等待 2004–2013 年 CSMAR 数据补齐**（下载清单见 `hw02-2/data/README.md`）。

## 目录结构

```
FinEco-hw/
├── README.md
├── .gitignore
├── hw02-1/
│   ├── hw02-1.ipynb       # 主分析报告（已运行）
│   ├── README.md
│   ├── requirements.txt
│   ├── code/              # 取数、构建、执行脚本
│   ├── data/              # 冻结数据快照（AKShare 公开数据，可入库）
│   └── figs/
└── hw02-2/
    ├── hw02-2.ipynb       # 待数据补齐后生成
    ├── README.md
    ├── requirements.txt
    ├── code/
    └── data/              # CSMAR 受限数据，不入库（见 data/README.md）
```

## 复现方式

每题目录内均有独立 README 与 requirements.txt；核心分析在 Notebook 中呈现，辅助脚本在 `code/`。HW02-1 数据快照已入库，按 README 新建虚拟环境后从头运行 Notebook 即可复现；HW02-2 需先按下载清单获取 CSMAR 数据（受限，未入库）。
