# RouterArena Benchmark Participation

> 本目录是论文 *Evaluation-Driven Release Governance for LLM Routing in Production*
> （§5.7 Public-Benchmark Participation）的公开评测证据，记录我们对
> [RouterArena](https://arxiv.org/abs/2510.00202)（ICLR 2026，首个持续更新的
> LLM 路由器公开榜单）的提交与复现材料。

## 提交状态（截至投稿日）

- **提交内容**：纯规则路由器（三档 length/digit-density 规则，对 RouterArena 数据
  **0 训练 / 0 拟合 / 0 调参**，符合平台 evaluation-only 政策）。
- **规模**：full split 10,018 条预测 + robustness 420 条。
- **校验**：官方 `check_config_prediction_files.py` 原版脚本全 PASS
  （校验方法见 [`复现步骤_Reproduce.md`](复现步骤_Reproduce.md)）。
- **评测**：官方 `/evaluate` 已请求，**结果返回前不报告任何榜单分数**
  （提交文件中 accuracy/cost 字段为 `null`，由官方评测时回填）。

## 目录

| 路径 | 内容 |
|---|---|
| [`复现步骤_Reproduce.md`](复现步骤_Reproduce.md) | 端到端复现步骤（获取数据 → 推理 → 校验 → 提交） |
| [`合规声明_Compliance.md`](合规声明_Compliance.md) | 平台合规声明（0 训练/拟合/调参） |
| [`提交说明_Submission.md`](提交说明_Submission.md) | 提交物清单、与正式档差异、检查命令 |
| `config/frugalgpt-router-v2.json` | 提交用路由配置 |
| `predictions/` | 提交的预测文件（full 10018 条 + robustness 420 条） |
| `scripts/` | 官方校验脚本与数据生成脚本（第三方，见下） |
| `data/` | 数据格式示例（完整数据集见 RouterArena / HuggingFace） |

## 复现

1. 从 RouterArena（[arXiv:2510.00202](https://arxiv.org/abs/2510.00202)）获取完整评测数据集
   （本目录仅含 `sub_10` 示例，用于格式核对）。
2. 按 [`复现步骤_Reproduce.md`](复现步骤_Reproduce.md) 运行：配置 → 预测生成 → 校验。
3. 将预测文件按平台指引提交，官方校验通过后即进入评测队列。

## 第三方版权声明

- `scripts/check_config_prediction_files.py`、`scripts/_gen_full.py` 来自
  [RouterArena 项目](https://arxiv.org/abs/2510.00202)（作者：Yifan Lu, Rixin Liu,
  Jiarong Xing, et al., Rice University / ICLR 2026），版权归原作者所有，
  随本仓库仅作复现用途，保留其原始版权与引用要求。
- 评测数据集版权归 RouterArena / HuggingFace 各数据源所有，请遵守其许可；
  本仓库不包含完整评测题库。

## 指标口径说明

RouterArena 的 accuracy 以**标准答案命中**计；论文中的质量指标以
**judge 生成质量评估**计（见论文 §5.5）。两者口径不同，论文不作直接比较，
仅引用已发表基线（§5.7）。
