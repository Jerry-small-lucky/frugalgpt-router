# RouterArena 提交复现步骤

本文档说明如何从 RouterArena 公开数据出发，端到端复现本仓库提交的预测文件
（`config/frugalgpt-router-v2.json` + `predictions/`）。

- **版本**：v2.0（对应本仓库提交物 **V2 优化档** `frugalgpt-router-v2`）
- **日期**：2026-10-13（实测生成并校验）
- **V0/V2 说明**：V0 为正式档（Medium=claude-3-haiku-20240307、阈值 450/25），
  V2 为优化备选档（Medium=gpt-4o-mini、阈值 700/35，**本仓库提交物即此档**）；
  两档差异见 [`合规声明_Compliance.md`](合规声明_Compliance.md) 第 1 节。

> **口径声明**
> - 本文是操作手册：本次已实际完成「数据集下载 → 官方模板复刻 → 全量预测生成 → 官方语义校验」；下列命令为可复现执行路径。
> - 合规：全程不在 RouterArena 标签列（`Answer`）上训练/拟合/调参；预测由纯规则现算。
> - **提交文件口径**：正式提交 = `full` split 预测文件（8400 regular + 1618 optimality 条目 = 10018 条）；
>   `generated_result` 保留 `null`（官方 `check_config_prediction_files.py` 的 `--check-generated-result` 默认 False，
>   Validate 在推理前运行、不检查该字段）；本地另存 `sub_10` 2427 条供 dry-run 验证。

---

## (a) 获取官方仓库文件与数据集

1. **抓取官方仓库文本文件**（RouterArena GitHub 仓库）：

   ```bash
   git clone https://github.com/RouteWorks/RouterArena.git
   ```

   需要的文件：
   - `README.md`
   - `router_inference/check_config_prediction_files.py`（官方校验脚本）
   - `router_inference/generate_prediction_file.py`、`router_inference/router/base_router.py`
   - `scripts/process_datasets/prep_datasets.py`
   - `config/eval_config/zero-shot/<40 个数据集>.json`（模板全集）

   > 注意：`universal_model_names.py` 位于**仓库根目录**（不是 `router_inference/` 子目录）——
   > 校验脚本通过 `sys.path.append(项目根)` 后 `from universal_model_names import ModelNameManager` 导入。

2. **下载 HF 数据集**（公开 parquet；含 `Answer` 标签列——**只读 prompt 用于路由决策，绝不读标签训练**）：

   ```python
   from datasets import load_dataset
   ds = load_dataset("RouteWorks/RouterArena")
   print(ds)   # sub_10 / full / robustness 三个 split
   ```

   - split 规模：sub_10 = 809 / full = 8400 / robustness = 420 行（与官方条数逐条吻合）。
   - **官方校验脚本约定的本地数据文件名**：`./dataset/router_data_10.json`（sub_10）、
     `./dataset/router_data.json`（full）、`./dataset/router_robustness.json`（robustness）——
     按官方 `prep_datasets.py` 逻辑复刻生成（本仓库 `data/router_data_10.json` 即 sub_10 示例）。
   - **LiveCodeBench 特殊处理**：官方 `prep_datasets.py` 的 LCB 分支从
     `lighteval/code_generation_lite`（release_v2，共 511 条）匹配 `is_stdin`
     （public_test_cases 的 testtype=stdin）。本包已实测：RouterArena 的 LCB 全局序号
     == release_v2 顺序号，sub_10 的 38 条 LCB 38/38 按序号命中。

## (b) 用合规规则路由生成预测

核心是把 `arena_router.py` 的 `rule_decide`（**V2 档**：Heavy >700 字符或 >35 数字；
Medium 251–700 字符或 11–35 数字；Light 其余）套到数据集每条 `prompt_formatted` 上，落成预测 JSON：

```python
import json, re

TIER_TO_ARENA = {
    "Light":  "gemini-2.0-flash-001",
    "Medium": "gpt-4o-mini",
    "Heavy":  "gpt-4o",
}

def rule_decide(text):
    n_digit = len(re.findall(r"\d", text or ""))
    n_chars = len(text or "")
    if n_chars > 700 or n_digit > 35:
        return "Heavy"
    if n_chars > 250 or n_digit > 10:
        return "Medium"
    return "Light"
```

要点（与官方 `generate_prediction_file.py` 语义一致，本仓库脚本 `scripts/_gen_full.py` 已完整实现）：

- **字段名**：`"global index"`（带空格，官方生成器字段名）；每条含
  `global index / prompt / prediction / generated_result(null) / cost(null) / accuracy(null) / for_optimality`。
- **regular 条目**：full 8400 条 / sub_10 809 条 / robustness 420 条；`prompt` 逐字 = 数据集 `prompt_formatted`。
- **optimality 条目**（仅 sub_10/full）：对每条 sub_10 查询生成其余 2 个模型的条目
  （`for_optimality: True`），供官方算 Optimal-selection / Optimal-cost 指标；full 提交 = 8400 + 809×2 = **10018 条**。
- **robustness 文件**：同规则、同 prompt（加噪后版本），**无 optimality 条目**（420 条）。
- **合规**：不读 `Answer` 标签列；`rule_decide` 是写死的字符长度/数字个数规则，0 训练、0 拟合、0 调参。

## (c) 本地校验

正式提交前先做轻量自检（纯标准库）：

```python
import json
cfg = json.load(open("config/frugalgpt-router-v2.json", encoding="utf-8"))
pred = json.load(open("predictions/frugalgpt-router-v2.json", encoding="utf-8"))
models = set(cfg["pipeline_params"]["models"])
regular = [p for p in pred if not p.get("for_optimality", False)]
assert len(regular) == 8400, f"条数错误: {len(regular)}"
for p in regular:
    assert p["prediction"] in models, f"模型名不在 config: {p['prediction']}"
print("OK", len(regular))
```

再跑官方校验脚本（原版，需在 RouterArena 仓库环境内、数据集就位后）：

```powershell
python router_inference/check_config_prediction_files.py frugalgpt-router-v2 full
python router_inference/check_config_prediction_files.py frugalgpt-router-v2 robustness
```

校验覆盖：config 模型能否被 `ModelNameManager` 识别；条数（full 8400 / robustness 420，regular 口径）；
`global index` 与 `prompt` 是否逐字命中数据集；`prediction` 是否 ∈ config 模型；每个模型在 `model_cost.json` 是否有价。

**本包已实测（2026-10-13）**：full regular 8400 / sub_10 809 / robustness 420 三条全 PASS
（prompt 逐字命中官方模板、模型全部 ∈ config 池、global index 与数据集对齐、0 错误）；
V2 档 full regular 分布 = Light 160 / Medium 4485 / Heavy 3755（1.9% / 53.4% / 44.7%）。

## (d) 提交与 /evaluate

1. fork `RouteWorks/RouterArena`，把三个文件放到对应路径：
   - `router_inference/config/frugalgpt-router-v2.json`（models=[gemini-2.0-flash-001, gpt-4o-mini, gpt-4o]）
   - `router_inference/predictions/frugalgpt-router-v2.json`（full 10018 条，含 optimality）
   - `router_inference/predictions/frugalgpt-router-v2-robustness.json`（420 条，无 optimality）
2. 向 `main` 分支开 PR；PR 评论发送 `/evaluate` 触发自动评测。
3. 自动工作流四步：**Validate → 全量评测 → PR 评论贴结果 → approval 后上榜**。
4. 提交后观察点：
   - Validate 是否因模型名不被 `ModelNameManager` 识别而失败（若失败，按报错改 `models` 名单）；
   - PR 评论贴出的 Accuracy / Cost / Arena Score 是否与本地量级自洽；
   - 榜单是「经人工 approval 后」才更新，PR 评论 ≠ 正式上榜；
   - 记录**提交时点**的榜单快照（名次随时间漂移，事后对外引用须注明提交日期）；
   - 若 Validate 报 prompt 不匹配：以官方 workflow 实际生成的 `./dataset/router_data*.json` 为准复核复刻脚本（`scripts/_gen_full.py`）的模板拼装细节。

## 来源链接

- 官方 README（提交流程）：https://raw.githubusercontent.com/RouteWorks/RouterArena/main/README.md
- 校验脚本：https://raw.githubusercontent.com/RouteWorks/RouterArena/main/router_inference/check_config_prediction_files.py
- 数据集：https://huggingface.co/datasets/RouteWorks/RouterArena
- 论文：https://arxiv.org/abs/2510.00202
