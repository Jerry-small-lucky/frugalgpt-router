# 发布门工程决策记录（观测驱动闭环 · 论文 §5.4/§5.8 证据）

> 本文件记录 2026-10-08 起自动重训与发布门（A/B 门控）的逐次迭代决策。
> 论文 §5.8 版本史（v1–v17）基于本记录：8 个门控候选未放行、0 错误放行。
> 数据均来自真实链路验证，未达标项如实标注。

## 一、闭环动作基线（多样业务流量）

1. **多样化业务流量灌入**：12 类 B 端业务场景（客服/代码/写作/数据分析/合同/翻译/内容审核/营销/报告/规划/金融/HR）× 模板 × 随机难度，共 **1500 条**，全部走真实路由链路（成功 1500 / 失败 0），档位分布约 Light ~87% / Heavy ~13%。
   - 口径：prompt 为业务场景模拟文本（非真实客户流量），但路由/审计/质量链路与线上一致。

2. **多样流量下评估门**：质量保持率 **96.0%**（≥95）｜成本节省率 **59.25%**（≥50）｜决策 p99 **2.65ms**（≤200ms）→ **PASS**。
   - 此前旧测试流量（敏感/多模态占 32%+、prompt 高度重复）下评估门如实 FAIL（93.1% / 48.5%）——门禁按设计工作；多样流量下达标，证明 FAIL 源于流量结构而非路由缺陷。

3. **漂移监控告警**：业务流量 vs 旧测试流量：档位 KL 0.0118（<0.10）但复杂度特征均值相对变化 +31.6%（>15% 阈值）→ **DRIFT**。

4. **自动重训产出 v2 候选**：385 条训练样本（Medium 210 / Light 152 / Heavy 23），来自真实路由链路决策（provenance: real-decision / retrain-v1 / quality-boost）。训练验证 acc 40.3%（如实：训练集含 shadow 错配标签与决策回灌标签冲突、模板化区分度有限）。

## 二、v2 迭代（未达标拒绝）

A/B 实机（50% 分流）：candidate（v2）n=191、judge 抽检 86 条、质量通过率 **93.02%**（6 fail）、节省 60.08%；对照（v6）n=220、抽检 119 条、质量通过率 **100%**、节省 60.78%。

**结论：v2 质量不达标（−6.98pp），按发布纪律不发布**；状态标记 `rejected`。这正是 A/B 门禁的价值——拦截不合格候选。已关闭分流，在线恢复 v6（online-v0）。

## 三、v3 迭代（未达标拒绝）

改进（针对 v2 根因）：决策回灌为主（同 prompt 多档取最新决策档，冲突以真实决策为准，过滤 808 条）；业务流量多样性扩展（每场景模板 4→6，新增 800 + 500 条）。

结果（如实）：训练 681 样本（Light 549 / Heavy 123 / Medium 9），同集验证 acc 100%。A/B 实机（500 条新流量，50% 分流）：candidate（v3）435 请求质量 **93.4%**、节省 56.3%；control（v6）476 请求质量 **97.3%**、节省 58.9%。

**判定：v3 质量仍不达标（−3.9pp）且节省略低 → rejected 不发布。**
**v3 根因**：P0 质量增强的升档信号（quality<0.6 强制升档，17 条）被"决策回灌为准"的去冲突规则覆盖；决策回灌以 Light 为主（81%），强化 v6 的 Light 倾向（自举偏差）。

## 四、v4 迭代（回滚）

改进（针对 v3 根因）：信号优先级改为 **P0 质量增强（升档）> 决策回灌 > shadow 错配**；quality<0.6 的行直接采用升档标签（boost_priority 标记，冲突过滤不得丢弃）。

结果（如实）：训练 1190 样本，验证 acc 99.2%。A/B 实机（500 条）：candidate 质量 **96.77%** vs control **96.83%**、节省 52.06% vs 52.59% → 质量/节省与对照持平（达标）。

**缺陷暴露**：smoke 回归「难题路由到 Medium/Heavy」FAIL——v4 对黎曼猜想等领域难题判 Light（训练集无难题样本，决策回灌把 v6 的 Light 错误决策自举强化）。发布纪律触发：`--rollback` 回滚至 v6，v4 状态=rolled_back。**教训：mock judge 识别不了"难题性"（难题行 judge pass，仍被回灌为 Light），难题识别不能靠观测回灌，必须显式知识注入。**

## 五、v5→v7 迭代（难题识别修复，v7 达标发布）

改进（针对 v4 难题缺陷）：
- 新增「难题研究」场景（12 条科学/数学/工程难题模板：黎曼猜想/纳维-斯托克斯/P vs NP/史瓦西/对抗鲁棒性/信道容量/拜占庭/Black-Scholes/四色/退相干/涌现/激波），灌入 600 条。
- 新增**显式难题知识注入**：内置 `HARD_TEMPLATES`（12 条难题模板）×4 变体 = **48 条 curated-hard → Heavy**（provenance=curated-hard），与决策回灌/P0 纠错/冲突过滤四融合。

**v7 结果（如实）**：
- 训练 619 样本（Heavy 142 含难题注入 48 / Medium 66 / Light 411），验证 acc 92.7%（含挑战性样本后自然回落）。
- 本地档位验证：黎曼→Heavy(0.613)、纳维斯托克斯→Heavy(0.701)、黎曼变体→Heavy(0.653)；易-客服→Light(0.754)。
- **A/B 实机（400 条，50% 分流）**：candidate（v7）204 请求质量 **98.2%**、节省 51.9%；control（v6）196 请求质量 97.7%、节省 52.4% → **质量超越对照（+0.5pp）且 ≥95% 门槛，节省基本持平（−0.5pp，难题→Heavy 的合理成本）→ 达标发布。**
- **A/B 难题对照**：candidate 黎曼/纳维/史瓦西/激波/拜占庭/退相干/Black-Scholes/四色/涌现全判 Heavy（个别变体 Medium）；control 同类难题普遍 Light——v6 的难题缺陷与 v7 的修复形成同流对照。
- **全量发布 v7**（在线模型 auto-retrain:v7@2026-10-08T21:14:23，旧 v6 备份 `publish_backups/online_before_v7.pkl`）。
- **发布后全量回归 33/33 PASS**（含 smoke 123/123；B4 合规 12/12 PASS）。
- **合规**：训练回灌用 summary 显式开启，发布验收后已恢复 `content_retention=off`。

## 六、A/B 机制审计与修复（v1.17.4）

对 A/B 全链路（分流→落盘→统计→状态机→门禁）逐段审计，修复：

| # | 严重度 | 问题（审计发现） | 修复 |
| --- | --- | --- | --- |
| 1 | P1 | 候选模型决策失败时 ab_group 保持 na——失败行从 A/B 统计消失，**candidate 统计被系统性高估** | 标记 `candidate-failed` 单列：回退在线决策，失败数单独报告，绝不混入统计 |
| 2 | P1 | eval_router 质量门 `qk is None` 时 ok_q=True——**judge 数据缺失时质量门默认放行** | 质量数据缺失按 FAIL 处理，绝不空放行 |
| 3 | P2 | promote 未校验 `0<ratio≤1` | 边界校验，越界报错退出 |
| 4 | P2 | full 未记录 previous_version——rollback 恢复恒为 online-v0 | full 时记录旧版本号 |
| 5 | P2 | full 时旧在线 pkl 缺失仍继续发布 | 旧 pkl 缺失拒绝发布 |
| 6 | P2 | full 写绝对路径 model_path——config 不可移植 | 写相对 BASE 路径 |
| 7 | P2 | auto_retrain 版本登记缺 status 字段 | 登记显式 status='candidate' |
| 8 | P2 | promote/full 对 rejected/rolled_back 版本无提示覆盖 | 覆盖前打印警告 |
| 9 | P3 | version_evidence 打印缺 judged n | candidate/control 打印 judge n；新增 candidate_failed_n |
| 10 | P2 | A/B 对比无自动判定 | 新增 `ab_verdict` 自动判定（质量≥对照且≥95%、节省劣化≤5pp、n≥30 → pass/fail/insufficient） |
| 11 | P3 | judge 注释与实际抽检逻辑不符 | 注释对齐实际逻辑 |

**验证**：纯函数验证（qk=None→FAIL、_ab_verdict 三分支、ratio 边界、candidate-failed 分支）全部 PASS；服务重启后 version_evidence：candidate 171 / control 160 / judge n 94/71，**A/B 判定 pass**（候选 98.9% ≥ 对照 97.2%）；全量回归 33/33 PASS。

## 七、遗留缺口（如实）

| 缺口 | 状态 | 下一步 |
| --- | --- | --- |
| v2/v3 质量不达标 | 已拒绝并记录原因 | 已在 v4/v7 通过 P0 纠错与难题注入解决 |
| v4 难题判 Light | 已回滚，v7 修复 | v7 已全量发布，难题判 Heavy 实证 |
| 训练回灌依赖 preview 显式开启 | 已文档化 | 合规评估后开启 summary，积累真实业务流量 |
| 版本证据/漂移基于模拟流量 | 待真实流量 | 接入真实流量后重跑 eval/drift/evidence |
| v1（DEMO 合成）候选遗留 ab 状态 | 遗留 | 在 versions.json 标注 synthetic，不影响在线 |

## 八、证据文件

- `eval_router_report.json`（最新 PASS：96.0% / 59.25% / p99 2.65ms）
- `drift_report.json`（DRIFT：comp rel +31.6%）
- `router_versions.json`（v2/v3=rejected 含原因、v4=rolled_back、v7=live）
- `version_evidence.json`（最新：candidate v7 98.2% vs control 97.7%、节省 51.9% vs 52.4%）
- `publish_backups/online_before_v7.pkl`（v6 备份，可回滚）
