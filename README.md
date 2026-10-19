# frugalgpt-router（Community Edition）

一个把每次 LLM 请求路由到「仍能答好的最便宜档位」的多档路由引擎。社区版以**纯规则路由**演示 FrugalGPT 范式：按请求长度、关键词与安全主题在三档模型（Light / Medium / Heavy）之间自动分档，内置 OpenAI 兼容 API，仅依赖 Python 标准库。

## 特性

- **三档规则路由**：短文本 → Light，常规任务 → Medium，复杂/长输入 → Heavy
- **安全优先**：命中敏感主题（医疗/金融/隐私等）强制走旗舰档，不因省成本降档
- **OpenAI 兼容 API**：`POST /v1/chat/completions`，改 `base_url` 即接入
- **零依赖**：运行期仅用 Python 标准库（Python ≥ 3.9）
- **随包论文**：本仓库配套系统论文与全量可复现证据（见下）

> 本仓库是**社区演示实现**：只含规则路由。学习式评分路由、语义 ANN 路由、漂移监控闭环、可审计证据链等为 Pro / Enterprise（商业版）能力，不在此发布。

## 研究论文

本仓库配套系统论文 *[Evaluation-Driven Release Governance for LLM Routing in Production: A Case Study of FrugalGPT Router Pro × Aegis](docs/Evaluation-Driven-Release-Governance-Paper.pdf)*，把 LLM 路由部署建模为受证据门控的发布流程，包含 2,000 题五供应商基准、313 题付费生产负载评估、一个负结果与两次被发布门拦截的版本回退案例。

- 论文中每个数字的证据溯源映射见 [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md)
- 论文参与 RouterArena（ICLR 2026）公开基准的提交物与复现材料见 [`benchmarks/routerarena/`](benchmarks/routerarena/)

## 安装

```bash
git clone https://github.com/Jerry-small-lucky/frugalgpt-router.git
cd frugalgpt-router
pip install .            # 仅依赖标准库，Python ≥ 3.9
```

（也可在 PyPI 发布后直接 `pip install frugalgpt-router`；当前阶段请从源码安装。）

## 快速开始

### 1. 离线演示（无需 API key）

```bash
python -m frugalgpt
```

输出示例：

```
frugalgpt-router 社区版 · 规则路由演示

请求                          档位     原因
你好                          Light    short
请帮我总结一下这份文档的要点       Medium   keyword-medium
请证明勾股定理                  Heavy    keyword-heavy
这个药物有什么副作用？           Heavy    safe
```

### 2. Python 调用

```python
from frugalgpt.engine import route_rule, MODELS
from frugalgpt.api import route_and_generate

# 规则分档：返回 (档位索引, 原因)
tier_idx, reason = route_rule("请帮我总结一下这份文档")
print(tier_idx, MODELS[tier_idx]["name"], reason)   # 1 Medium keyword-medium

# 路由 + 生成（mock 模式，零费用）：返回完整决策与成本信息
r = route_and_generate("把这段中文翻译成英文")
print(r["tier"], r["reason"], r["cost"], r["decision_us"])
```

### 3. OpenAI 兼容 HTTP API

```bash
python -m frugalgpt.api --port 8090
```

```bash
curl -X POST http://127.0.0.1:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"frugalgpt-router","messages":[{"role":"user","content":"请帮我总结一下这份文档"}]}'
```

响应为 OpenAI 兼容结构（`choices` / `usage`），路由决策同时通过响应头返回：

```
X-Router-Tier: Medium
X-Router-Reason: keyword-medium
X-Router-Cost-USD: 0.000059
X-Router-Decision-Us: 18.2
```

其他端点：`GET /v1/models`（模型池与路由配置）、`GET /healthz`（健康检查与模式）。

## API 参考

### `frugalgpt.engine`

| 符号 | 说明 |
|---|---|
| `MODELS` | 三档模型池：`Light` / `Medium` / `Heavy`，含输入/输出成本（$/M tokens） |
| `COSTS` | 各档位 `cin + cout` 汇总 |
| `SENSITIVE_WORDS` | 敏感主题词表，命中任一强制旗舰档 |
| `route_rule(text) -> (int, str)` | 纯规则分档，返回 `(档位索引, 原因)`；原因 ∈ `safe` / `keyword-heavy` / `long` / `keyword-medium` / `short` |

### `frugalgpt.api`

| 符号 | 说明 |
|---|---|
| `route_and_generate(message) -> dict` | 分档并生成（mock 或 real 模式），返回 `tier / reason / content / cost / in_tokens / out_tokens / decision_us` |
| `MODE` | `mock`（默认，零费用）或 `real`（需 `DEEPSEEK_API_KEY` 环境变量，接 DeepSeek 厂商） |

启动参数：`--port`（默认 8090）、`--mode`（`mock` / `real`）。

## 配置与扩展

规则与常量集中在 [`frugalgpt/engine.py`](frugalgpt/engine.py)，改后重新运行测试即可：

| 配置项 | 位置 | 默认行为 |
|---|---|---|
| 档位成本 | `MODELS` | Light 0.15/0.55，Medium 0.60/0.72，Heavy 2.50/0.86（$/M tokens） |
| 敏感词表 | `SENSITIVE_WORDS` | 8 个中文敏感主题词，命中强制 Heavy |
| 中档触发词 | `_MEDIUM_WORDS` | 总结/翻译/分析/代码/解释/写 等 |
| 旗舰触发词 | `_HEAVY_WORDS` | 推理/数学/证明/合同/法律/诊断 等 |
| 长度阈值 | `route_rule` | >120 字符 → Heavy；>40 字符 → Medium（按字符数计） |

> 注：长度阈值为经验硬编码（社区版无配置注入口）；对英文长 prompt 会系统性低估长度。生产环境语义判断请使用商业版。

## 测试

```bash
python tests/test_smoke.py
```

覆盖：规则分档、安全优先、API 管线、边界用例（空串/纯数字/超长输入）。

## 目录结构

```
├── frugalgpt/          路由引擎（标准库实现）
├── examples/           快速开始示例
├── tests/              冒烟测试
├── benchmarks/
│   └── routerarena/    RouterArena 公开基准参与证据（复现 + 提交 + 合规声明）
├── repro_evidence/     论文每个数字的证据文件（溯源映射见 docs/REPRODUCIBILITY.md）
└── docs/               论文 PDF、可复现性说明
```

## 许可

本仓库以 **FrugalGPT Community License 1.0** 发布（源码可见，**非 OSI 开源**）：个人学习、研究、30 天评估免费；商业生产使用、向第三方提供路由服务、竞品/复刻用途需另行商业授权。**2030-10-18** 起本版本自动转为 **Apache-2.0**。

详见 [`LICENSE`](LICENSE) 与 [`NOTICE`](NOTICE)。

## 作者

Jiarui Wang · [GitHub @Jerry-small-lucky](https://github.com/Jerry-small-lucky) · [ORCID 0009-0006-5054-6062](https://orcid.org/0009-0006-5054-6062)
