# 提交说明（RouterArena V2 档）

- **版本**：V2 提交档（2026-10-13）
- **状态**：本地可提交 ✅（官方脚本原版 Validate 全 PASS）

## 一、提交物（对应 fork 路径）

| fork 内路径 | 本仓库文件 | 内容 | 大小 |
|---|---|---|---|
| `router_inference/config/frugalgpt-router-v2.json` | `config/frugalgpt-router-v2.json` | models=[gemini-2.0-flash-001, gpt-4o-mini, gpt-4o] | 0.1KB |
| `router_inference/predictions/frugalgpt-router-v2.json` | `predictions/frugalgpt-router-v2.json` | full：8400 regular + 1618 optimality | 11.6MB |
| `router_inference/predictions/frugalgpt-router-v2-robustness.json` | `predictions/frugalgpt-router-v2-robustness.json` | robustness：420 条 | 0.5MB |

## 二、与 V0 正式档的差异

| 指标 | V0 | V2 | 变化 |
|---|---|---|---|
| 档位分布（full 8400） | L 1.9% / M 27.6% / H 70.5% | L 1.9% / M **53.4%** / H **44.7%** | Heavy −25.8pt |
| cost/1K（中性 300tok 估算） | ≈ $2.68 | ≈ **$1.74** | **−35%** |
| accuracy 预期 | 接近 gpt-4o 上限 | 略降（<2% 量级，论文实证安全区） | 可接受 |

## 三、提交前检查

```powershell
# 轻量自检（纯标准库）：regular 8400 / total 10018
python -c "import json; d=json.load(open('predictions/frugalgpt-router-v2.json',encoding='utf-8')); r=[p for p in d if not p.get('for_optimality')]; assert len(r)==8400 and len(d)==10018; print('OK', len(r))"

# 官方脚本原版 Validate（需按复现步骤 (a) 节就位数据集与 universal_model_names.py）
python scripts/check_config_prediction_files.py frugalgpt-router-v2 full        # ✓ ALL CHECKS PASSED
python scripts/check_config_prediction_files.py frugalgpt-router-v2 robustness  # ✓ ALL CHECKS PASSED
```

## 四、提交流程

fork `RouteWorks/RouterArena` → 上传三件套到同名路径 → 开 PR → PR 评论 `/evaluate`。

> 注意：V2 提交的 router 名称为 `frugalgpt-router-v2`，PR 标题建议
> `[Router] Add FrugalGPT Router v2 (frugalgpt-router-v2)`，并在 PR 描述注明 "V2 optimized tier configuration"。
