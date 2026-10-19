# 复现说明 REPRODUCIBILITY — Evaluation-Driven Release Governance

> **版本说明（2026-10-19）**：本复现文档与仓库 docs/ 论文 PDF 均对应 **v3.3（终版）**。
> v3.3 已将精确统计（Clopper-Pearson 区间 [0.892, 0.953]、精确二项 power、Table 8 精确 MDD）
> 直接合入正文，本文档 §2 的 scipy 复算与正文口径一致，无需再做版本换算。

> 配套论文：*Evaluation-Driven Release Governance for LLM Routing in Production: A Case Study of FrugalGPT Router Pro × Aegis*（v3.3，本仓库 docs/ PDF 为该版）
> 整理日期：2026-10-19
> 原则：**论文中的每个数字都可从本目录（`repro_evidence/`）或下述原始路径追溯**；外部基准分数只引用已发表来源，不编造未获得的评测结果。

---

## 1. 目录结构

```
Github开源/
├── frugalgpt/                     ← 社区版代码（api/engine/__init__/__main__）
├── examples/ quickstart.py        ← 快速上手
├── tests/ test_smoke.py           ← 冒烟测试
├── benchmarks/routerarena/        ← RouterArena（ICLR 2026）提交物与复现材料
├── docs/                          ← 论文 PDF（v3.3）、本复现说明
├── repro_evidence/                ← 证据文件（只读副本，源文件以企业产品目录为准）
└── LICENSE / NOTICE / README.md / SECURITY.md / pyproject.toml / CHANGELOG.md
```

**证据文件 → 论文章节映射**：

| 论文章节 | 证据文件（repro_evidence/） | 原始位置（企业产品，只读） |
|---|---|---|
| §5.1 基准（Table 2） | `bench2000_manifest.json`、`bench2000_results.json`、`bench2000_recheck_results.json`、`bench2000_权威基准报告.md`、`bench2000_复测报告_2026-10-06.md` | `04_内部_Internal\实验_Experiments\实验结果_Results\真实实验\`（manifest 在 `bench_data\` 子目录） |
| §5.2 规则调优负结果 | `bench2000_权威基准报告.md`（规则变体交叉部分） | 同上 |
| §5.3 生产负载（Table 4/Figure 2） | `终极评估报告_2026-10-10.md` | `04_内部_Internal\评估审计_Audit\评估报告_Reports\` |
| §5.4 发布门（Table 5） | `闭环决策_Closed-Loop-Decisions.md`、`router_versions.json`、`AB测试报告_v12v13_vs_v7_2026-10-11.md` | `06_路由_Router\frugalgpt-router-pro\docs\` 与 `data\`；`04_内部_Internal\评估审计_Audit\评估报告_Reports\` |
| §5.5 judge 校准（Figure 4） | `judge_calibration_report.md` | `06_路由_Router\frugalgpt-router-pro\data\` |
| §5.6.2 θ 敏感性（Figure 6） | `theta_calibration.json`（735 行重放、459 judged、21 点 θ 曲线） | `06_路由_Router\frugalgpt-router-pro\data\` |
| §5.6.1 吞吐（Figure 5） | `压测与高可用报告_v1.2.md`（404 QPS、37.6/49.8 ms、1043 ms tail） | `04_内部_Internal\实验_Experiments\实验报告_Reports\` |
| §4.2/§4.3 统计协议 | 本包统计脚本（下方 §3）；精确二项 power 与 Clopper-Pearson 区间可用 scipy 复算 | — |
| 口径台账 | `CLAIMS.json`、`gsm8k_mmlu_results_final.json`（历史锚点，已由 2000 题×5 厂商口径取代） | `04_内部_Internal\研发文档_Engineering\`、`真实实验\` |

## 2. 精确统计复算（scipy，一行命令可验）

```python
import numpy as np
from scipy import stats

# §5.4 Table 8 power（精确二项，单侧 alpha=0.05，与 v3.3 正文口径一致）
# 313 窗口、H0 p0=0.9278：MDE@80% ≈ 4.0pp；3pp 退化（p1=0.8978）power ≈ 60%
# 盲评 v13 窗口（n=29, p0=0.828）：MDD ≈ 19.7pp；实测 -20.7pp 退化 power ≈ 0.83

# §5.3 CI（Clopper-Pearson 精确区间，k=290, n=313）
lo, hi = stats.beta.ppf(0.025, 290, 313-290+1), stats.beta.ppf(0.975, 290+1, 313-290)
print(f"CP 95% CI: [{lo:.4f}, {hi:.4f}]")   # → [0.892, 0.953]
```

## 3. 可复现性分级（诚实声明）

- **A 级（完全可复现）**：θ 曲线、吞吐/延迟（本地实测数据 + 脚本即可重跑）；统计检验（精确二项、McNemar、Clopper-Pearson 均可从表中计数重算）。
- **B 级（需真实 API 成本）**：2000 题×5 厂商基准、313 题生产负载的成本与质量数字——需要 DeepSeek/硅基流动/智谱/阶跃 API key 才能重跑；结果文件已随包提供，可在不重跑的前提下逐项核对。
- **C 级（内部业务数据）**：真实生产流量的 tier 分布、A/B 分流、v12/v13 的 25/75 分流记录——属企业内部运营数据，论文仅报告聚合值；逐条审计行（audit/billing 账本）在 Aegis 中版本化并哈希，未随包公开。
- **外部基准**：RouterArena（ICLR 2026）基线分数引自 Lu et al. 论文（arXiv:2510.00202 Table 6 等），非本文实测；本文在 RouterArena 的提交处于官方评测待返回状态，论文不报告未返回的分数。

## 4. RouterArena 提交状态（供审稿人核查）

- 提交物（本仓库）：`benchmarks/routerarena/config|predictions/frugalgpt-router-v2*.json`（full 10018 条 + robustness 420 条）
- 校验：官方 `check_config_prediction_files.py` 原版脚本 **ALL CHECKS PASSED**（full/robustness/sub_10 三 split）
- 合规：纯规则路由（三档 length/digit-density），**0 训练、0 拟合、0 调参**于 RouterArena 数据
- 状态：官方 `/evaluate` 已请求、待返回（2026-10-19）

## 5. 当前状态（截至整理日）

- 论文 §4.5 的 `repository URL` 占位符将在仓库公开发布时填入；
- 论文配图生成脚本与 bench2000 复检脚本为内部工具，未随本仓库发布（论文图与数字可直接从 `repro_evidence/` 与下方复算核对）。
